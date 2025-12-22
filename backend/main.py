from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import os
import json
import re
import logging
from urllib.parse import urlparse
from typing import Optional
import video_processor
import fact_checker

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vigil AI Lite API",
    description="Analyzes video URLs for misinformation using a Triage & Escalate model."
)

# Configure CORS to allow requests from the React frontend
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",  # Vite default port
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    video_url: HttpUrl


def detect_url_type(url: str) -> str:
    """
    Detects the type of URL and returns one of:
    - 'youtube': YouTube video links
    - 'video_platform': Instagram, Facebook, TikTok, etc.
    - 'webpage': Regular web page
    """
    url_lower = url.lower()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # YouTube detection
    youtube_patterns = [
        'youtube.com', 'youtu.be', 'm.youtube.com', 
        'youtube-nocookie.com'
    ]
    if any(pattern in domain for pattern in youtube_patterns):
        return 'youtube'
    
    # Video platform detection
    video_platforms = [
        'instagram.com', 'facebook.com', 'fb.watch',
        'tiktok.com', 'twitter.com', 'x.com',
        'vimeo.com', 'dailymotion.com', 'twitch.tv'
    ]
    if any(platform in domain for platform in video_platforms):
        return 'video_platform'
    
    # Default to webpage
    return 'webpage'


@app.get("/", tags=["Status"])
def read_root():
    return {"status": "Vigil AI Lite API is running."}

@app.post("/analyze", tags=["Analysis"])
async def analyze_video(request: VideoRequest):
    """
    Main endpoint to analyze a video or webpage. Implements the 'Triage & Escalate' model.
    Handles YouTube URLs, other video platforms, and regular web pages differently.
    """
    url = str(request.video_url)
    url_type = detect_url_type(url)
    files_to_clean = []
    
    try:
        # Detect URL type and route accordingly
        # YouTube URLs are sent directly to Gemini using FileData format
        # Other video platforms are downloaded and processed
        if url_type == 'youtube':
            return await analyze_youtube_url(url)
        elif url_type == 'video_platform':
            return await analyze_video_platform(url, files_to_clean)
        else:  # webpage
            return await analyze_webpage(url)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    finally:
        # Cleanup all temporary files (but keep analysis folder)
        video_processor.cleanup_files(files_to_clean)


async def analyze_youtube_url(url: str) -> dict:
    """
    Handles YouTube URLs by sending the URL directly to Gemini.
    YouTube videos can be processed natively by Gemini without downloading.
    """
    session_path = None
    
    try:
        # Extract basic metadata without downloading
        video_title = "YouTube Video"
        uploader = "Unknown"
        
        try:
            import yt_dlp
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Don't resolve URLs, just get metadata
                'no_check_certificate': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'YouTube Video')
                uploader = info_dict.get('uploader', 'Unknown')
        except Exception as metadata_error:
            # If metadata extraction fails, continue without it
            # Gemini can still analyze the video from the URL
            logger.warning(f"⚠️ Could not extract metadata: {metadata_error}")
            logger.info(f"ℹ️ Continuing with Gemini analysis using URL only")
        
        # Create analysis session folder for inspection
        session_path = video_processor.create_analysis_session({
            "title": video_title,
            "url": url
        })
        logger.info(f"📁 Created analysis session: {session_path}")
        
        # Save metadata
        metadata_path = os.path.join(session_path, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                "url": url,
                "title": video_title,
                "uploader": uploader,
                "url_type": "youtube",
                "processing_method": "direct_to_gemini"
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved metadata to: {os.path.basename(metadata_path)}")
        
        # Send YouTube URL directly to Gemini (YouTube uses Gemini)
        gemini_report = fact_checker.analyze_youtube_with_gemini(url, video_title, uploader, session_path)
        
        return {
            "source": "Vigil AI Analysis (YouTube - Gemini)",
            "url_type": "youtube",
            "report": gemini_report,
            "analysis_session": session_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube analysis failed: {e}")


async def analyze_video_platform(url: str, files_to_clean: list) -> dict:
    """
    Handles Instagram, Facebook, TikTok, etc. by downloading and processing
    frames and audio like we do for non-YouTube videos.
    """
    session_path = None
    
    try:
        # 1. Download video and get metadata
        metadata = video_processor.download_video_and_get_metadata(url)
        video_path = metadata.get("video_path")
        if video_path:
            files_to_clean.append(video_path)
        video_title = metadata.get("title", "")
        
        # Create analysis session folder for inspection
        session_path = video_processor.create_analysis_session(metadata)

        # Extract frames and audio for Gemini analysis
        keyframes = video_processor.extract_keyframes(video_path, num_frames=20)
        files_to_clean.extend(keyframes)
        
        if not keyframes:
            raise HTTPException(status_code=400, detail="Could not extract frames from video.")
        
        # Extract audio/captions from video
        caption_path = metadata.get('caption_path')
        audio_info = video_processor.extract_audio_transcription(video_path, caption_path)
        if audio_info.get('audio_path'):
            files_to_clean.append(audio_info['audio_path'])
        if caption_path:
            files_to_clean.append(caption_path)
        
        # Pass session_path and audio_info to Gemini analysis
        gemini_report = fact_checker.analyze_with_gemini(metadata, keyframes, audio_info, session_path)
        
        return {
            "source": "Vigil AI Generative Analysis (Video Platform)",
            "url_type": "video_platform",
            "report": gemini_report,
            "analysis_session": session_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video platform analysis failed: {e}")


async def analyze_webpage(url: str) -> dict:
    """
    Handles regular web pages by scraping content and sending to Gemini.
    """
    session_path = None
    
    try:
        # Scrape webpage content
        scraped_data = video_processor.scrape_webpage(url)
        
        if not scraped_data.get('success'):
            raise HTTPException(status_code=400, detail=f"Failed to scrape webpage: {scraped_data.get('error')}")
        
        # Create analysis session folder for inspection
        page_title = scraped_data.get('title', 'Webpage')
        session_path = video_processor.create_analysis_session({
            "title": page_title,
            "url": url
        })
        logger.info(f"📁 Created analysis session: {session_path}")
        
        # Save metadata
        metadata_path = os.path.join(session_path, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                "url": url,
                "title": page_title,
                "url_type": "webpage",
                "processing_method": "web_scraping",
                "word_count": scraped_data.get('word_count', 0)
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved metadata to: {os.path.basename(metadata_path)}")
        
        # Send scraped content to Gemini
        gemini_report = fact_checker.analyze_webpage_with_gemini(url, scraped_data, session_path)
        
        return {
            "source": "Vigil AI Generative Analysis (Web Content)",
            "url_type": "webpage",
            "report": gemini_report,
            "analysis_session": session_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webpage analysis failed: {e}")


@app.post("/analyze/upload", tags=["Analysis"])
async def analyze_uploaded_file(file: UploadFile = File(...)):
    """
    Analyzes uploaded files (video, audio, PDF, Word documents, images, etc.)
    for misinformation and authenticity.
    
    Supported formats:
    - Video: mp4, avi, mov, mkv, webm
    - Audio: mp3, wav, m4a, aac, ogg
    - Documents: pdf, docx, doc, txt
    - Images: jpg, jpeg, png, gif, webp
    """
    temp_file_path = None
    files_to_clean = []
    session_path = None
    
    try:
        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Save uploaded file temporarily
        video_processor.setup_temp_dir()
        import uuid
        temp_id = str(uuid.uuid4())
        temp_file_path = os.path.join(video_processor.TEMP_DIR, f"{temp_id}{file_ext}")
        
        logger.info(f"📤 Received file upload: {file.filename} ({file_ext})")
        
        # Write uploaded file to disk
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        files_to_clean.append(temp_file_path)
        file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
        logger.info(f"💾 Saved to temp: {temp_file_path} ({file_size_mb:.2f} MB)")
        
        # Detect file type and route accordingly
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
        audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma']
        document_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']
        
        if file_ext in video_extensions:
            return await analyze_uploaded_video(temp_file_path, file.filename, files_to_clean)
        elif file_ext in audio_extensions:
            return await analyze_uploaded_audio(temp_file_path, file.filename, files_to_clean)
        elif file_ext in document_extensions:
            return await analyze_uploaded_document(temp_file_path, file.filename, file_ext)
        elif file_ext in image_extensions:
            return await analyze_uploaded_image(temp_file_path, file.filename)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
            
    except HTTPException:
        # Re-raise HTTPException to preserve status code
        raise
    except Exception as e:
        logger.error(f"❌ File upload analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {e}")
    finally:
        # Cleanup temporary files
        video_processor.cleanup_files(files_to_clean)


async def analyze_uploaded_video(video_path: str, filename: str, files_to_clean: list) -> dict:
    """Analyzes uploaded video files for misinformation and deepfakes."""
    session_path = None
    
    try:
        # Verify video file exists and is readable
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file not found: {filename}")
        
        file_size = os.path.getsize(video_path)
        logger.info(f"📹 Processing uploaded video: {filename} ({file_size} bytes)")
        
        # Create metadata for the uploaded file
        metadata = {
            "video_path": video_path,
            "title": filename,
            "url": f"uploaded_file://{filename}",
            "uploader": "User Upload",
            "caption_path": None
        }
        
        # Create analysis session
        session_path = video_processor.create_analysis_session(metadata)
        logger.info(f"📁 Created analysis session for upload: {session_path}")
        
        # Extract 20 keyframes from the video
        logger.info(f"🎞️ Extracting keyframes from video...")
        keyframes = video_processor.extract_keyframes(video_path, num_frames=20)
        files_to_clean.extend(keyframes)
        
        if not keyframes:
            raise HTTPException(status_code=400, detail="Could not extract frames from video.")
        
        logger.info(f"✅ Extracted {len(keyframes)} keyframes")
        
        # Extract audio from the video
        logger.info(f"🎵 Extracting audio from video...")
        audio_info = video_processor.extract_audio_transcription(video_path, caption_path=None)
        if audio_info.get('audio_path'):
            files_to_clean.append(audio_info['audio_path'])
        
        logger.info(f"✅ Audio extraction status: {audio_info.get('status', 'unknown')}")
        
        # Analyze with Gemini
        logger.info(f"🤖 Sending to Gemini for analysis...")
        gemini_report = fact_checker.analyze_with_gemini(metadata, keyframes, audio_info, session_path)
        
        logger.info(f"✅ Video analysis complete")
        
        return {
            "source": "Vigil AI Generative Analysis (Uploaded Video)",
            "file_type": "video",
            "filename": filename,
            "report": gemini_report,
            "analysis_session": session_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uploaded video analysis failed: {e}")


async def analyze_uploaded_audio(audio_path: str, filename: str, files_to_clean: list) -> dict:
    """Analyzes uploaded audio files for misinformation and deepfakes."""
    session_path = None
    
    try:
        # Verify audio file exists and is readable
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail=f"Audio file not found: {filename}")
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"🎵 Processing uploaded audio: {filename} ({file_size} bytes)")
        
        # Create metadata
        metadata = {
            "title": filename,
            "url": f"uploaded_file://{filename}",
            "uploader": "User Upload"
        }
        
        # Create analysis session
        session_path = video_processor.create_analysis_session(metadata)
        logger.info(f"📁 Created analysis session for audio: {session_path}")
        
        # Get audio duration
        import cv2
        # For audio-only files, we'll use a different approach
        # Just pass the audio file directly
        audio_info = {
            "status": "success",
            "audio_path": audio_path,
            "method": "uploaded",
            "caption_text": None
        }
        
        # Analyze audio with Gemini
        logger.info(f"🤖 Sending audio to Gemini for analysis...")
        gemini_report = fact_checker.analyze_audio_with_gemini(audio_path, filename, session_path)
        
        logger.info(f"✅ Audio analysis complete")
        
        return {
            "source": "Vigil AI Generative Analysis (Uploaded Audio)",
            "file_type": "audio",
            "filename": filename,
            "report": gemini_report,
            "analysis_session": session_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Uploaded audio analysis failed: {e}")
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Uploaded audio analysis failed: {e}")


async def analyze_uploaded_document(doc_path: str, filename: str, file_ext: str) -> dict:
    """Analyzes uploaded documents (PDF, Word, etc.) for misinformation."""
    session_path = None
    
    try:
        # Verify document file exists and is readable
        if not os.path.exists(doc_path):
            raise HTTPException(status_code=404, detail=f"Document file not found: {filename}")
        
        file_size = os.path.getsize(doc_path)
        logger.info(f"📄 Processing uploaded document: {filename} ({file_size} bytes)")
        
        # Extract text from document
        logger.info(f"📖 Extracting text from document...")
        extracted_text = video_processor.extract_text_from_document(doc_path, file_ext)
        
        # Create analysis session (do this early to save all artifacts)
        metadata = {
            "title": filename,
            "url": f"uploaded_file://{filename}"
        }
        session_path = video_processor.create_analysis_session(metadata)
        logger.info(f"📁 Created analysis session: {session_path}")
        
        # Check if it's an image-based PDF (scanned)
        if extracted_text == "IMAGE_BASED_PDF":
            logger.info(f"🎨 Image-based PDF detected - using Gemini Vision API")
            
            # Render PDF pages as images (for scanned PDFs)
            images_dir = os.path.join(session_path, "pdf_pages")
            image_paths = video_processor.render_pdf_pages_as_images(doc_path, images_dir)
            
            if not image_paths:
                raise HTTPException(status_code=422, detail="Failed to render PDF pages as images. Please install PyMuPDF: pip install PyMuPDF")
            
            logger.info(f"🖼️ Rendered {len(image_paths)} pages as images")
            
            # Analyze images with Gemini Vision
            logger.info(f"🤖 Sending PDF page images to Gemini Vision API for analysis...")
            gemini_report = fact_checker.analyze_document_images_with_gemini(image_paths, filename, session_path)
            
            logger.info(f"✅ Image-based PDF analysis complete")
            
            return {
                "source": "Vigil AI Generative Analysis (Scanned PDF)",
                "file_type": "document",
                "filename": filename,
                "report": gemini_report,
                "analysis_session": session_path,
                "pages_rendered": len(image_paths)
            }
        
        # Check if text extraction returned an error message
        if extracted_text and extracted_text.startswith("ERROR:"):
            error_msg = extracted_text.replace("ERROR: ", "")
            logger.error(f"❌ Text extraction error: {error_msg}")
            raise HTTPException(status_code=422, detail=error_msg)
        
        # Check text length - be lenient for short documents
        text_length = len(extracted_text.strip()) if extracted_text else 0
        logger.info(f"✅ Extracted {text_length} characters of text")
        
        if text_length < 10:
            # Very short or empty - might be scanned PDF or extraction issue
            if text_length == 0:
                error_msg = "Could not extract any text from document. The file might be empty, image-based (scanned), or corrupted. For scanned PDFs, OCR is required."
                logger.error(f"❌ {error_msg}")
                raise HTTPException(status_code=422, detail=error_msg)
            else:
                # Has some text but very short - allow it but warn
                logger.warning(f"⚠️ Document has very little text ({text_length} chars). Proceeding with analysis...")
        
        logger.info(f"✅ Text extraction successful: {text_length} characters")
        
        # Save extracted text
        text_path = os.path.join(session_path, "extracted_text.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        logger.info(f"💾 Saved extracted text")
        
        # For PDFs, also extract any embedded images
        embedded_images = []
        if file_ext == '.pdf':
            logger.info(f"�️ Checking for embedded images in PDF...")
            images_dir = os.path.join(session_path, "embedded_images")
            embedded_image_paths, has_text = video_processor.extract_embedded_images_from_pdf(doc_path, images_dir)
            
            if embedded_image_paths:
                logger.info(f"✅ Found {len(embedded_image_paths)} embedded image(s)")
                embedded_images = embedded_image_paths
            else:
                logger.info(f"ℹ️ No embedded images found")
        
        # Analyze document with Gemini
        logger.info(f"🤖 Sending document to Gemini for analysis...")
        gemini_report = fact_checker.analyze_document_with_gemini(
            filename, 
            extracted_text, 
            session_path,
            embedded_images=embedded_images  # Pass embedded images if any
        )
        
        logger.info(f"✅ Document analysis complete")
        
        response = {
            "source": "Vigil AI Generative Analysis (Text-based Document)",
            "file_type": "document",
            "filename": filename,
            "report": gemini_report,
            "analysis_session": session_path
        }
        
        if embedded_images:
            response["embedded_images_found"] = len(embedded_images)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document analysis failed: {e}")
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {e}")


async def analyze_uploaded_image(image_path: str, filename: str) -> dict:
    """Analyzes uploaded images for misinformation and manipulation."""
    session_path = None
    
    try:
        # Verify image file exists and is readable
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"Image file not found: {filename}")
        
        file_size = os.path.getsize(image_path)
        logger.info(f"🖼️ Processing uploaded image: {filename} ({file_size} bytes)")
        
        # Create metadata
        metadata = {
            "title": filename,
            "url": f"uploaded_file://{filename}"
        }
        
        # Create analysis session
        session_path = video_processor.create_analysis_session(metadata)
        logger.info(f"📁 Created analysis session for image: {session_path}")
        
        # Copy image to session folder
        import shutil
        session_image_path = os.path.join(session_path, f"uploaded_image{os.path.splitext(filename)[1]}")
        shutil.copy(image_path, session_image_path)
        logger.info(f"💾 Saved image to session folder")
        
        # Analyze image with OpenAI (uploaded images use OpenAI)
        logger.info(f"🤖 Sending image to OpenAI for analysis...")
        gemini_report = fact_checker.analyze_image_with_gemini(image_path, filename, session_path)
        
        logger.info(f"✅ Image analysis complete")
        
        return {
            "source": "Vigil AI Analysis (Uploaded Image - OpenAI Vision)",
            "file_type": "image",
            "filename": filename,
            "report": gemini_report,
            "analysis_session": session_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Image analysis failed: {e}")
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


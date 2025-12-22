import cv2
import yt_dlp
import os
import uuid
import numpy as np  # Added for placeholder image generation
import logging
import shutil
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

TEMP_DIR = "temp_media"
ANALYSIS_DIR = "analysis"

# LIVE DEBUG LOG FILE - writes immediately to disk
DEBUG_LOG_FILE = os.path.join(os.path.dirname(__file__), "LIVE_DEBUG.txt")

def live_log(message: str):
    """Write debug message immediately to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()  # Force write to disk immediately

def setup_temp_dir():
    """Ensures the temporary directory exists."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        logger.info(f"Created temporary directory: {TEMP_DIR}")


def setup_analysis_dir():
    """Ensures the analysis directory exists for storing inspection data."""
    if not os.path.exists(ANALYSIS_DIR):
        os.makedirs(ANALYSIS_DIR)
        logger.info(f"Created analysis directory: {ANALYSIS_DIR}")
    return ANALYSIS_DIR


def create_analysis_session(video_metadata: dict) -> str:
    """
    Creates a timestamped folder for this analysis session.
    Returns the path to the session folder.
    """
    setup_analysis_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_title_safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                               for c in video_metadata.get('title', 'unknown'))[:50].strip()
    session_name = f"{timestamp}_{video_title_safe}"
    session_path = os.path.join(ANALYSIS_DIR, session_name)
    os.makedirs(session_path, exist_ok=True)
    logger.info(f"📁 Created analysis session folder: {session_path}")
    return session_path

def download_video_and_get_metadata(url: str) -> dict:
    """
    Downloads a video from a URL to a temporary path and extracts metadata.
    Returns a dictionary with video_path, title, uploader, and captions.
    """
    live_log("\n" + "=" * 80)
    live_log(f"FUNCTION CALLED: download_video_and_get_metadata('{url}')")
    setup_temp_dir()
    video_id = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, f"{video_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'best',  # Simplified format selection for better compatibility
        'outtmpl': output_template,
        'quiet': False,  # Set to False to see download progress
        'socket_timeout': 30,  # Increase timeout
        'retries': 10,  # Increase number of retries
        'fragment_retries': 10,  # Increase fragment retries
        'skip_download': False,  # Set to True for testing without downloading
        'noplaylist': True,  # Only download single video, not playlist
        # Add options to bypass YouTube restrictions
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],  # Try alternative clients
                'skip': ['hls', 'dash'],  # Skip problematic formats
            }
        },
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Download subtitles/captions
        'writesubtitles': True,
        'writeautomaticsub': True,  # Download auto-generated captions if manual ones not available
        'subtitleslangs': ['en'],  # Prefer English
        'subtitlesformat': 'vtt',  # WebVTT format
    }
    
    try:
        print(f"Starting download from {url}...")
        logger.info(f"Starting video download from URL: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
            
            # Look for downloaded caption files
            caption_path = None
            video_base = os.path.splitext(video_path)[0]
            possible_caption_files = [
                f"{video_base}.en.vtt",
                f"{video_base}.vtt",
            ]
            for caption_file in possible_caption_files:
                if os.path.exists(caption_file):
                    caption_path = caption_file
                    logger.info(f"📝 Found captions: {os.path.basename(caption_path)}")
                    break
            
            print(f"Successfully downloaded to {video_path}")
            logger.info(f"✅ Video downloaded successfully")
            logger.info(f"   - Path: {video_path}")
            logger.info(f"   - Title: {info_dict.get('title', 'N/A')}")
            logger.info(f"   - Uploader: {info_dict.get('uploader', 'N/A')}")
            logger.info(f"   - Duration: {info_dict.get('duration', 'N/A')} seconds")
            logger.info(f"   - Captions: {'Available' if caption_path else 'Not available'}")
            
            return {
                "video_path": video_path,
                "title": info_dict.get('title', 'N/A'),
                "uploader": info_dict.get('uploader', 'N/A'),
                "description": info_dict.get('description', 'N/A')[:500],  # Limit description length
                "caption_path": caption_path
            }
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        logger.error(f"❌ Failed to download video: {str(e)}")
        # For testing purposes, you can return a mock response when download fails
        # This allows the rest of the pipeline to be tested even if YouTube connection fails
        mock_video_path = os.path.join(TEMP_DIR, f"{video_id}_mock.mp4")
        with open(mock_video_path, 'wb') as f:
            f.write(b'MOCK VIDEO')  # Create a small dummy file
        
        logger.warning(f"⚠️  Created mock video for testing at: {mock_video_path}")
        return {
            "video_path": mock_video_path,
            "title": "Mock video due to download error",
            "uploader": "System",
            "description": f"Download failed with error: {str(e)}",
            "caption_path": None
        }

def extract_keyframes(video_path: str, num_frames: int = 20) -> list[str]:
    """
    Extracts a specified number of frames from a video and saves them as JPEGs.
    Returns a list of file paths to the extracted frames.
    If the video cannot be processed, generates placeholder images.
    """
    logger.info(f"Starting keyframe extraction from: {video_path}")
    logger.info(f"Target number of frames: {num_frames}")
    
    frame_paths = []
    try:
        video_id = os.path.basename(video_path).split('.')[0]
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            logger.error(f"❌ Failed to open video file: {video_path}")
            return generate_placeholder_frames(video_id, num_frames)
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video properties - Total frames: {total_frames}, FPS: {fps:.2f}, Duration: {duration:.2f}s")
        
        if total_frames <= 0:
            print(f"Error: Video has no frames or invalid frame count: {total_frames}")
            logger.error(f"❌ Invalid frame count: {total_frames}")
            cap.release()
            return generate_placeholder_frames(video_id, num_frames)
        
        if total_frames < num_frames:
            logger.warning(f"⚠️  Video has fewer frames ({total_frames}) than requested ({num_frames}), adjusting...")
            num_frames = total_frames

        # Extract frames at EQUAL TIME INTERVALS
        # For a 60-second video with 20 frames: extract every 3 seconds
        # Calculate time interval between frames
        time_interval = duration / num_frames  # seconds per frame
        logger.info(f"Extracting frames at {time_interval:.2f} second intervals")
        
        frame_indices = []
        for i in range(num_frames):
            # Calculate the time position for this frame
            time_position = i * time_interval
            # Convert time to frame index
            frame_index = int(time_position * fps)
            # Ensure we don't exceed total frames
            frame_index = min(frame_index, total_frames - 1)
            frame_indices.append(frame_index)
        
        logger.info(f"Frame indices (time-based): {frame_indices}")
        logger.info(f"Time positions: {[f'{i*time_interval:.2f}s' for i in range(num_frames)]}")
        
        for i, frame_index in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(TEMP_DIR, f"{video_id}_frame_{i}.jpg")
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                logger.info(f"✅ Frame {i+1}/{num_frames} extracted - Index: {frame_index} -> {os.path.basename(frame_path)}")
            else:
                print(f"Warning: Could not read frame {frame_index}")
                logger.warning(f"⚠️  Failed to read frame at index {frame_index}")
                
        cap.release()
        
        # If we couldn't extract any frames, generate placeholders
        if not frame_paths:
            print("Warning: No frames could be extracted, generating placeholders")
            logger.warning("⚠️  No frames extracted, generating placeholders")
            return generate_placeholder_frames(video_id, num_frames)
        
        logger.info(f"🎬 Keyframe extraction complete: {len(frame_paths)} frames saved")
        for idx, path in enumerate(frame_paths, 1):
            logger.info(f"   Frame {idx}: {os.path.basename(path)}")
        
        return frame_paths
        
    except Exception as e:
        print(f"Error extracting keyframes: {str(e)}")
        logger.error(f"❌ Error during keyframe extraction: {str(e)}")
        # Generate placeholder frames on error
        return generate_placeholder_frames(os.path.basename(video_path).split('.')[0], num_frames)

def generate_placeholder_frames(video_id: str, num_frames: int = 5) -> list[str]:
    """Generates placeholder image files when video processing fails."""
    logger.info(f"Generating {num_frames} placeholder frames for video_id: {video_id}")
    frame_paths = []
    for i in range(num_frames):
        # Create a blank color image (black background)
        height, width = 480, 640
        img = np.zeros((height, width, 3), np.uint8)
        
        # Add text with error message
        cv2.putText(
            img, 
            f"Error processing video", 
            (width//10, height//2 - 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (255, 255, 255), 
            2
        )
        
        cv2.putText(
            img, 
            f"Frame {i+1} of {num_frames}", 
            (width//10, height//2 + 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (255, 255, 255), 
            2
        )
        
        # Save the placeholder image
        frame_path = os.path.join(TEMP_DIR, f"{video_id}_placeholder_{i}.jpg")
        cv2.imwrite(frame_path, img)
        frame_paths.append(frame_path)
        logger.info(f"   Placeholder {i+1}: {os.path.basename(frame_path)}")
    
    logger.info(f"✅ Generated {len(frame_paths)} placeholder frames")
    return frame_paths

def cleanup_files(files: list[str]):
    """Deletes a list of temporary files."""
    logger.info(f"Cleaning up {len(files)} temporary files")
    cleaned_count = 0
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"   Deleted: {os.path.basename(file_path)}")
                cleaned_count += 1
            except Exception as e:
                logger.error(f"   Failed to delete {os.path.basename(file_path)}: {str(e)}")
    logger.info(f"✅ Cleanup complete: {cleaned_count}/{len(files)} files removed")


def scrape_webpage(url: str) -> dict:
    """
    Scrapes content from a web page including text, images, and metadata.
    Returns a dictionary with scraped content.
    """
    logger.info(f"🌐 Starting webpage scraping for: {url}")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Send GET request with headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'No title found'
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''
        
        # Extract all text content
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text_content = soup.get_text()
        
        # Clean up text: remove extra whitespace
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text length
        max_chars = 10000
        if len(cleaned_text) > max_chars:
            cleaned_text = cleaned_text[:max_chars] + "\n...(content truncated)"
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            img_src = img.get('src', '')
            img_alt = img.get('alt', '')
            if img_src:
                # Convert relative URLs to absolute
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    from urllib.parse import urljoin
                    img_src = urljoin(url, img_src)
                images.append({'src': img_src, 'alt': img_alt})
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().strip()
            link_href = link.get('href')
            if link_href and link_text:
                links.append({'text': link_text, 'href': link_href})
        
        logger.info(f"✅ Webpage scraped successfully")
        logger.info(f"   - Title: {title_text}")
        logger.info(f"   - Text length: {len(cleaned_text)} characters")
        logger.info(f"   - Images found: {len(images)}")
        logger.info(f"   - Links found: {len(links)}")
        
        return {
            'success': True,
            'url': url,
            'title': title_text,
            'description': description,
            'text_content': cleaned_text,
            'images': images[:10],  # Limit to first 10 images
            'links': links[:20],  # Limit to first 20 links
            'word_count': len(cleaned_text.split()),
            'image_count': len(images),
            'link_count': len(links)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch webpage: {str(e)}")
        return {
            'success': False,
            'error': f"Failed to fetch webpage: {str(e)}"
        }
    except Exception as e:
        logger.error(f"❌ Error scraping webpage: {str(e)}")
        return {
            'success': False,
            'error': f"Error scraping webpage: {str(e)}"
        }


def parse_vtt_captions(vtt_path: str) -> str:
    """
    Parses a VTT (WebVTT) caption file and extracts the text content.
    Returns a string with all caption text.
    """
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        caption_text = []
        for line in lines:
            line = line.strip()
            # Skip WEBVTT header, timestamps, and empty lines
            if (line and 
                not line.startswith('WEBVTT') and 
                not '-->' in line and 
                not line.isdigit() and
                not line.startswith('NOTE')):
                caption_text.append(line)
        
        full_text = ' '.join(caption_text)
        logger.info(f"   Parsed {len(caption_text)} caption lines")
        return full_text
    except Exception as e:
        logger.error(f"   Failed to parse VTT file: {str(e)}")
        return ""


def extract_audio_from_video(video_path: str) -> dict:
    """
    Extracts audio from a video file using multiple fallback methods:
    1. Try moviepy (Python-only, no external dependencies)
    2. Try ffmpeg if available
    3. Return error if both fail
    
    Returns dict with audio_path and metadata.
    """
    live_log("=" * 80)
    live_log(f"FUNCTION CALLED: extract_audio_from_video('{video_path}')")
    live_log(f"   Video file exists: {os.path.exists(video_path)}")
    if os.path.exists(video_path):
        live_log(f"   Video file size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    logger.info(f"🎤 Starting audio extraction for: {video_path}")
    logger.info(f"   Video file exists: {os.path.exists(video_path)}")
    logger.info(f"   Video file size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    try:
        live_log("   Creating audio path...")
        video_id = os.path.basename(video_path).split('.')[0]
        audio_path = os.path.join(TEMP_DIR, f"{video_id}_audio.mp3")
        logger.info(f"   Target audio path: {audio_path}")
        live_log(f"   Target audio path: {audio_path}")
        
        # Get video duration
        live_log("   Reading video properties with OpenCV...")
        logger.info(f"   Reading video properties with OpenCV...")
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()
        logger.info(f"   Video duration: {duration:.2f} seconds, FPS: {fps:.2f}")
        live_log(f"   Video duration: {duration:.2f} seconds, FPS: {fps:.2f}")
        
        # Method 1: Try moviepy (Python-only)
        try:
            live_log("   METHOD 1: Trying moviepy for audio extraction...")
            logger.info(f"   Trying moviepy for audio extraction...")
            # moviepy 2.x uses different import structure
            try:
                live_log("   Attempting: from moviepy import VideoFileClip (2.x)")
                from moviepy import VideoFileClip
                logger.info(f"   ✅ Imported VideoFileClip from moviepy (2.x)")
                live_log("   ✅ SUCCESS: Imported VideoFileClip from moviepy (2.x)")
            except ImportError as e1:
                live_log(f"   ❌ moviepy 2.x import failed: {type(e1).__name__}: {str(e1)}")
                logger.info(f"   moviepy 2.x import failed: {e1}, trying 1.x syntax...")
                live_log("   Attempting: from moviepy.editor import VideoFileClip (1.x)")
                # Fallback for moviepy 1.x
                from moviepy.editor import VideoFileClip
                logger.info(f"   ✅ Imported VideoFileClip from moviepy.editor (1.x)")
                live_log("   ✅ SUCCESS: Imported VideoFileClip from moviepy.editor (1.x)")
            
            live_log(f"   Opening video file with moviepy: {video_path}")
            logger.info(f"   Opening video file with moviepy...")
            
            try:
                video_clip = VideoFileClip(video_path)
                logger.info(f"   Video loaded successfully")
                live_log("   Video loaded successfully")
            except (OSError, IOError) as video_error:
                # If VideoFileClip fails, try AudioFileClip (for audio-only MP4/files)
                live_log(f"   ⚠️ VideoFileClip failed: {str(video_error)}")
                logger.info(f"   VideoFileClip failed, trying AudioFileClip for audio-only file...")
                live_log("   Attempting to load as audio-only file with AudioFileClip...")
                
                try:
                    from moviepy import AudioFileClip
                except ImportError:
                    from moviepy.editor import AudioFileClip
                
                audio_clip = AudioFileClip(video_path)
                logger.info(f"   Audio-only file loaded successfully")
                live_log("   Audio-only file loaded successfully")
                live_log(f"   Extracting audio to: {audio_path}")
                
                audio_clip.write_audiofile(audio_path)
                audio_clip.close()
                logger.info(f"   Audio extraction complete, verifying file...")
                live_log("   Audio extraction complete, verifying file...")
                
                if os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    logger.info(f"✅ Audio extracted successfully from audio-only file")
                    live_log(f"✅ SUCCESS: Audio extracted from audio-only file - {file_size / (1024*1024):.2f} MB")
                    
                    return {
                        "status": "success",
                        "method": "moviepy_audio",
                        "audio_path": audio_path,
                        "duration": duration,
                        "file_size": file_size
                    }
                raise Exception("Audio file created but not found")
            
            logger.info(f"   Checking for audio track...")
            live_log("   Checking for audio track...")
            
            if video_clip.audio is not None:
                live_log(f"   Audio track found! Extracting to: {audio_path}")
                logger.info(f"   Audio track found! Extracting to: {audio_path}")
                # MoviePy 2.x changed API - removed 'verbose' and 'logger' parameters
                video_clip.audio.write_audiofile(audio_path)
                video_clip.close()
                logger.info(f"   Audio extraction complete, verifying file...")
                live_log("   Audio extraction complete, verifying file...")
                
                if os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                    logger.info(f"✅ Audio extracted successfully using moviepy")
                    logger.info(f"   - Path: {audio_path}")
                    logger.info(f"   - Size: {file_size / (1024*1024):.2f} MB")
                    logger.info(f"   - Duration: {duration:.2f} seconds")
                    live_log(f"✅ SUCCESS: Audio extracted - {file_size / (1024*1024):.2f} MB")
                    
                    return {
                        "status": "success",
                        "method": "moviepy",
                        "audio_path": audio_path,
                        "duration": duration,
                        "file_size": file_size
                    }
            else:
                live_log("   ⚠️ Video has no audio track")
                logger.warning(f"   Video has no audio track")
                video_clip.close()
                return {
                    "status": "no_audio",
                    "method": "moviepy",
                    "audio_path": None,
                    "error": "Video contains no audio track"
                }
                
        except ImportError as ie:
            live_log(f"   ❌ EXCEPTION (ImportError): {str(ie)}")
            logger.warning(f"   moviepy import failed: {str(ie)}")
            logger.warning(f"   Trying ffmpeg instead...")
            live_log("   Falling back to METHOD 2: ffmpeg")
        except Exception as e:
            live_log(f"   ❌ EXCEPTION ({type(e).__name__}): {str(e)}")
            logger.warning(f"   moviepy failed with error: {type(e).__name__}: {str(e)}")
            logger.warning(f"   Trying ffmpeg instead...")
            import traceback
            logger.debug(f"   Full traceback: {traceback.format_exc()}")
            live_log(f"   Traceback: {traceback.format_exc()}")
            live_log("   Falling back to METHOD 2: ffmpeg")
        
        # Method 2: Try ffmpeg
        try:
            live_log("   METHOD 2: Trying ffmpeg for audio extraction...")
            import subprocess
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame',  # Use MP3 codec
                '-q:a', '2',  # Good quality
                '-y',  # Overwrite output file
                audio_path
            ]
            
            logger.info(f"   Trying ffmpeg for audio extraction...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                logger.info(f"✅ Audio extracted successfully using ffmpeg")
                logger.info(f"   - Path: {audio_path}")
                logger.info(f"   - Size: {file_size / (1024*1024):.2f} MB")
                logger.info(f"   - Duration: {duration:.2f} seconds")
                
                return {
                    "status": "success",
                    "method": "ffmpeg",
                    "audio_path": audio_path,
                    "duration": duration,
                    "file_size": file_size
                }
            else:
                logger.error(f"   ffmpeg failed: {result.stderr[:200]}")
                
        except FileNotFoundError:
            logger.warning(f"   ffmpeg not found")
        except subprocess.TimeoutExpired:
            logger.error(f"   ffmpeg timed out")
        except Exception as e:
            logger.warning(f"   ffmpeg failed: {str(e)}")
        
        # Both methods failed
        live_log("   ❌ BOTH METHODS FAILED - No audio extraction available")
        logger.error(f"❌ Could not extract audio - both moviepy and ffmpeg failed")
        return {
            "status": "error",
            "method": None,
            "audio_path": None,
            "error": "No audio extraction method available. Install moviepy or ffmpeg."
        }
            
    except Exception as e:
        import traceback
        live_log(f"❌ OUTER EXCEPTION ({type(e).__name__}): {str(e)}")
        live_log(f"   Full traceback:\n{traceback.format_exc()}")
        logger.error(f"❌ Error during audio extraction: {type(e).__name__}: {str(e)}")
        logger.error(f"   Full traceback:\n{traceback.format_exc()}")
        return {
            "status": "error",
            "method": None,
            "audio_path": None,
            "error": f"{type(e).__name__}: {str(e)}"
        }


def extract_audio_transcription(video_path: str, caption_path: str = None) -> dict:
    """
    Extracts audio/captions from a video file.
    Priority:
    1. Use YouTube captions if available (fastest, most accurate)
    2. Extract audio file for Gemini to transcribe
    
    Returns dict with caption text and/or audio file path.
    """
    logger.info(f"🎤 Starting audio/caption extraction for: {video_path}")
    
    result = {
        "status": "processing",
        "caption_text": None,
        "audio_path": None,
        "duration": 0,
        "method": None
    }
    
    # Try captions first (if available from YouTube)
    if caption_path and os.path.exists(caption_path):
        logger.info(f"📝 Found YouTube captions, parsing...")
        caption_text = parse_vtt_captions(caption_path)
        
        if caption_text:
            result["caption_text"] = caption_text
            result["status"] = "success"
            result["method"] = "youtube_captions"
            logger.info(f"✅ Captions extracted: {len(caption_text)} characters")
            logger.info(f"   Preview: {caption_text[:100]}...")
    
    # Also extract audio file for Gemini to analyze
    audio_result = extract_audio_from_video(video_path)
    
    if audio_result["status"] == "success":
        result["audio_path"] = audio_result["audio_path"]
        result["duration"] = audio_result.get("duration", 0)
        result["file_size"] = audio_result.get("file_size", 0)
        result["audio_method"] = audio_result.get("method")
        
        if result["status"] != "success":
            result["status"] = "success"
            result["method"] = f"audio_{audio_result['method']}"
    else:
        result["audio_error"] = audio_result.get("error", "Unknown error")
    
    # Final status
    if result["caption_text"] or result["audio_path"]:
        logger.info(f"✅ Audio/caption extraction complete")
        if result["caption_text"]:
            logger.info(f"   - Captions: {len(result['caption_text'])} characters")
        if result["audio_path"]:
            logger.info(f"   - Audio: {os.path.basename(result['audio_path'])}")
    else:
        result["status"] = "failed"
        logger.warning(f"⚠️  No captions or audio could be extracted")
    
    return result


def save_analysis_data(session_path: str, video_metadata: dict, keyframe_paths: list[str], 
                       audio_info: dict = None, gemini_prompt: str = None) -> None:
    """
    Saves all data being sent to Gemini API for inspection.
    
    Args:
        session_path: Path to the analysis session folder
        video_metadata: Video metadata dictionary
        keyframe_paths: List of paths to keyframe images
        audio_info: Audio/caption extraction information (optional)
        gemini_prompt: The prompt being sent to Gemini (optional)
    """
    logger.info(f"💾 Saving analysis data to: {session_path}")
    
    # 1. Save metadata as JSON
    metadata_path = os.path.join(session_path, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(video_metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"   ✅ Saved metadata: {os.path.basename(metadata_path)}")
    
    # 2. Copy all keyframes to analysis folder
    frames_dir = os.path.join(session_path, "keyframes")
    os.makedirs(frames_dir, exist_ok=True)
    
    for i, frame_path in enumerate(keyframe_paths):
        if os.path.exists(frame_path):
            dest_path = os.path.join(frames_dir, f"frame_{i:03d}_{os.path.basename(frame_path)}")
            shutil.copy2(frame_path, dest_path)
            logger.info(f"   ✅ Copied frame {i+1}: {os.path.basename(dest_path)}")
    
    # 3. Save audio/caption info
    if audio_info:
        audio_info_path = os.path.join(session_path, "audio_info.json")
        with open(audio_info_path, 'w', encoding='utf-8') as f:
            # Don't save the full caption text in JSON, save separately
            info_copy = audio_info.copy()
            if 'caption_text' in info_copy and info_copy['caption_text']:
                info_copy['caption_text'] = f"{len(info_copy['caption_text'])} characters (see captions.txt)"
            json.dump(info_copy, f, indent=2, ensure_ascii=False)
        logger.info(f"   ✅ Saved audio info: {os.path.basename(audio_info_path)}")
        
        # Save caption text separately
        if audio_info.get('caption_text'):
            caption_text_path = os.path.join(session_path, "captions.txt")
            with open(caption_text_path, 'w', encoding='utf-8') as f:
                f.write(audio_info['caption_text'])
            logger.info(f"   ✅ Saved captions: {os.path.basename(caption_text_path)} ({len(audio_info['caption_text'])} chars)")
        
        # Copy audio file to analysis folder if available
        if audio_info.get('audio_path') and os.path.exists(audio_info['audio_path']):
            audio_dest = os.path.join(session_path, os.path.basename(audio_info['audio_path']))
            shutil.copy2(audio_info['audio_path'], audio_dest)
            logger.info(f"   ✅ Copied audio file: {os.path.basename(audio_dest)}")
        
        # Copy original caption file if available
        if video_metadata.get('caption_path') and os.path.exists(video_metadata['caption_path']):
            caption_dest = os.path.join(session_path, os.path.basename(video_metadata['caption_path']))
            shutil.copy2(video_metadata['caption_path'], caption_dest)
            logger.info(f"   ✅ Copied caption file: {os.path.basename(caption_dest)}")
    
    # 4. Save Gemini prompt if provided
    if gemini_prompt:
        prompt_path = os.path.join(session_path, "gemini_prompt.txt")
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(gemini_prompt)
        logger.info(f"   ✅ Saved Gemini prompt: {os.path.basename(prompt_path)}")
    
    # 5. Create a summary README
    readme_path = os.path.join(session_path, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# Analysis Session\n\n")
        f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Video Information\n\n")
        f.write(f"- **Title:** {video_metadata.get('title', 'N/A')}\n")
        f.write(f"- **Uploader:** {video_metadata.get('uploader', 'N/A')}\n")
        f.write(f"- **Video Path:** {video_metadata.get('video_path', 'N/A')}\n\n")
        f.write(f"## Extracted Data\n\n")
        f.write(f"- **Keyframes:** {len(keyframe_paths)} frames extracted\n")
        if audio_info:
            f.write(f"- **Audio/Captions:** {audio_info.get('status', 'N/A')}\n")
            if audio_info.get('caption_text'):
                f.write(f"  - YouTube Captions: {len(audio_info['caption_text'])} characters\n")
            if audio_info.get('audio_path'):
                f.write(f"  - Audio File: {os.path.basename(audio_info['audio_path'])} ")
                f.write(f"({audio_info.get('duration', 0):.2f}s, {audio_info.get('file_size', 0)/(1024*1024):.2f} MB)\n")
            if audio_info.get('method'):
                f.write(f"  - Extraction Method: {audio_info['method']}\n")
        f.write(f"- **Gemini Prompt:** {'Saved' if gemini_prompt else 'Not provided'}\n\n")
        f.write(f"## Files in This Session\n\n")
        f.write(f"- `metadata.json` - Complete video metadata\n")
        f.write(f"- `keyframes/` - Extracted video frames ({len(keyframe_paths)} frames)\n")
        if audio_info:
            if audio_info.get('caption_text'):
                f.write(f"- `captions.txt` - Extracted YouTube captions/subtitles\n")
            if audio_info.get('audio_path'):
                f.write(f"- `{os.path.basename(audio_info['audio_path'])}` - Extracted audio file\n")
            f.write(f"- `audio_info.json` - Audio/caption extraction details\n")
        if gemini_prompt:
            f.write(f"- `gemini_prompt.txt` - Exact prompt sent to Gemini API\n")
    
    logger.info(f"   ✅ Created README: {os.path.basename(readme_path)}")


def extract_embedded_images_from_pdf(pdf_path: str, output_dir: str) -> tuple[list[str], bool]:
    """
    Extracts ONLY embedded images from PDF (photos, diagrams, etc.).
    Does NOT render text pages as images.
    Returns: (list of image paths, has_text_content)
    """
    try:
        import fitz  # PyMuPDF
        import os
        
        live_log(f"   🖼️ Scanning PDF for embedded images and text content...")
        
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        total_text_length = 0
        
        # Open PDF
        pdf_document = fitz.open(pdf_path)
        
        # First pass: Check if PDF has text content
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            total_text_length += len(text.strip())
        
        has_text_content = total_text_length > 100  # More than 100 chars = text-based PDF
        
        live_log(f"   📊 PDF Analysis: {total_text_length} characters found")
        live_log(f"   📄 PDF Type: {'Text-based' if has_text_content else 'Image-based/Scanned'}")
        
        # Extract embedded images from each page
        image_count = 0
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Get list of images on this page
            image_list = page.get_images(full=True)
            
            if image_list:
                live_log(f"   📸 Page {page_num + 1}: Found {len(image_list)} embedded image(s)")
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]  # Image reference number
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Save embedded image
                    image_filename = f"embedded_page{page_num + 1}_img{img_index + 1}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    image_paths.append(image_path)
                    image_count += 1
                    live_log(f"   ✅ Extracted: {image_filename}")
                    
                except Exception as e:
                    live_log(f"   ⚠️ Failed to extract image {img_index + 1} from page {page_num + 1}: {e}")
                    continue
        
        pdf_document.close()
        
        if image_count > 0:
            live_log(f"   ✅ Total embedded images extracted: {image_count}")
        else:
            live_log(f"   ℹ️ No embedded images found in PDF")
        
        return image_paths, has_text_content
        
    except ImportError:
        live_log(f"   ❌ PyMuPDF not installed. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "PyMuPDF"], check=True)
        live_log(f"   ✅ PyMuPDF installed. Please retry the upload.")
        return [], False
    except Exception as e:
        live_log(f"   ❌ Failed to extract images: {e}")
        return [], False


def render_pdf_pages_as_images(pdf_path: str, output_dir: str) -> list[str]:
    """
    Renders PDF pages as images (for scanned/image-based PDFs).
    Use this ONLY when PDF has no extractable text.
    """
    try:
        import fitz  # PyMuPDF
        import os
        
        live_log(f"   📸 Rendering PDF pages as images for OCR...")
        
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        
        # Open PDF
        pdf_document = fitz.open(pdf_path)
        
        # Render each page as an image
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Render page to image (high quality)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            
            # Save as PNG
            image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
            pix.save(image_path)
            image_paths.append(image_path)
            
            live_log(f"   ✅ Rendered page {page_num + 1}/{len(pdf_document)} as image")
        
        pdf_document.close()
        live_log(f"   ✅ Rendered {len(image_paths)} pages as images")
        
        return image_paths
        
    except Exception as e:
        live_log(f"   ❌ Failed to render pages: {e}")
        return []


def extract_text_with_ocr(pdf_path: str) -> str:
    """
    Extracts text from scanned/image-based PDFs using OCR (Tesseract).
    Falls back gracefully if OCR dependencies are not available.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image
        import os
        
        # Configure Tesseract path if needed (Windows)
        # Try common installation locations automatically
        possible_tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\portable_ocr\tesseract\tesseract.exe',
        ]
        
        for tess_path in possible_tesseract_paths:
            if os.path.exists(tess_path):
                pytesseract.pytesseract.tesseract_cmd = tess_path
                live_log(f"   🔧 Found Tesseract at: {tess_path}")
                break
        
        # Try common Poppler locations
        possible_poppler_paths = [
            r'C:\poppler\poppler-24.08.0\Library\bin',
            r'C:\Program Files\poppler\Library\bin',
            r'C:\portable_ocr\poppler\Library\bin',
        ]
        
        poppler_path = None
        for pop_path in possible_poppler_paths:
            if os.path.exists(pop_path):
                poppler_path = pop_path
                live_log(f"   🔧 Found Poppler at: {pop_path}")
                break
        
        live_log(f"   📸 Converting PDF pages to images for OCR...")
        
        # Convert PDF to images (one image per page)
        try:
            if poppler_path:
                images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
            else:
                images = convert_from_path(pdf_path, dpi=300)  # Try without path (if in PATH)
            live_log(f"   ✅ Converted {len(images)} pages to images")
        except Exception as e:
            live_log(f"   ❌ Failed to convert PDF to images: {e}")
            return f"ERROR: Could not convert PDF to images. Make sure poppler is installed. Error: {str(e)}"
        
        # Extract text from each page using OCR
        extracted_text = ""
        for page_num, image in enumerate(images, start=1):
            try:
                live_log(f"   🔍 Running OCR on page {page_num}/{len(images)}...")
                page_text = pytesseract.image_to_string(image, lang='eng')
                extracted_text += f"\n--- Page {page_num} ---\n{page_text}\n"
                live_log(f"   ✅ Page {page_num}: Extracted {len(page_text)} characters")
            except Exception as e:
                live_log(f"   ⚠️ OCR failed for page {page_num}: {e}")
                continue
        
        total_chars = len(extracted_text.strip())
        if total_chars > 0:
            live_log(f"   ✅ OCR Complete: Extracted {total_chars} characters from {len(images)} pages")
            return extracted_text
        else:
            live_log(f"   ❌ OCR extracted no text from any page")
            return "ERROR: OCR completed but no text was extracted. The PDF might be blank or have very low quality images."
            
    except ImportError as e:
        missing_lib = str(e).split("'")[-2] if "'" in str(e) else "unknown"
        live_log(f"   ❌ OCR library not available: {missing_lib}")
        return f"ERROR: OCR requires pytesseract and pdf2image. Please install: pip install pytesseract pdf2image. Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
    except Exception as e:
        live_log(f"   ❌ OCR failed with error: {type(e).__name__}: {str(e)}")
        return f"ERROR: OCR processing failed: {str(e)}"


def extract_text_from_document(doc_path: str, file_ext: str) -> str:
    """
    Extracts text from various document formats (PDF, DOCX, TXT, etc.)
    """
    live_log(f"FUNCTION CALLED: extract_text_from_document('{doc_path}', '{file_ext}')")
    
    try:
        if file_ext == '.txt' or file_ext == '.rtf':
            # Plain text files
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                live_log(f"   Extracted {len(text)} characters from text file")
                return text
        
        elif file_ext == '.pdf':
            # PDF files - use PyPDF2 or pdfplumber, with OCR fallback for scanned PDFs
            try:
                import PyPDF2
                text = ""
                with open(doc_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_pages = len(pdf_reader.pages)
                    
                    for page_num in range(num_pages):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    
                    text_len = len(text.strip())
                    live_log(f"   Extracted {text_len} characters from PDF ({num_pages} pages)")
                    
                    # Check if PDF is likely scanned/image-based
                    if text_len < 50 and num_pages > 0:
                        live_log(f"   ⚠️ WARNING: Very little text extracted ({text_len} chars).")
                        live_log(f"   🎨 This appears to be a scanned/image-based PDF.")
                        live_log(f"   💡 Will extract images and use Gemini Vision API instead.")
                        
                        # Return special marker to indicate image-based PDF
                        return "IMAGE_BASED_PDF"
                    
                    return text
            except ImportError:
                live_log("   PyPDF2 not installed, trying pdfplumber...")
                try:
                    import pdfplumber
                    text = ""
                    with pdfplumber.open(doc_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    live_log(f"   Extracted {len(text.strip())} characters from PDF")
                    
                    if len(text.strip()) < 50:
                        live_log(f"   ⚠️ WARNING: Very little text extracted. Attempting OCR...")
                        ocr_text = extract_text_with_ocr(doc_path)
                        if ocr_text and not ocr_text.startswith("ERROR:"):
                            return ocr_text
                    
                    return text
                except ImportError:
                    live_log("   ERROR: Neither PyPDF2 nor pdfplumber installed")
                    return "ERROR: PDF extraction requires PyPDF2 or pdfplumber. Install with: pip install PyPDF2"
        
        elif file_ext in ['.docx', '.doc']:
            # Word documents - use python-docx
            try:
                import docx
                doc = docx.Document(doc_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                live_log(f"   Extracted {len(text)} characters from Word document")
                return text
            except ImportError:
                live_log("   ERROR: python-docx not installed")
                return "ERROR: Word document extraction requires python-docx. Install with: pip install python-docx"
        
        else:
            return f"Unsupported document format: {file_ext}"
            
    except Exception as e:
        live_log(f"   ERROR: {type(e).__name__}: {str(e)}")
        logger.error(f"Document text extraction failed: {e}")
        return f"Error extracting text: {str(e)}"

    logger.info(f"📦 Analysis data saved successfully in: {os.path.basename(session_path)}")
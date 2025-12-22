# File Upload Feature Documentation

## Overview
Vigil AI Lite now supports direct file uploads for authenticity analysis. Users can upload their own media files instead of just analyzing URLs.

## Supported File Types

### 🎬 Video Files
- **Formats**: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V
- **Analysis**: 20 keyframe extraction, audio analysis, deepfake detection, visual manipulation detection
- **Same process as**: Instagram, Facebook, TikTok video analysis

### 🎵 Audio Files
- **Formats**: MP3, WAV, M4A, AAC, OGG, FLAC, WMA
- **Analysis**: 
  - AI-generated voice detection (deepfake audio)
  - Audio manipulation indicators (splicing, pitch shifting)
  - Background noise analysis
  - Recording quality and consistency
  - Content and claim verification

### 📄 Document Files
- **Formats**: PDF, DOCX, DOC, TXT, RTF
- **Analysis**:
  - Document credibility assessment
  - Source and author verification
  - Fact-checking of claims
  - Bias detection
  - Citation quality evaluation
  - Statistical manipulation detection
- **Dependencies**: PyPDF2, python-docx

### 🖼️ Image Files
- **Formats**: JPG, JPEG, PNG, GIF, WEBP, BMP, TIFF
- **Analysis**:
  - Digital manipulation detection (Photoshop, AI generation)
  - Metadata analysis
  - Compression artifacts
  - Lighting/shadow inconsistencies
  - Deepfake face detection
  - Reverse image search recommendations

## API Endpoint

### POST /analyze/upload
Multipart form data endpoint for file uploads.

**Request**:
```
Content-Type: multipart/form-data
file: <binary file data>
```

**Response**:
```json
{
  "source": "Vigil AI Generative Analysis (Uploaded Video/Audio/Document/Image)",
  "file_type": "video|audio|document|image",
  "filename": "example.mp4",
  "report": {
    // Gemini analysis results specific to file type
  },
  "analysis_session": "analysis/20251002_HHMMSS_filename/"
}
```

## Frontend Implementation

### Tab-Based UI
- **Analyze URL Tab**: Original URL input functionality
- **Upload File Tab**: Drag-and-drop file upload interface

### FileUpload Component (`src/components/FileUpload.js`)
- Drag-and-drop support
- File type validation
- Visual file preview with icon and size
- Progress indication during upload

### User Flow
1. User selects "Upload File" tab
2. Either clicks to browse or drags file into drop zone
3. File information displayed with icon and size
4. Click "Analyze File" button
5. File uploaded to backend via FormData
6. Analysis results displayed in same ReportCard component

## Backend Processing Flow

### 1. File Reception
- File saved to `temp_media/` with UUID
- File extension validated
- Size logged

### 2. Type Detection & Routing
```python
if file_ext in video_extensions:
    analyze_uploaded_video()
elif file_ext in audio_extensions:
    analyze_uploaded_audio()
elif file_ext in document_extensions:
    analyze_uploaded_document()
elif file_ext in image_extensions:
    analyze_uploaded_image()
```

### 3. Analysis Process

#### Video Files
1. Extract 20 keyframes (time-based intervals)
2. Extract audio with moviepy
3. Send to Gemini with same prompt as video platform analysis
4. Save all artifacts to analysis session folder

#### Audio Files
1. Upload audio directly to Gemini
2. Specialized audio forensics prompt
3. Deepfake detection and content analysis
4. Save results to analysis session

#### Document Files
1. Extract text:
   - TXT/RTF: Direct read
   - PDF: PyPDF2 extraction
   - DOCX/DOC: python-docx extraction
2. Truncate to 50,000 chars if needed
3. Send to Gemini with document analysis prompt
4. Save extracted text and results

#### Image Files
1. Upload image directly to Gemini
2. Specialized image forensics prompt
3. Manipulation detection and context analysis
4. Save results to analysis session

### 4. Analysis Session Creation
Each upload creates timestamped folder:
```
analysis/20251002_094523_filename/
├── metadata.json
├── gemini_prompt.txt
├── gemini_response_raw.txt
├── gemini_response.json
├── uploaded_image.jpg (for images)
├── extracted_text.txt (for documents)
├── keyframes/ (for videos)
└── video_audio.mp3 (for videos)
```

## Gemini Prompts

### Audio Analysis Prompt
- Audio authenticity assessment (deepfake detection)
- Content analysis (claims, speaker, tone)
- Misinformation indicators
- Red flags
- Final verdict with confidence

### Document Analysis Prompt
- Document credibility
- Content analysis (claims, evidence, bias)
- Fact verification
- Misinformation indicators
- Red flags
- Final verdict

### Image Analysis Prompt
- Image authenticity assessment
- Manipulation detection
- Content analysis
- Misinformation context
- Red flags
- Final verdict with confidence

## Installation

### Backend Dependencies
```bash
pip install PyPDF2 python-docx
```

Or from requirements.txt:
```bash
pip install -r requirements.txt
```

### Frontend
No additional dependencies needed (uses existing axios for file upload).

## Usage Examples

### Upload Video
```bash
curl -X POST http://localhost:8000/analyze/upload \
  -F "file=@suspicious_video.mp4"
```

### Upload PDF
```bash
curl -X POST http://localhost:8000/analyze/upload \
  -F "file=@research_paper.pdf"
```

### Upload Audio
```bash
curl -X POST http://localhost:8000/analyze/upload \
  -F "file=@voice_recording.mp3"
```

### Upload Image
```bash
curl -X POST http://localhost:8000/analyze/upload \
  -F "file=@suspicious_photo.jpg"
```

## Error Handling

### Unsupported File Type
```json
{
  "detail": "Unsupported file type: .xyz"
}
```

### Document Extraction Failure
```json
{
  "detail": "Could not extract text from document."
}
```

### Analysis Failure
Returns partial results with error information in the report object.

## Security Considerations

1. **File Size Limits**: Consider adding max file size validation
2. **File Type Validation**: Server-side validation beyond extension checking
3. **Virus Scanning**: Consider integrating antivirus scanning for uploads
4. **Rate Limiting**: Implement rate limits on upload endpoint
5. **Cleanup**: Temporary files cleaned up after analysis

## Future Enhancements

1. **Batch Upload**: Multiple file analysis
2. **Comparison Mode**: Compare two files for consistency
3. **Advanced PDF**: Extract images from PDFs for separate analysis
4. **Audio Transcription**: Speech-to-text for audio files
5. **Video Metadata**: EXIF and metadata extraction
6. **Progress Tracking**: Real-time upload and analysis progress
7. **File Size Optimization**: Compress large files before upload

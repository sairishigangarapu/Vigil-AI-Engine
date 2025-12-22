# Vigil AI - System Overview

## 🎯 Project Purpose
Vigil AI is a multimodal misinformation detection system that analyzes videos, images, audio, and web content using Google Gemini AI to identify potential fake news, deepfakes, and misleading information.

## 🏗️ Architecture

### High-Level Flow
```
User Input (URL) → Type Detection → Processing Pipeline → Gemini Analysis → Risk Assessment → User
```

### Components

#### 1. **Frontend** (React)
- Location: `frontend/`
- Interface for submitting URLs and displaying analysis results
- Real-time processing status updates

#### 2. **Backend** (FastAPI)
- Location: `backend/`
- REST API server running on `http://localhost:8000`
- Three main modules:
  - `main.py` - API routing and URL type detection
  - `video_processor.py` - Media download, extraction, web scraping
  - `fact_checker.py` - Gemini AI integration and fact-checking

## 🔄 Processing Pipelines

### Pipeline 1: YouTube URLs (Direct Processing)
**Speed: Fast (~5-10 seconds)**

```
YouTube URL → detect_url_type()
              ↓
          analyze_youtube_url()
              ↓
      analyze_youtube_with_gemini()
              ↓
   Send URL directly to Gemini
              ↓
          Analysis Response
```

**Advantages:**
- No download required
- Fastest method
- Full video + audio analysis
- No storage used

### Pipeline 2: Video Platforms (Download & Extract)
**Speed: Medium (~30-120 seconds)**

**Supported Platforms:**
- Instagram
- Facebook
- TikTok
- Twitter/X
- Vimeo
- Dailymotion
- Twitch

```
Platform URL → detect_url_type()
                ↓
           analyze_video_platform()
                ↓
       download_video_and_get_metadata() (yt-dlp)
                ↓
       ┌────────┴────────┐
       ↓                 ↓
extract_keyframes()  extract_audio_transcription()
   (20 frames)      (captions + audio)
       ↓                 ↓
       └────────┬────────┘
                ↓
      analyze_with_gemini()
                ↓
       Gemini analyzes frames + audio
                ↓
         Analysis Response
                ↓
    Save to analysis/ folder
```

**Output Files:**
- `analysis/YYYYMMDD_HHMMSS_VideoTitle/`
  - `metadata.json` - Video metadata
  - `gemini_prompt.txt` - Prompt sent to Gemini
  - `gemini_response.json` - Parsed response
  - `gemini_response_raw.txt` - Raw response
  - `captions.txt` - Extracted captions
  - `audio_info.json` - Audio metadata
  - `video_audio.mp3` - Extracted audio
  - `keyframes/` - 20 JPEG frames
  - `README.md` - Analysis summary

### Pipeline 3: Web Pages (Scrape Content)
**Speed: Fast (~1-3 seconds)**

```
Web URL → detect_url_type()
           ↓
      analyze_webpage()
           ↓
      scrape_webpage() (BeautifulSoup4)
           ↓
    Extract: title, text, images, links
           ↓
   analyze_webpage_with_gemini()
           ↓
    Gemini analyzes content
           ↓
     Analysis Response
```

**Extracted Data:**
- Page title
- Meta description
- Text content (max 10,000 chars)
- First 10 images
- First 20 links
- Word count

## 🧠 AI Analysis

### Gemini 2.5 Pro
- Model: `gemini-2.0-flash-exp`
- Multimodal capabilities: video, audio, images, text

### Analysis Prompts

#### YouTube/Video Analysis
```
You are an advanced AI trained in OSINT and media forensics...

Analyze this video for potential misinformation:
1. Context Check (original footage vs. edited/recontextualized)
2. Audio-Visual Analysis (claims, consistency, manipulation)
3. Claim Verification (corroborate with known facts)
4. Visual Red Flags (deepfakes, edits, inconsistencies)

Output: risk_level, summary, detailed analysis
```

#### Webpage Analysis
```
You are a fact-checking AI analyzing web content...

Assess this content for misinformation:
1. Source Credibility
2. Claim Analysis
3. Fact Verification
4. Content Red Flags

Output: risk_level, summary, detailed analysis
```

### Risk Levels
- **Verified**: Authentic and verified by multiple credible sources
- **Low Risk**: Minor concerns but generally trustworthy
- **Medium Risk**: Some unverified claims or potential issues
- **High Risk**: Contains misinformation, manipulation, or debunked claims
- **Error**: Analysis failed or could not be completed

## 📊 Response Format

### Standard Response Structure
```json
{
  "source": "Vigil AI Generative Analysis (YouTube Direct/Video Platform/Web Content)",
  "url_type": "youtube|video_platform|webpage",
  "report": {
    "risk_level": "Low Risk|Medium Risk|High Risk|Verified|Error",
    "summary": "Brief analysis summary...",
    // Type-specific fields...
  },
  "analysis_session": "analysis/YYYYMMDD_HHMMSS_VideoTitle" // Only for video platforms
}
```

### Video Platform Response Fields
```json
{
  "context_check": {
    "status": "Context Match|Context Mismatch|No Earlier Context Found",
    "details": "..."
  },
  "audio_analysis": {
    "key_claims": ["claim1", "claim2"],
    "audio_visual_match": "...",
    "manipulation_detected": "..."
  },
  "claim_verification": {
    "status": "Corroborated|Uncorroborated|Debunked",
    "details": "..."
  },
  "visual_red_flags": ["flag1", "flag2"]
}
```

### Webpage Response Fields
```json
{
  "source_credibility": {
    "status": "Credible|Not Credible|Mixed",
    "details": "..."
  },
  "claim_analysis": {
    "main_claims": ["claim1", "claim2"],
    "claim_types": "Factual|Opinion|Mixed",
    "sensationalism_detected": "..."
  },
  "fact_verification": {
    "status": "Verified|Unverified|Debunked",
    "details": "..."
  },
  "content_red_flags": ["flag1", "flag2"]
}
```

## 🔧 Technology Stack

### Backend
- **FastAPI**: REST API framework
- **Python 3.12**: Core language
- **yt-dlp**: Video/audio downloading from 1000+ sites
- **OpenCV**: Frame extraction from videos
- **moviepy**: Python-only audio extraction
- **ffmpeg**: Fallback audio extraction (optional)
- **BeautifulSoup4**: Web scraping
- **Google Generative AI**: Gemini API client
- **requests**: HTTP client

### Frontend
- **React**: UI framework
- **JavaScript/JSX**: Core language

### Key Dependencies
```txt
fastapi
uvicorn
opencv-python-headless
yt-dlp
google-generativeai
python-dotenv
requests
python-multipart
pydantic
moviepy
beautifulsoup4
```

## 🚀 Setup & Usage

### 1. Environment Setup
```bash
# Create .env file in backend/
GEMINI_API_KEY=your_api_key_here
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Start Backend
```bash
python main.py
# Server runs on http://localhost:8000
```

### 4. Start Frontend (if applicable)
```bash
cd frontend
npm install
npm start
# Frontend runs on http://localhost:3000
```

### 5. Test API
```bash
# YouTube video
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'

# Instagram video
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.instagram.com/p/ABC123/"}'

# News article
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.example.com/news/article"}'
```

## 📁 Project Structure

```
vigilant-octo-enigma/
├── backend/
│   ├── main.py                 # API routing and URL detection
│   ├── video_processor.py      # Media processing and scraping
│   ├── fact_checker.py         # Gemini AI integration
│   ├── requirements.txt        # Python dependencies
│   ├── test.py                 # Testing utilities
│   └── test_api.py             # API tests
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   └── components/
│   ├── public/
│   └── package.json
├── analysis/                   # Analysis session storage
│   └── YYYYMMDD_HHMMSS_Title/
│       ├── metadata.json
│       ├── gemini_prompt.txt
│       ├── gemini_response.json
│       ├── captions.txt
│       ├── audio_info.json
│       ├── video_audio.mp3
│       ├── keyframes/
│       └── README.md
├── temp_media/                 # Temporary downloads (auto-cleaned)
├── API.md                      # API documentation
├── FFMPEG_SETUP.md            # FFmpeg setup guide
├── URL_ROUTING.md             # URL routing documentation
├── ANALYSIS_INSPECTION.md     # Analysis folder guide
├── SYSTEM_OVERVIEW.md         # This file
└── README.md                  # Project README
```

## 🔍 URL Detection Logic

```python
def detect_url_type(url: str) -> str:
    """
    Detects the type of URL provided.
    
    Returns:
        - "youtube": YouTube video URLs
        - "video_platform": Instagram, Facebook, TikTok, Twitter, etc.
        - "webpage": Regular web pages
    """
    domain = urlparse(url).netloc.lower()
    
    # YouTube patterns
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    if any(yt in domain for yt in youtube_domains):
        return "youtube"
    
    # Video platforms
    video_platforms = ['instagram.com', 'facebook.com', 'fb.watch', 
                      'tiktok.com', 'twitter.com', 'x.com', 'vimeo.com',
                      'dailymotion.com', 'twitch.tv']
    if any(platform in domain for platform in video_platforms):
        return "video_platform"
    
    # Default to webpage
    return "webpage"
```

## 📝 Logging System

All operations are logged with emoji indicators:

- ✅ Success
- ❌ Error
- ⚠️ Warning
- 🎬 Video processing
- 📝 Caption extraction
- 🎤 Audio processing
- 🌐 Web scraping
- 💾 Data saving
- 📤 Gemini API call

## 🔒 Security Considerations

### Current Implementation
- CORS enabled for localhost development
- API key stored in `.env` file
- Temporary files auto-cleaned
- Input URL validation

### Production Recommendations
- Add rate limiting
- Implement authentication
- Add content filtering
- Set up HTTPS
- Add request size limits
- Implement proper error handling
- Add logging and monitoring
- Set up database for analysis history

## ⚡ Performance Metrics

| URL Type | Processing Time | Downloads | Storage |
|----------|----------------|-----------|---------|
| YouTube | 5-10 seconds | None | None |
| Instagram | 30-60 seconds | Video | 50-200 MB |
| Facebook | 30-90 seconds | Video | 50-300 MB |
| TikTok | 20-40 seconds | Video | 20-100 MB |
| Web Page | 1-3 seconds | None | None |

**Factors affecting speed:**
- Video length (longer videos = more processing)
- Video quality (higher quality = larger files)
- Network speed (download speed)
- Server load (Gemini API response time)

## 🐛 Troubleshooting

### YouTube Download Errors
- ✅ FIXED: Added Android client fallback in yt-dlp
- Configuration: `extractor_args={'youtube': {'player_client': ['android', 'web']}}`

### FFmpeg Not Found
- ✅ OPTIONAL: moviepy provides Python-only audio extraction
- Fallback chain: moviepy → ffmpeg → no audio

### Import Errors
- Pylance may show import errors if packages are installed in user directory
- Run `pip list` to verify packages are actually installed
- Code will work despite Pylance warnings

### Gemini API Errors
- Check `.env` file has valid `GEMINI_API_KEY`
- Verify API key has Gemini API enabled
- Check quota limits on Google Cloud Console

## 📚 Documentation

- [API.md](API.md) - Complete API reference
- [URL_ROUTING.md](URL_ROUTING.md) - URL routing system details
- [FFMPEG_SETUP.md](FFMPEG_SETUP.md) - FFmpeg installation guide
- [ANALYSIS_INSPECTION.md](ANALYSIS_INSPECTION.md) - Analysis folder structure

## 🎓 Learning Resources

### yt-dlp
- [Documentation](https://github.com/yt-dlp/yt-dlp)
- Supports 1000+ sites
- Powerful extraction options

### Google Gemini
- [API Documentation](https://ai.google.dev/)
- Multimodal AI capabilities
- Vision, audio, text analysis

### FastAPI
- [Documentation](https://fastapi.tiangolo.com/)
- Modern Python web framework
- Automatic OpenAPI docs at `/docs`

## 🔮 Future Enhancements

### Planned Features
- [ ] Database storage for analysis history
- [ ] User authentication system
- [ ] Advanced deepfake detection
- [ ] Multi-language support
- [ ] Browser extension
- [ ] Mobile app
- [ ] Batch processing
- [ ] Export reports (PDF/JSON)
- [ ] Integration with fact-checking databases
- [ ] Real-time monitoring of social media

### Technical Improvements
- [ ] Caching layer for repeated URLs
- [ ] Queue system for long-running tasks
- [ ] Webhooks for async processing
- [ ] CDN integration for faster access
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Monitoring and alerting
- [ ] A/B testing framework

## 👥 Contributing

This is a hackathon project. Future contributions welcome!

## 📄 License

See [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for Google Hackathon**

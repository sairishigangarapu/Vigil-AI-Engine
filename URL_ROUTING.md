# Smart URL Routing System

## Overview

The application now intelligently detects the type of URL and uses the optimal analysis method for each platform.

## URL Type Detection

### 1. YouTube URLs (Direct Processing)
**Domains detected:**
- `youtube.com`
- `youtu.be`
- `m.youtube.com`
- `youtube-nocookie.com`

**Processing Method:**
- ✅ **No download required!**
- Sends YouTube URL directly to Gemini
- Gemini processes the video natively
- Fastest analysis method
- Full video + audio analysis by Gemini

**Benefits:**
- ⚡ Fast - No video download
- 💾 No disk space used
- 🎯 Full video analysis (not just 20 frames)
- 🎤 Complete audio analysis (not extracted)
- 🌐 Works with any YouTube video

### 2. Video Platform URLs (Download & Extract)
**Domains detected:**
- `instagram.com`
- `facebook.com` / `fb.watch`
- `tiktok.com`
- `twitter.com` / `x.com`
- `vimeo.com`
- `dailymotion.com`
- `twitch.tv`

**Processing Method:**
- Downloads video using yt-dlp
- Extracts 20 keyframes (equally spaced)
- Extracts audio/captions
- Sends frames + audio to Gemini
- Creates analysis session folder

**Benefits:**
- 🎬 Works with any video platform
- 📊 Detailed frame-by-frame analysis
- 🎤 Audio extraction and analysis
- 💾 All data saved for inspection

### 3. Regular Web Pages (Scrape Content)
**All other URLs**

**Processing Method:**
- Scrapes page content using BeautifulSoup4
- Extracts: title, text, images, links
- Sends scraped content to Gemini
- No video processing

**Benefits:**
- 📰 Analyzes news articles
- 🌐 Works with any website
- 📝 Text-based fact-checking
- 🔗 Analyzes linked sources

## API Response Format

All responses include a `url_type` field:

### YouTube Response
```json
{
  "source": "Vigil AI Generative Analysis (YouTube Direct)",
  "url_type": "youtube",
  "report": {
    "risk_level": "Low Risk",
    "summary": "...",
    "context_check": {...},
    "audio_visual_analysis": {...},
    "claim_verification": {...},
    "visual_red_flags": [...]
  }
}
```

### Video Platform Response
```json
{
  "source": "Vigil AI Generative Analysis (Video Platform)",
  "url_type": "video_platform",
  "report": {
    "risk_level": "Medium Risk",
    "summary": "...",
    "context_check": {...},
    "audio_analysis": {...},
    "claim_verification": {...},
    "visual_red_flags": [...]
  },
  "analysis_session": "analysis/20251001_143025_Video_Title"
}
```

### Webpage Response
```json
{
  "source": "Vigil AI Generative Analysis (Web Content)",
  "url_type": "webpage",
  "report": {
    "risk_level": "High Risk",
    "summary": "...",
    "source_credibility": {...},
    "claim_analysis": {...},
    "fact_verification": {...},
    "content_red_flags": [...]
  }
}
```

## Analysis Workflow

```
┌─────────────────┐
│   User submits  │
│      URL        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Detect URL     │
│     Type        │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬─────────┐
    │         │            │         │
    ▼         ▼            ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│YouTube │ │Instagram│ │Facebook│ │Webpage │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    │          └──────────┴──────────┤
    │                                │
    ▼                                ▼
┌─────────────┐              ┌─────────────┐
│Send URL     │              │Download &   │
│directly to  │              │Process      │
│Gemini       │              │locally      │
└──────┬──────┘              └──────┬──────┘
       │                            │
       └──────────┬─────────────────┘
                  ▼
         ┌────────────────┐
         │ Fact Check API │
         │   (Triage)     │
         └────────┬───────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
    ┌────────┐        ┌────────┐
    │ Found  │        │Not Found│
    │Return  │        │Escalate │
    │Result  │        │to Gemini│
    └────────┘        └───┬────┘
                          │
                          ▼
                   ┌─────────────┐
                   │Return Gemini│
                   │   Analysis  │
                   └─────────────┘
```

## Example Usage

### Testing YouTube
```bash
POST /analyze
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```
Result: Direct Gemini processing, no download

### Testing Instagram
```bash
POST /analyze
{
  "video_url": "https://www.instagram.com/p/ABC123/"
}
```
Result: Download → Extract frames/audio → Gemini analysis

### Testing News Article
```bash
POST /analyze
{
  "video_url": "https://www.example.com/news/article"
}
```
Result: Scrape content → Gemini analysis

## Performance Comparison

| URL Type | Download Time | Processing Time | Disk Space | Analysis Quality |
|----------|--------------|-----------------|------------|------------------|
| YouTube | None | ~5-10s | None | ⭐⭐⭐⭐⭐ (Full video) |
| Video Platform | 30-120s | ~20-30s | 100-500MB | ⭐⭐⭐⭐ (20 frames + audio) |
| Webpage | 1-3s | ~5-10s | Minimal | ⭐⭐⭐⭐ (Full text) |

## Configuration

### Adding New Video Platforms

Edit `main.py` to add more platforms to the detection:

```python
video_platforms = [
    'instagram.com', 'facebook.com', 'fb.watch',
    'tiktok.com', 'twitter.com', 'x.com',
    'vimeo.com', 'dailymotion.com', 'twitch.tv',
    'your-platform.com'  # Add here
]
```

### Customizing Scraping

Edit `video_processor.scrape_webpage()` to customize:
- Text extraction depth
- Image handling
- Content filtering

## Error Handling

The system gracefully handles:
- Invalid URLs
- Unsupported formats
- Network failures
- API errors

Each method has fallback mechanisms and returns structured error responses.

## Security Considerations

- URLs are validated before processing
- Scraping uses browser-like headers
- Request timeouts prevent hanging
- Content length limits prevent memory issues
- No execution of scraped scripts

## Future Enhancements

Potential improvements:
- [ ] Download videos from more platforms
- [ ] Extract embedded videos from web pages
- [ ] Process PDF documents
- [ ] Analyze image-only posts
- [ ] Support for live streams

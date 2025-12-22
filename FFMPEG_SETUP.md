# Audio/Caption Extraction Guide

## Overview

The application now uses **multiple methods** to extract audio/captions from videos, with automatic fallback:

1. **YouTube Captions** (Primary) - Downloads subtitles directly from YouTube
2. **MoviePy** (Python-only) - Extracts audio without external dependencies  
3. **FFmpeg** (Optional) - High-quality audio extraction if installed

## Installation

### Quick Start (Python-only, No FFmpeg Required!)

```cmd
pip install moviepy
```

That's it! The application will:
- Download YouTube captions automatically (fastest, most accurate)
- Use moviepy to extract audio from videos (pure Python)
- No external tools needed!

### Optional: FFmpeg (For Higher Quality)

If you want higher quality audio extraction, you can optionally install FFmpeg:

#### Windows
```cmd
choco install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt install ffmpeg
```

## How It Works

### Priority Order

1. **YouTube Captions First**
   - yt-dlp automatically downloads available captions/subtitles
   - Parsed and sent to Gemini as text
   - ✅ Fast, accurate, no processing needed

2. **Audio Extraction (if captions unavailable or as backup)**
   - Tries **moviepy** first (pure Python, no dependencies)
   - Falls back to **ffmpeg** if moviepy fails
   - Extracted audio sent to Gemini for analysis

### What Gets Sent to Gemini?

- **20 Keyframes** - Equally spaced throughout the video
- **Captions** (if available from YouTube) - Full text of subtitles
- **Audio File** (if captions not available) - Complete audio track as MP3

This allows Gemini to perform comprehensive analysis including:
- Visual content analysis
- Audio transcription and claim detection
- Cross-referencing audio/captions with visuals
- Detecting dubbing or audio manipulation

# API Migration: Gemini → OpenAI (Except YouTube)

**Date:** October 2, 2025  
**Purpose:** Switch from Gemini to OpenAI for all content analysis EXCEPT YouTube videos

---

## Migration Overview

### What Changed

**BEFORE:**
- ❌ All content analyzed with Gemini (Gemini 2.5 Pro / Gemini 2.0 Flash)
- ❌ Google Fact Check API used (but always failed validation)
- ❌ Mixed AI model usage

**AFTER:**
- ✅ YouTube videos → **Gemini 2.5 Pro** (native YouTube URL support)
- ✅ All other content → **OpenAI GPT-4o** (better reasoning, no roleplay issues)
- ✅ Google Fact Check API **REMOVED** (didn't work)

---

## Detailed Changes

### 1. **Removed Google Fact Check API**

**Files Modified:**
- `backend/fact_checker.py` - Removed `query_google_fact_check()` function
- `backend/main.py` - Removed all fact check API calls
- `backend/.env` - `FACT_CHECK_API_KEY` no longer used (can be removed)

**Reason:** The Fact Check API was always returning "invalidated" results and wasn't providing useful information.

**Lines Removed from main.py:**
```python
# REMOVED from analyze_youtube_url():
if video_title != "YouTube Video":
    fact_check_result = fact_checker.query_google_fact_check(query_text=video_title)
    if fact_check_result and fact_check_result.get("rating"):
        return { "source": "Google Fact-Check Database", ... }

# REMOVED from analyze_video_platform():
fact_check_result = fact_checker.query_google_fact_check(query_text=video_title)
if fact_check_result and fact_check_result.get("rating"):
    return { "source": "Google Fact-Check Database", ... }

# REMOVED from analyze_webpage():
fact_check_result = fact_checker.query_google_fact_check(query_text=page_title)
if fact_check_result and fact_check_result.get("rating"):
    return { "source": "Google Fact-Check Database", ... }
```

---

### 2. **OpenAI Integration**

**New Dependencies:**
```bash
pip install openai
```

**Environment Variables Required:**
```properties
# .env file
OPEN_AI_API_KEY=sk-proj-...  # Already present
GOOGLE_API_KEY=...            # For YouTube (Gemini)
```

**Code Added to fact_checker.py:**
```python
from openai import OpenAI
import base64

# Configure OpenAI API (for all content except YouTube)
try:
  openai_client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
  logger.info("✅ OpenAI API configured successfully")
except Exception as e:
  openai_client = None

def encode_image_base64(image_path: str) -> str:
  """Encode an image file to base64 string for OpenAI API."""
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
```

---

### 3. **Function-by-Function Conversion**

#### **A. `analyze_with_gemini()` - Non-YouTube Video Analysis**

**Purpose:** Analyzes Instagram, Facebook, TikTok, uploaded videos

**BEFORE (Gemini):**
```python
model = genai.GenerativeModel('gemini-2.5-pro')
# Add images as binary data
content_parts = []
for path in keyframe_paths:
    content_parts.append({"mime_type": "image/jpeg", "data": open(path, "rb").read()})
response = model.generate_content(prompt_parts + content_parts + [instruction])
```

**AFTER (OpenAI GPT-4o):**
```python
# Encode images to base64
messages_content = [{"type": "text", "text": prompt}]
for path in keyframes_to_use[:10]:  # Limit to 10 frames
    base64_image = encode_image_base64(path)
    messages_content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}
    })

response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": messages_content}],
    max_tokens=2000,
    temperature=0.3
)
```

**Why:** OpenAI GPT-4o has vision capabilities and better reasoning without roleplay confusion.

---

#### **B. `analyze_youtube_with_gemini()` - YouTube Videos**

**Purpose:** Analyzes YouTube videos (kept with Gemini)

**STATUS:** ✅ **NO CHANGE** (still uses Gemini 2.5 Pro)

**Reason:** Gemini can process YouTube URLs natively without downloading, OpenAI cannot.

```python
model = genai.GenerativeModel('gemini-2.5-pro')
# YouTube URL sent directly - no download needed
```

---

#### **C. `analyze_webpage_with_gemini()` - Web Articles**

**Purpose:** Analyzes news articles, blog posts, web content

**BEFORE (Gemini):**
```python
model = genai.GenerativeModel('gemini-2.5-pro')
response = model.generate_content(prompt)
```

**AFTER (OpenAI GPT-4o):**
```python
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=2000,
    temperature=0.3
)
```

**Benefit:** Better fact-checking reasoning, less prone to simulation mode.

---

#### **D. `analyze_audio_with_gemini()` - Audio Files**

**Purpose:** Analyzes uploaded audio for misinformation/deepfakes

**BEFORE (Gemini):**
```python
model = genai.GenerativeModel('gemini-2.0-flash-exp')
audio_file = genai.upload_file(audio_path)
response = model.generate_content([prompt, audio_file])
```

**AFTER (OpenAI Whisper + GPT-4o):**
```python
# Step 1: Transcribe audio with Whisper
with open(audio_path, "rb") as audio_file:
    transcript = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

# Step 2: Analyze transcription with GPT-4o
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt_with_transcription}],
    max_tokens=1500,
    temperature=0.3
)
```

**Note:** OpenAI doesn't support direct audio analysis like Gemini, so we transcribe first then analyze text.

---

#### **E. Document & Image Analysis**

**Functions:**
- `analyze_document_with_gemini()` - Text documents (PDF, DOCX, TXT)
- `analyze_image_with_gemini()` - Uploaded images
- `analyze_document_images_with_gemini()` - Scanned PDFs (image-based)

**TODO:** These functions still need conversion to OpenAI. Current status:
- Document text analysis → Should use GPT-4o (text-based)
- Image analysis → Should use GPT-4o Vision (same as video frames)
- Scanned PDFs → Should use GPT-4o Vision (multiple images)

**Conversion Pattern:**
```python
# For text documents:
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)

# For images:
base64_image = encode_image_base64(image_path)
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }]
)
```

---

### 4. **Updated Source Labels in Responses**

**main.py changes:**

```python
# YouTube (Gemini)
return {
    "source": "Vigil AI Analysis (YouTube - Gemini)",
    "url_type": "youtube",
    ...
}

# Video Platforms (OpenAI)
return {
    "source": "Vigil AI Analysis (Video Platform - OpenAI)",
    "url_type": "video_platform",
    ...
}

# Webpages (OpenAI)
return {
    "source": "Vigil AI Analysis (Web Content - OpenAI)",
    "url_type": "webpage",
    ...
}

# Uploaded Videos (OpenAI)
return {
    "source": "Vigil AI Analysis (Uploaded Video - OpenAI)",
    "file_type": "video",
    ...
}

# Uploaded Audio (OpenAI)
return {
    "source": "Vigil AI Analysis (Uploaded Audio - OpenAI)",
    "file_type": "audio",
    ...
}
```

---

## Architecture Summary

### Content Type → AI Model Mapping

| Content Type | AI Model Used | Reason |
|--------------|---------------|--------|
| **YouTube URLs** | Gemini 2.5 Pro | Native YouTube URL support |
| **Instagram/TikTok/Facebook Videos** | OpenAI GPT-4o Vision | Better reasoning, no download issues |
| **Uploaded Videos (MP4, AVI, etc.)** | OpenAI GPT-4o Vision | Consistent with other video analysis |
| **Web Articles/News** | OpenAI GPT-4o | Better fact-checking, no simulation mode |
| **Uploaded Audio Files** | OpenAI Whisper → GPT-4o | Transcribe then analyze |
| **Uploaded Images** | OpenAI GPT-4o Vision (TODO) | Vision analysis needed |
| **Documents (PDF, DOCX)** | OpenAI GPT-4o (TODO) | Text analysis needed |
| **Scanned PDFs** | OpenAI GPT-4o Vision (TODO) | Multi-page image analysis |

---

## Benefits of Migration

### 1. **Better Fact-Checking**
- OpenAI GPT-4o has stronger reasoning capabilities
- Less prone to treating prompts as roleplay/simulation
- More consistent responses

### 2. **Removed Unreliable API**
- Google Fact Check API was always failing
- Simplified codebase by removing unused feature

### 3. **Specialized Models**
- YouTube → Gemini (native support)
- Everything else → OpenAI (better for general analysis)

### 4. **Audio Transcription**
- OpenAI Whisper is industry-standard for transcription
- More accurate than Gemini for audio-to-text

---

## Testing Required

### ✅ Completed Conversions
1. **Non-YouTube Videos** → OpenAI GPT-4o Vision
   - Test: Upload MP4 file, verify analysis
   - Test: Instagram/TikTok URL, verify analysis

2. **Webpages** → OpenAI GPT-4o
   - Test: News article URL, verify fact-checking
   - Re-test: Manchester synagogue article (should work better now)

3. **Audio Files** → OpenAI Whisper + GPT-4o
   - Test: Upload MP3, verify transcription + analysis

### ⚠️ Pending Conversions
4. **Images** → Needs OpenAI GPT-4o Vision conversion
5. **Documents** → Needs OpenAI GPT-4o conversion
6. **Scanned PDFs** → Needs OpenAI GPT-4o Vision conversion

---

## Cost Considerations

### API Costs
- **Gemini (YouTube only):** Moderate cost, only for YouTube
- **OpenAI GPT-4o:** Higher cost but better quality
  - Images: $0.01275/image (low detail mode used to reduce cost)
  - Text: $5/1M input tokens, $15/1M output tokens
  - Whisper: $0.006/minute of audio

### Optimization Tips
1. **Video Analysis:** Limited to 10 keyframes instead of 20 (saves 50% image cost)
2. **Image Detail:** Using `"detail": "low"` for images (faster + cheaper)
3. **Token Limits:** Set `max_tokens` to reasonable limits (2000 for most requests)

---

## Environment Setup

### Required API Keys
```properties
# backend/.env
GOOGLE_API_KEY=your_gemini_api_key_here
OPEN_AI_API_KEY=your_openai_api_key_here

# No longer needed:
# FACT_CHECK_API_KEY=... (removed)
```

### Installation
```bash
cd backend
pip install openai
# Or reinstall all:
pip install -r requirements.txt
```

---

## Files Modified

### Core Files
1. **backend/fact_checker.py**
   - Added OpenAI client configuration
   - Added `encode_image_base64()` helper function
   - Converted `analyze_with_gemini()` to OpenAI GPT-4o Vision
   - Converted `analyze_webpage_with_gemini()` to OpenAI GPT-4o
   - Converted `analyze_audio_with_gemini()` to OpenAI Whisper + GPT-4o
   - Removed `query_google_fact_check()` function
   - Updated file output names (gemini_prompt.txt → openai_prompt.txt, etc.)

2. **backend/main.py**
   - Removed all `query_google_fact_check()` calls
   - Updated source labels to indicate AI model used
   - Updated comments to reflect new architecture

3. **backend/requirements.txt**
   - Added `openai` package

4. **backend/.env**
   - `OPEN_AI_API_KEY` is now used (was already present)
   - `FACT_CHECK_API_KEY` can be removed (no longer used)

### Documentation
5. **API_MIGRATION.md** (this file)
   - Complete migration documentation

---

## Known Issues & Future Work

### Issues
1. ⚠️ Document/Image analysis functions still use Gemini (need conversion)
2. ⚠️ OpenAI package installation partially failed (needs retry or manual install)

### Future Improvements
1. Complete document analysis migration to OpenAI
2. Complete image analysis migration to OpenAI
3. Test cost optimization (reduce image count further if needed)
4. Consider using GPT-4o-mini for cheaper analysis when appropriate
5. Add error handling for API rate limits
6. Implement caching for repeated analyses

---

## Migration Status

**Overall Progress:** 70% Complete

✅ **Completed:**
- Google Fact Check API removal
- OpenAI client configuration
- Video analysis (non-YouTube) → OpenAI
- Webpage analysis → OpenAI
- Audio analysis → OpenAI
- YouTube analysis → Kept with Gemini

⚠️ **Pending:**
- Document analysis → OpenAI (needs conversion)
- Image analysis → OpenAI (needs conversion)
- Scanned PDF analysis → OpenAI (needs conversion)

---

**Next Steps:**
1. Test the converted functions with real content
2. Complete remaining conversions (documents, images)
3. Re-test Manchester synagogue article to verify improved fact-checking
4. Monitor API costs and optimize if needed


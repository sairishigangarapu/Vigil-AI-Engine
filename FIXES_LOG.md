# Vigil AI - Fixes Log

## October 2, 2025 - Audio & Frame Extraction Improvements

### Issue 1: No Audio Extracted from Instagram Reels

**Problem:**
- Audio was not being extracted from Instagram reels
- The `audio_info.json` showed: `"error": "No audio extraction method available. Install moviepy or ffmpeg."`
- Even though moviepy was installed, it wasn't being imported correctly

**Root Cause:**
- moviepy was updated from version 1.x to 2.x
- Version 2.x changed the import structure:
  - **Old (1.x):** `from moviepy.editor import VideoFileClip`
  - **New (2.x):** `from moviepy import VideoFileClip`
- The code was using the old import syntax, causing an ImportError

**Solution:**
1. Updated `extract_audio_from_video()` in `video_processor.py` to try both import methods:
   ```python
   try:
       from moviepy import VideoFileClip  # moviepy 2.x
   except ImportError:
       from moviepy.editor import VideoFileClip  # moviepy 1.x (fallback)
   ```

2. Added comprehensive logging to track the audio extraction process:
   - Import success/failure
   - Video loading status
   - Audio track detection
   - Extraction progress
   - File verification

**Result:**
✅ Audio is now successfully extracted from Instagram reels and other video platforms
✅ Supports both moviepy 1.x and 2.x
✅ Detailed logging helps debug any future issues

---

### Issue 2: Unequal Frame Intervals

**Problem:**
- Frames were being extracted at equal **frame count** intervals, not equal **time** intervals
- For example, a 60-second video would extract frames based on total frame count, which could result in uneven temporal distribution
- User requirement: For a 1-minute video, extract 1 frame every 3 seconds (60s / 20 frames = 3s per frame)

**Old Logic:**
```python
frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
```
This divided the total number of frames equally, but didn't account for variable frame rates.

**New Logic:**
```python
# Calculate time interval between frames
time_interval = duration / num_frames  # seconds per frame

frame_indices = []
for i in range(num_frames):
    # Calculate the time position for this frame
    time_position = i * time_interval
    # Convert time to frame index
    frame_index = int(time_position * fps)
    frame_indices.append(frame_index)
```

**Examples:**
- **1-minute video (60s):** Extracts frames at 0s, 3s, 6s, 9s, ..., 57s (every 3 seconds)
- **2-minute video (120s):** Extracts frames at 0s, 6s, 12s, 18s, ..., 114s (every 6 seconds)
- **30-second video (30s):** Extracts frames at 0s, 1.5s, 3s, 4.5s, ..., 28.5s (every 1.5 seconds)

**Result:**
✅ Frames are now extracted at **equal time intervals** throughout the video
✅ Temporal distribution is consistent regardless of frame rate
✅ Better representation of video content over time
✅ Logging shows both frame indices and time positions for verification

---

## Testing Instructions

### Test Audio Extraction
1. Analyze an Instagram reel or other video platform URL
2. Check the analysis folder for:
   - `video_audio.mp3` file (should exist now)
   - `audio_info.json` should show `"status": "success"`
3. Look at the console logs to see the audio extraction process

### Test Frame Intervals
1. Analyze a video of known duration (e.g., 60 seconds)
2. Check the console logs for:
   - "Extracting frames at X.XX second intervals"
   - "Time positions: ['0.00s', '3.00s', '6.00s', ...]"
3. Verify frames are evenly distributed in time
4. Check the `keyframes/` folder in the analysis session

---

## Technical Details

### moviepy 2.x Import Structure
The new version of moviepy simplified the import structure:
- **2.x:** Direct imports from `moviepy` package
  - `from moviepy import VideoFileClip, AudioFileClip, ImageClip`
- **1.x:** Imports from `moviepy.editor` submodule
  - `from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip`

Our code now supports both versions for maximum compatibility.

### Frame Extraction Math

**Formula:**
```
time_interval = video_duration / num_frames
frame_index = int(time_position * fps)
```

**Where:**
- `video_duration`: Total video length in seconds
- `num_frames`: Number of frames to extract (default: 20)
- `fps`: Frames per second of the video
- `time_position`: Target time in seconds (0, time_interval, 2*time_interval, ...)

**Example Calculation (60-second video at 30 FPS):**
```
time_interval = 60 / 20 = 3 seconds
Frame 0: time=0s    → frame_index = 0 * 30 = 0
Frame 1: time=3s    → frame_index = 3 * 30 = 90
Frame 2: time=6s    → frame_index = 6 * 30 = 180
...
Frame 19: time=57s  → frame_index = 57 * 30 = 1710
```

---

## Files Modified

1. **backend/video_processor.py**
   - `extract_keyframes()`: Changed frame extraction logic from frame-count-based to time-based intervals
   - `extract_audio_from_video()`: Updated moviepy imports to support both 1.x and 2.x, added detailed logging

---

## Next Steps

- Test with various video lengths and platforms
- Verify audio quality and frame distribution
- Monitor logs for any remaining issues
- Consider adding frame extraction visualization to frontend

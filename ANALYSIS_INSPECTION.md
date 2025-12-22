# Analysis Inspection Guide

## Overview
The application now saves all data being sent to the Gemini API in an `analysis/` folder for inspection and debugging purposes.

## Analysis Folder Structure

Each video analysis creates a timestamped session folder:

```
analysis/
└── 20251001_143025_Video_Title_Here/
    ├── README.md                    # Summary of the analysis session
    ├── metadata.json                # Complete video metadata
    ├── gemini_prompt.txt            # Exact prompt sent to Gemini
    ├── gemini_response.json         # Parsed JSON response from Gemini
    ├── gemini_response_raw.txt      # Raw response from Gemini API
    ├── fact_check_result.json       # Google Fact Check result (if found)
    ├── transcription.json           # Audio transcription (when implemented)
    └── keyframes/                   # Extracted video frames
        ├── frame_000_uuid_frame_0.jpg
        ├── frame_001_uuid_frame_1.jpg
        └── ...
```

## File Descriptions

### `README.md`
- Quick overview of the analysis session
- Video information
- List of extracted data

### `metadata.json`
Contains:
- Video title
- Uploader name
- Video description (first 500 chars)
- Local video path

### `gemini_prompt.txt`
- The exact prompt text sent to Gemini API
- Includes instructions and metadata
- Note: Images are sent separately but logged here as "[N images attached]"

### `gemini_response.json`
The structured JSON response from Gemini containing:
- Risk level assessment
- Summary
- Context check results
- Claim verification
- Visual red flags

### `gemini_response_raw.txt`
- Raw unprocessed response from Gemini
- Useful for debugging JSON parsing issues

### `keyframes/`
- All extracted video frames in JPEG format
- Named with sequence numbers for easy inspection
- These are the actual images sent to Gemini API

## Usage

### Inspecting an Analysis
1. Navigate to the `analysis/` folder
2. Find the session folder by timestamp or video title
3. Read `README.md` for an overview
4. Check `gemini_prompt.txt` to see exactly what was sent
5. View `keyframes/` to see the extracted images
6. Compare `gemini_response.json` with the images to verify the analysis

### Debugging
- If Gemini gives unexpected results, check:
  - `gemini_prompt.txt` - Is the prompt correct?
  - `keyframes/` - Are the frames representative?
  - `gemini_response_raw.txt` - Did parsing fail?

### Reproducing Issues
- Share an entire session folder to reproduce analysis results
- Contains everything needed to understand what data was sent to Gemini

## Log Output

Look for these log messages:
```
📁 Created analysis session folder: analysis/20251001_143025_Video_Title
💾 Saving analysis data to: analysis/20251001_143025_Video_Title
   ✅ Saved metadata: metadata.json
   ✅ Copied frame 1: frame_000_uuid_frame_0.jpg
   ✅ Saved Gemini prompt: gemini_prompt.txt
📦 Analysis data saved successfully
```

## Notes

- The `analysis/` folder is gitignored and won't be committed
- Session folders persist after the API request completes
- Temporary files in `temp_media/` are still cleaned up after each request
- You can safely delete old analysis sessions to save disk space

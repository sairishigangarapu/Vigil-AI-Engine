# Prompt De-Simulation Update

## Problem Identified
The prompts used a roleplay/simulation style ("You are 'Vigil AI', a world-class OSINT analyst...") which may have caused Gemini to treat fact-checking as a creative exercise rather than a real task, leading to:
- Ignoring Google Search capability
- Making up conclusions without verification
- Treating instructions as roleplay scenario rather than mandatory requirements

## Solution Implemented
Completely removed all roleplay elements and converted to **direct, imperative task instructions**.

## Before vs. After

### ❌ **OLD STYLE (Roleplay/Simulation):**
```
You are 'Vigil AI', a world-class OSINT analyst with access to real-time 
information through Google Search. Your mission is to investigate web content 
for signs of misinformation...

**CRITICAL INSTRUCTIONS:**
- You MUST use Google Search to verify...
- You are given the video's metadata...
- Perform the following analysis...
```

**Problems:**
- "You are" creates a roleplay scenario
- "Your mission" sounds like a game
- Model may think it's acting/simulating rather than executing

### ✅ **NEW STYLE (Direct Task):**
```
TASK: Perform real-time fact-checking and verification of web content using 
Google Search.

**MANDATORY REQUIREMENTS:**
- Current date: {current_date} - Use this for temporal context
- You MUST use Google Search to verify claims - THIS IS NOT A SIMULATION
- DO NOT make conclusions based solely on training data
- BEFORE stating "no corroboration found", SEARCH GOOGLE for: "{title}"
```

**Improvements:**
- Starts with "TASK:" - clear it's work to do
- "MANDATORY REQUIREMENTS" - not suggestions
- "THIS IS NOT A SIMULATION" - explicit clarification
- Direct imperatives (DO NOT, MUST, SEARCH)

## Changes Applied

### 1. **Webpage Analysis** (`analyze_webpage_with_gemini`)

**Changed:**
- ❌ "You are 'Vigil AI', a world-class OSINT analyst..."
- ✅ "TASK: Perform real-time fact-checking and verification..."

**Key Improvements:**
- Removed all roleplay framing
- Changed "Your mission" → "MANDATORY REQUIREMENTS"
- Changed "You have been provided" → "CONTENT TO ANALYZE"
- Changed "Based on your analysis, generate" → "OUTPUT REQUIRED: Generate"

### 2. **Video Analysis** (`analyze_with_gemini`)

**Changed:**
- ❌ "You are 'Vigil AI', a world-class OSINT video analyst..."
- ✅ "TASK: Perform real-time video content verification..."

**Key Improvements:**
- Removed character/persona completely
- Changed "Your mission is to investigate" → "MANDATORY REQUIREMENTS"
- Changed "You are given" → "Execute these steps with provided video data"
- Changed instructions from suggestions to commands

### 3. **Audio Analysis** (`analyze_audio_with_gemini`)

**Changed:**
- ❌ "You are an expert OSINT analyst specializing in audio forensics..."
- ✅ "TASK: Analyze audio file for authenticity, manipulation..."

**Key Improvements:**
- Removed expert persona framing
- Direct task statement
- "MANDATORY REQUIREMENTS" instead of "CRITICAL INSTRUCTIONS"
- Clearer imperative commands

### 4. **Document Analysis** (`analyze_document_with_gemini`)

**Changed:**
- ❌ "You are an expert OSINT analyst specializing in document analysis..."
- ✅ "TASK: Analyze document for credibility, misinformation..."

**Key Improvements:**
- No roleplay - direct task
- "MANDATORY REQUIREMENTS" over "CRITICAL INSTRUCTIONS"
- Commands instead of suggestions

## Linguistic Changes

### **Command Structure:**

| Old (Roleplay) | New (Imperative) |
|----------------|------------------|
| "You must verify..." | "MUST verify..." |
| "You have been provided with..." | "CONTENT TO ANALYZE:" |
| "Your mission is to investigate..." | "TASK: Perform verification..." |
| "You are given..." | "Execute these steps..." |
| "Based on your analysis, generate..." | "OUTPUT REQUIRED: Generate..." |
| "Provide a comprehensive analysis..." | "Provide analysis in this exact JSON..." |
| "You should search for..." | "Search for..." |
| "It is critical that you..." | "MANDATORY:" |

### **Section Headers:**

| Old | New |
|-----|-----|
| "CRITICAL INSTRUCTIONS" | "MANDATORY REQUIREMENTS" |
| "Your Search Protocol" | "VERIFICATION PROTOCOL - EXECUTE IN ORDER" |
| "Important Reminders" | "CRITICAL NOTES" |
| "You have been provided with content..." | "CONTENT TO ANALYZE:" |
| "Based on your analysis, generate..." | "OUTPUT REQUIRED:" |

### **Tone Shift:**

**Before:**
- Conversational ("You are", "Your mission", "You have been given")
- Suggestive ("You should", "It would be good to")
- Roleplay-oriented ("world-class analyst", "your mission")

**After:**
- Direct and imperative ("MUST", "DO NOT", "EXECUTE")
- Command-oriented ("Search", "Verify", "Check")
- Task-focused ("TASK:", "MANDATORY", "REQUIRED")

## Expected Impact

### **On Gemini's Behavior:**
1. ✅ **Takes task seriously** - Not treating it as creative roleplay
2. ✅ **Executes searches** - Understands it MUST actually search
3. ✅ **Follows protocol** - Treats steps as mandatory, not suggestions
4. ✅ **Provides accurate results** - Real verification, not simulation

### **On Verification Quality:**
- More likely to actually use Google Search capability
- Less likely to "pretend" to search without doing it
- More accurate fact-checking with real sources
- Better distinction between verified and unverified information

### **On False Positives:**
- Should reduce false "debunked" flags on real news
- Will actually search for corroboration before claiming fake
- Better verification of current information (political figures, recent events)
- More nuanced assessments based on real search results

## Technical Details

### Files Modified:
- `backend/fact_checker.py`
  - `analyze_webpage_with_gemini()` - Lines ~295-380
  - `analyze_with_gemini()` - Lines ~66-75
  - `analyze_audio_with_gemini()` - Lines ~465-490
  - `analyze_document_with_gemini()` - Lines ~615-635

### Key Patterns Removed:
```python
# OLD
prompt = f"""You are 'Vigil AI', a world-class OSINT analyst...
Your mission is to investigate...
You have been provided with...
```

### Key Patterns Added:
```python
# NEW
prompt = f"""TASK: Perform real-time fact-checking...
**MANDATORY REQUIREMENTS:**
- MUST use Google Search...
**CONTENT TO ANALYZE:**
**OUTPUT REQUIRED:**
```

## Testing Recommendations

### 1. **Re-test Manchester Article**
The article that was incorrectly flagged as "fabricated" should now:
- Actually search Google for "Manchester synagogue attack"
- Find coverage from BBC, Reuters, Times of India
- Return "Corroborated" status with source list
- Correctly identify Keir Starmer as current PM

### 2. **Test Search Transparency**
Check if response includes:
- `search_performed`: List of actual searches conducted
- `sources_checked`: Which outlets were consulted
- `sources_confirming`: Sources that found the story
- Evidence that real searching was done

### 3. **Compare Behavior**
Old prompts: "No corroboration found" (without searching)
New prompts: Should show actual search results and sources

## Psychological Impact

### Why This Matters:
Large language models are trained to:
- **Roleplay when prompted with "You are..."**
- **Simulate when given personas/missions**
- **Create plausible fiction when in character**

By removing roleplay elements:
- Model treats task as real work, not creative writing
- Commands are interpreted as mandatory, not suggestions
- Search capability used as tool, not roleplay prop

### Analogy:
**Bad:** "You are a chef preparing a meal..." (might describe cooking without doing it)
**Good:** "TASK: Prepare meal. MUST use stove. STEPS: 1. Heat pan..." (actually follows steps)

## Conclusion

The de-simulation update transforms prompts from creative roleplay scenarios into direct, imperative task instructions. This should significantly improve Gemini's:
- **Accuracy** - Real searching instead of simulated searching
- **Reliability** - Follows mandatory steps instead of suggestions
- **Transparency** - Shows actual work done
- **Trustworthiness** - Real verification, not plausible fiction

**This is a critical fix for production fact-checking systems!** 🎯

---

**Status:** ✅ Complete - All prompts updated
**Priority:** CRITICAL - Core functionality improvement
**Testing:** Required - Verify improved search behavior

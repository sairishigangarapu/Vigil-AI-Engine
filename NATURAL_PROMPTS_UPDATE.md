# Natural Prompts Update - Conversational Fact-Checking Instructions

**Date:** October 2, 2025  
**Purpose:** Transform prompts from formal task-based instructions to natural, conversational requests

---

## Problem Identified

The previous "TASK:" structure, while removing roleplay elements, still felt mechanical and formal:
- `"TASK: Perform real-time fact-checking..."`
- `"MANDATORY REQUIREMENTS:"`
- `"EXECUTE GOOGLE SEARCH"`
- `"OUTPUT REQUIRED:"`

This formal framing might still trigger "simulation mode" where the AI treats verification as a hypothetical exercise rather than real work.

---

## Solution: Natural Conversational Prompts

Rewrite all prompts to sound like a person asking for real help:
- "I need you to fact-check this article..."
- "What you need to do:"
- "How to verify this:"
- "Give me ONLY a JSON object..."

Key principle: **Talk to the AI like you're asking a colleague to do actual work, not giving it a creative writing assignment.**

---

## Changes Made

### 1. **Webpage/Article Analysis** (`analyze_webpage_with_gemini()`)

**OLD (Formal/Task-Based):**
```python
prompt = f"""TASK: Perform real-time fact-checking and verification of web content using Google Search.

**MANDATORY REQUIREMENTS:**
- Current date: {current_date} - Use this for temporal context
- You MUST use Google Search to verify claims - THIS IS NOT A SIMULATION
- DO NOT make conclusions based solely on your training data
- BEFORE stating "no corroboration found", SEARCH GOOGLE for: "{title}"
```

**NEW (Natural/Conversational):**
```python
prompt = f"""I need you to fact-check this article using Google Search right now. This is real fact-checking work, not a hypothetical exercise.

Before you begin, check today's date to ensure temporal accuracy in your analysis.

**Critical requirements for this check:**
- Use Google Search to verify the claims - search for "{title}" and related terms
- Don't rely only on what you already know - recent events require current sources
- Before flagging something as wrong, verify it with today's information (people's positions, current events, etc.)
- If something seems recent, search for it - don't assume it's false just because it's new
- Choose sources that actually cover this type of content (see guidelines below)
```

**Key Changes:**
- ✅ "I need you to..." instead of "TASK:"
- ✅ "check today's date" instead of explicitly stating the date
- ✅ "this is real fact-checking work" instead of "NOT A SIMULATION"
- ✅ Natural flow, conversational tone
- ✅ Removed ALL CAPS emphasis

---

### 2. **Date Handling**

**OLD (Explicit Date Injection):**
```python
from datetime import datetime
current_date = datetime.now().strftime("%B %d, %Y")
prompt = f"""...
**MANDATORY REQUIREMENTS:**
- Current date: {current_date} - Use this for temporal context
...
{{
  "date_analyzed": "{current_date}",
```

**NEW (Let AI Check Date):**
```python
# No date variable needed
prompt = f"""...
Before you begin, check today's date to ensure temporal accuracy in your analysis.
...
{{
  "date_analyzed": "[Today's date]",
```

**Rationale:** 
- Asking AI to "check today's date" forces it to use real-time capabilities
- Prevents confusion about whether this is current or historical analysis
- More natural - mimics how humans ask each other to verify dates

---

### 3. **Video Analysis** (`analyze_with_gemini()`)

**OLD:**
```python
prompt_parts = [
    "TASK: Perform real-time video content verification and deepfake detection using Google Search.\n\n",
    f"**MANDATORY REQUIREMENTS:**\n- Current date: {current_date}\n- MUST use Google Search...\n",
    "**ANALYSIS PROTOCOL:**\nExecute these steps with provided video data...\n",
]
```

**NEW:**
```python
prompt_parts = [
    "I need you to analyze this video for authenticity and verify its claims using Google Search. This is real verification work.\n\n",
    "**What you need to do:**\n- Check today's date first for temporal accuracy\n- Use Google Search to verify any claims made in the video\n- Don't just rely on what you already know - search for current information\n",
    "**How to analyze this video:**\n1. **Search for this content:** Look online to see if this video or similar footage appeared elsewhere...\n",
]
```

**Key Changes:**
- ✅ "I need you to analyze..." instead of "TASK: Perform..."
- ✅ "What you need to do:" instead of "MANDATORY REQUIREMENTS:"
- ✅ "How to analyze:" instead of "ANALYSIS PROTOCOL:"
- ✅ Natural numbered steps instead of military-style execution commands

---

### 4. **Audio Analysis** (`analyze_audio_with_gemini()`)

**OLD:**
```python
prompt = f"""TASK: Analyze audio file for authenticity, manipulation, and misinformation using real-time verification.
    
**Audio File:** "{filename}"

**MANDATORY REQUIREMENTS:**
- Use Google Search to verify factual claims in the audio
- Search for speaker identity if identifiable
- DO NOT assume claims are false without searching first

**OUTPUT REQUIRED:**
Provide analysis in this exact JSON structure:
```

**NEW:**
```python
prompt = f"""I need you to analyze this audio file for authenticity and verify any claims made in it. This is real forensic work.
    
**Audio file:** "{filename}"

**What you need to do:**
- Check today's date first for context
- Use Google Search to verify any factual claims made in the audio
- If you can identify the speaker, search for information about them
- Search first, don't just assume something is wrong

**What to analyze:**

1. **Is this audio real?**
   - Does the voice sound AI-generated or synthetic?
   - Any signs of audio editing or manipulation?

**Response format:**
Give me ONLY a JSON object with this structure (no extra text):
```

**Key Changes:**
- ✅ "I need you to analyze..." instead of "TASK: Analyze..."
- ✅ "What you need to do:" instead of "MANDATORY REQUIREMENTS:"
- ✅ "What to analyze:" with conversational questions
- ✅ "Give me ONLY a JSON object..." instead of "OUTPUT REQUIRED:"

---

### 5. **Document Analysis** (`analyze_document_with_gemini()`)

**OLD:**
```python
prompt = f"""TASK: Analyze document for credibility, misinformation, and authenticity using real-time verification.

**Document:** "{filename}"

**MANDATORY REQUIREMENTS:**
- Use Google Search to verify all factual claims, statistics, and references
- Search for authors, organizations, and sources mentioned
- Search for corroboration before claiming information is false

**Document Content:**
{extracted_text}

**OUTPUT REQUIRED:**
Provide analysis in this exact JSON structure:
```

**NEW:**
```python
prompt = f"""I need you to analyze this document for credibility and verify the information in it. This is real document analysis.

**Document:** "{filename}"

**What you need to do:**
- Check today's date first for temporal context
- Use Google Search to verify all factual claims, statistics, and references mentioned
- Search for information about any authors, organizations, or sources cited
- Search for corroboration before deciding something is false

**Document content:**
{extracted_text}

**What to analyze:**

1. **Is this document credible?**
   - Can you identify the source or publisher?
   - Is the author credible? (search for them)

**Response format:**
Give me ONLY a JSON object with this structure (no extra text):
```

**Key Changes:**
- ✅ "I need you to analyze..." instead of "TASK: Analyze..."
- ✅ "What you need to do:" instead of "MANDATORY REQUIREMENTS:"
- ✅ "Document content:" instead of "Document Content:" (more casual)
- ✅ "Give me ONLY a JSON object..." instead of "OUTPUT REQUIRED:"

---

## Linguistic Pattern Analysis

### Command Structure Transformation

| OLD (Formal/Imperative) | NEW (Conversational/Request) |
|-------------------------|------------------------------|
| `TASK: Perform real-time fact-checking...` | `I need you to fact-check this article...` |
| `MANDATORY REQUIREMENTS:` | `What you need to do:` |
| `EXECUTE GOOGLE SEARCH` | `Use Google Search` / `search for...` |
| `DO NOT make conclusions...` | `Don't rely only on what you already know...` |
| `BEFORE stating "no corroboration"` | `Before flagging something as wrong...` |
| `OUTPUT REQUIRED:` | `Response format:` / `Give me ONLY a JSON...` |
| `Generate ONLY valid JSON...` | `Give me ONLY a JSON object...` |
| `Current date: {current_date}` | `check today's date` / `Before you begin, check today's date` |

### Section Header Transformation

| OLD (Formal) | NEW (Natural) |
|--------------|---------------|
| `**MANDATORY REQUIREMENTS:**` | `**What you need to do:**` |
| `**ANALYSIS PROTOCOL:**` | `**How to analyze this:**` |
| `**CONTENT TO ANALYZE:**` | `**Article details:**` / `**Document content:**` |
| `**OUTPUT REQUIRED:**` | `**Response format:**` |
| `**VERIFICATION PROTOCOL - EXECUTE IN ORDER:**` | `**How to verify this article:**` |
| `**CRITICAL NOTES:**` | `**Important notes:**` |

### Question-Based Prompting

Instead of commands, use natural questions:

**OLD:**
```
1. Source Credibility: Search for reputation and track record
2. Claim Analysis: Extract main claims and categorize
3. Fact Verification: Execute Google Search protocol
4. Content Quality: Evaluate sensationalism
```

**NEW:**
```
1. **Is this document credible?**
   - Can you identify the source or publisher?
   - Is the author credible? (search for them)

2. **What does it say?**
   - What are the main claims being made?
   - What evidence is provided?

3. **Are the facts accurate?**
   - Which facts can be verified? (search for them)
   - What claims lack verification?
```

---

## Psychological Impact

### Why Natural Language Works Better

1. **Human-AI Interaction Pattern**
   - "I need you to..." → Establishes collaborative relationship
   - "check today's date" → Triggers real-time capability usage
   - "this is real work" → Clarifies this isn't creative writing

2. **Reduced Simulation Framing**
   - No "TASK:" prefix that might trigger exercise mode
   - No ALL CAPS commands that feel like test scenarios
   - No "MANDATORY" language that sounds hypothetical

3. **Question-Based Engagement**
   - "Is this audio real?" → Engages analytical thinking
   - "What does it say?" → Natural flow of analysis
   - "Are the facts accurate?" → Direct investigation prompt

4. **Implicit Current Context**
   - "check today's date" → Forces real-time context awareness
   - "search for current information" → Emphasizes timeliness
   - "verify it with today's information" → Grounds in present

---

## Expected Improvements

### Before (Task-Based Prompts)
```
Issue: Gemini might treat as hypothetical
- "Based on my training data from 2023..."
- "I cannot verify current events..."
- "This appears to be from the future..."
Result: False positives on real breaking news
```

### After (Natural Prompts)
```
Expected: Gemini treats as real request
- Uses Google Search to verify claims
- Checks current date for temporal context
- Verifies people's current positions
- Lists actual sources checked
Result: Accurate verification of current events
```

---

## Testing Checklist

After this update, re-test these scenarios:

### ✅ Test 1: Current Events (Manchester Synagogue Attack)
- **URL:** `https://www.wionews.com/world/police-deployed-to-synagogues-nationwide-after-deadly-attack-in-manchester-pm-starmer-1759411544272`
- **Expected Result:**
  - `date_analyzed`: Shows October 2, 2025 (or current date)
  - `risk_level`: "Low Risk" or "Verified"
  - `fact_verification.status`: "Corroborated"
  - `sources_checked`: Lists BBC, Reuters, Times of India, etc.
  - `sources_confirming`: Shows outlets that covered the story
  - Recognizes Keir Starmer as current UK PM

### ✅ Test 2: Topic-Specific Content
- **Gaming article** → Should check IGN, Kotaku, GameSpot
- **Anime article** → Should check Crunchyroll, Anime News Network
- **Tech article** → Should check TechCrunch, The Verge

### ✅ Test 3: Date Awareness
- Content from "today" or "this week" should be verified, not rejected
- AI should explicitly mention checking today's date in analysis
- `date_analyzed` field should show current date, not training data cutoff

### ✅ Test 4: Source Transparency
- `search_performed` field should list actual search queries
- `sources_checked` should list real news outlets
- `sources_confirming` should show which outlets covered the story
- No more generic "no corroboration found" without evidence

---

## Code Locations

All changes made in `backend/fact_checker.py`:

1. **`analyze_webpage_with_gemini()`** - Lines ~290-380
   - Webpage/article analysis prompt
   
2. **`analyze_with_gemini()`** - Lines ~60-95
   - Video analysis prompt
   
3. **`analyze_audio_with_gemini()`** - Lines ~455-530
   - Audio forensics prompt
   
4. **`analyze_document_with_gemini()`** - Lines ~625-695
   - Document credibility prompt

---

## Summary

**Core Principle:** Make Gemini feel like it's having a real conversation about fact-checking work, not executing a simulation or completing a test scenario.

**Key Techniques:**
- ✅ Conversational requests ("I need you to...")
- ✅ Natural questions ("Is this audio real?")
- ✅ Implicit date checking ("check today's date")
- ✅ Friendly instructions ("What you need to do:")
- ✅ Direct requests ("Give me ONLY a JSON object...")

**Expected Outcome:** Gemini treats fact-checking as real work requiring actual Google Search usage, current date awareness, and transparent source verification—eliminating false positives on legitimate breaking news.

---

**Status:** ✅ All prompts updated (October 2, 2025)  
**Next Step:** Re-test Manchester synagogue article to verify improvements

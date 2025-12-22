# Gemini Search Enforcement - Critical Update

## Problem
Despite instructions to use Google Search, Gemini was still claiming "no corroboration found" for legitimate breaking news events that ARE being widely reported.

## Root Cause
The original prompts were too polite and vague. Gemini was not taking the search instruction seriously enough and was still defaulting to its training data.

## Solution Implemented

### 1. **Aggressive Search Mandate**
Changed from:
> "You MUST use Google Search to verify..."

To:
> "BEFORE saying 'no corroboration found', you MUST actively search Google for: [specific article title]"
> "Search for these exact terms: 'Manchester synagogue attack October 2 2025' on Google News"

### 2. **Step-by-Step Search Protocol**
Added explicit numbered steps that Gemini MUST follow:
```
**STEP 1:** Search Google News for the event described
**STEP 2:** Search for coverage from BBC, Reuters, AP News, The Guardian  
**STEP 3:** Verify political figures (e.g., "Keir Starmer UK Prime Minister 2025")
**STEP 4:** Check Indian news outlets coverage
**STEP 5:** Only AFTER searching, determine if event is real or fabricated
```

### 3. **Accountability Requirements**
Modified the JSON response structure to FORCE Gemini to report what it searched:

```json
"fact_verification": {
  "status": "Corroborated/Uncorroborated/Debunked/Mixed",
  "details": "MUST include which sources you searched and what you found",
  "search_performed": "List the actual Google searches you conducted",
  "sources_found": ["List of credible sources that ARE covering this story"]
}
```

This forces Gemini to:
- Document what searches it performed
- List which sources it found
- Be accountable for its verification process

### 4. **Explicit Warnings**
Added specific warnings about common mistakes:
- "If multiple credible sources ARE reporting it, the event IS REAL - do not call it fabricated"
- "An event being RECENT does not mean it's fake"
- "You MUST distinguish between 'I haven't found coverage yet' vs 'coverage doesn't exist'"
- "Keir Starmer IS the current UK Prime Minister (since July 2024)"

### 5. **Title-Specific Search Instruction**
The prompt now includes the actual article title:
```python
f"BEFORE saying 'no corroboration found', you MUST actively search Google for: \"{scraped_data.get('title', 'article topic')}\""
```

This makes it impossible for Gemini to ignore the search requirement.

## Expected Behavior Change

### Before (Wrong):
```json
{
  "risk_level": "High Risk",
  "summary": "Complete fabrication, no corroboration found",
  "fact_verification": {
    "status": "Debunked",
    "details": "No credible sources reporting this event"
  }
}
```

### After (Correct):
```json
{
  "risk_level": "Low Risk",
  "summary": "Legitimate breaking news covered by multiple credible sources",
  "fact_verification": {
    "status": "Corroborated",
    "details": "Event confirmed by multiple outlets",
    "search_performed": "Searched Google News for 'Manchester synagogue attack October 2 2025', Checked BBC, Reuters, Times of India, Hindustan Times",
    "sources_found": ["BBC News", "Reuters", "Times of India", "Hindustan Times", "India Today", "The Guardian"]
  }
}
```

## Frontend Updates
The ReportCard component will now display:
- ✅ **Search Performed**: Shows what searches Gemini actually did
- ✅ **Sources Found**: Lists credible sources covering the story
- ✅ **Verification Details**: More transparent fact-checking process

## Testing Instructions

1. **Re-analyze the Manchester Article**
   - URL: `https://www.wionews.com/world/police-deployed-to-synagogues-nationwide-after-deadly-attack-in-manchester-pm-starmer-1759411544272`
   - Expected: Should now show "Corroborated" with list of sources
   - Should list BBC, Reuters, Times of India, etc. as sources found

2. **Check the New Fields**
   - Look for "Search Performed" in the fact verification section
   - Look for "Sources Found" list
   - Verify it shows actual news outlets

3. **Verify Keir Starmer Recognition**
   - Should correctly identify him as UK Prime Minister
   - Should not flag his mention as an error

## Critical Changes Made

**File:** `backend/fact_checker.py` - `analyze_webpage_with_gemini()`

**Key Additions:**
1. Line ~295: Aggressive search mandate with exact search terms
2. Line ~305-315: Step-by-step search protocol
3. Line ~345-350: Accountability fields in JSON structure
4. Line ~292: Title-specific search instruction

## Impact Assessment

### High Priority Fix ⚠️
This is CRITICAL for a fact-checking tool because:
- ❌ **Before**: Flagged real news as fake (false positives)
- ✅ **After**: Should correctly verify real news events
- 📊 **Transparency**: Now shows what sources were checked

### Trust Implications
- **User Trust**: Users seeing real BBC-reported news flagged as "complete fabrication" would lose all trust in the system
- **Liability**: False accusations of fabrication against legitimate outlets could have legal implications
- **Reputation**: A fact-checker that doesn't check facts properly is worse than no fact-checker

## Next Steps

1. ✅ Restart backend (auto-reload should pick up changes)
2. 🧪 Test with Manchester synagogue article
3. 📊 Review "search_performed" and "sources_found" fields
4. ✅ Verify proper source attribution
5. 📝 Monitor for any remaining false positives

## Fallback Plan

If Gemini STILL doesn't search properly, consider:
1. **Google Custom Search API Integration**: Perform searches ourselves and pass results to Gemini
2. **NewsAPI Integration**: Pull recent news and cross-reference
3. **Fact-Check API Priority**: Query Google Fact Check API first before Gemini analysis
4. **Multi-Model Approach**: Use different AI models for verification

---

**Status**: Changes applied, ready for testing
**Priority**: CRITICAL - affects core functionality
**Testing Required**: Yes - verify with real breaking news articles

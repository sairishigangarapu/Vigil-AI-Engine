# Real-Time Search Integration for Fact-Checking

**Date:** December 2024  
**Status:** ✅ IMPLEMENTED  
**Update:** Now uses ACTUAL Google Custom Search API instead of asking Gemini to search

## Evolution of the Approach

### Version 1: Relying on Training Data
- ❌ Gemini used only knowledge cutoff (before July 2024)
- ❌ Couldn't verify recent events
- ❌ Flagged legitimate breaking news as fake

### Version 2: Asking Gemini to Search
- ⚠️ Asked Gemini to "use Google Search"
- ⚠️ Gemini hallucinated search results
- ⚠️ Still unreliable for verification

### Version 3: ACTUAL Google Search API (Current)
- ✅ Performs real Google Custom Search API calls
- ✅ Provides actual search results to Gemini
- ✅ Evidence-based, verifiable fact-checking

## The Core Problem

AI models (including Gemini) **cannot actually search Google in real-time**. When you ask them to "search Google and verify," they:

1. **Hallucinate search results** - Make up what they think Google would return
2. **Use outdated knowledge** - Rely on training data cutoff
3. **Can't verify recent news** - Don't have access to today's headlines

**Example from your system:**
```
Article (Oct 3, 2025): "Morocco protest: PM calls for dialogue"
Gemini claimed: "I searched Google and found this story on BBC, Reuters..."
Reality: Gemini DIDN'T search - it hallucinated those sources
Result: Story was actually fabricated, no search results exist
```

## The Solution: Real Search Integration

### New Architecture

```
┌─────────────────┐
│  Article Title  │
│   "Morocco..."  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Google Custom Search    │  ← ACTUAL API CALL
│ API: Real-time search   │     (backend/fact_checker.py)
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Real Search Results:    │
│  1. (no results found)   │  ← REAL DATA from Google
│  OR                      │
│  1. BBC: Different story │
│  2. Reuters: Unrelated   │
└────────┬─────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Gemini Analysis:           │
│  "I've reviewed the actual  │
│  Google search results you  │  ← EVIDENCE-BASED
│  provided. NONE of the 10   │
│  results match this story.  │
│  Status: Debunked"          │
└─────────────────────────────┘
```

## Implementation Details

### New Function: `search_google_news()`

**Location:** `backend/fact_checker.py` (lines 22-76)

**What it does:**
```python
def search_google_news(query: str, num_results: int = 10) -> list:
    """
    Performs ACTUAL Google search via Custom Search JSON API.
    Returns real results with title, snippet, source, link.
    """
    # Makes real HTTP request to Google
    # Returns: [{"title": "...", "snippet": "...", "source": "..."}]
    # Or: [] if nothing found (important data!)
```

**Returns:**
- List of actual search results from Google's index
- Empty list `[]` if nothing found (**this is valuable evidence!**)
- Each result includes: title, snippet, source domain, full URL, date

### Updated: `analyze_webpage_with_gemini()`

**Location:** `backend/fact_checker.py` (lines 294-483)

**Changes:**

**1. Performs Real Search:**
```python
# Lines 315-325
search_results = search_google_news(title_query, num_results=10)

# Fallback if no results
if not search_results and len(title_query.split()) > 3:
    keywords = ' '.join([w for w in title_query.split() if len(w) > 4][:5])
    search_results = search_google_news(keywords, num_results=10)
```

**2. Formats Results for Gemini:**
```python
# Lines 327-345
if search_results:
    search_results_text = "\n**ACTUAL GOOGLE NEWS SEARCH RESULTS:**\n"
    for idx, result in enumerate(search_results, 1):
        search_results_text += f"{idx}. **{result['title']}**\n"
        search_results_text += f"   Source: {result['source']}\n"
        search_results_text += f"   Snippet: {result['snippet']}\n"
else:
    search_results_text = "⚠️ NO RESULTS FOUND\n"
```

**3. Instructs Gemini to Compare:**
```python
# Lines 347-352
prompt = f"""I need you to fact-check this article by comparing it 
against REAL Google News search results that I've provided below.

Don't pretend to search - I've already done the search for you.
Just analyze what I've provided.

{search_results_text}

Compare the article against these search results...
"""
```

**4. Saves Everything:**
```python
# Lines 436-444
# Saves: google_search_results.json
{
  "query": "Morocco protest GenZ 212",
  "num_results": 0,
  "search_date": "2024-12-08T14:30:00",
  "results": []
}
```

## What Gets Saved

### New Analysis Session Structure

```
analysis/20241208_143052_Morocco_protest/
├── scraped_content.json           # Original article text
├── google_search_results.json     # ✨ NEW: Real search results
├── gemini_prompt.txt              # Prompt WITH search results
├── gemini_response.json           # Gemini's comparison
├── gemini_response_raw.txt        # Raw response
└── metadata.json                  # Session info
```

### Example: google_search_results.json

**When NO results found (fabricated story):**
```json
{
  "query": "Morocco protest GenZ 212 police open fire",
  "num_results": 0,
  "search_date": "2024-12-08T14:30:15.123456",
  "results": []
}
```

**When results found (real story):**
```json
{
  "query": "Manchester synagogue attack",
  "num_results": 8,
  "search_date": "2024-12-08T14:30:15.123456",
  "results": [
    {
      "title": "Manchester synagogue attacker sentenced...",
      "snippet": "A man who attacked a Jewish community...",
      "source": "bbc.com",
      "link": "https://www.bbc.com/...",
      "date": "2024-10-02"
    }
  ]
}
```

## API Setup Required

### Google Custom Search API

**Prerequisites:**
1. Google Cloud account (free tier available)
2. Custom Search Engine created
3. Custom Search API enabled

**Environment Variables:**
```env
# .env file
GOOGLE_API_KEY=your_existing_gemini_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Quota:**
- **Free tier:** 100 searches/day (sufficient for most use)
- **Paid tier:** $5 per 1,000 additional queries

**Setup Guide:** See `GOOGLE_SEARCH_SETUP.md` for detailed instructions

## Testing

### Test Script: `backend/test_search.py`

**Run:**
```bash
python backend/test_search.py
```

**Expected Output:**
```
✅ Search successful! Found 5 results:

1. Morocco announces economic reforms
   Source: reuters.com
   Snippet: Morocco's government unveiled...
   
2. Moroccan football team advances
   Source: bbc.com
   Snippet: Morocco's national team...
```

### Integration Test

```bash
# Restart backend
python backend/main.py

# Analyze a news article
# Check: backend/analysis/[session]/google_search_results.json
```

## Example Comparison

### Scenario: Fabricated Morocco Protest Article

**Article Claims:**
- "3 people died in Leqliaa, Morocco"
- "Police opened fire on protesters"
- "GenZ 212 protest group leading demonstrations"
- "Date: October 3, 2025"

**Google Search Results:** (ACTUAL API RESPONSE)
```json
{
  "num_results": 0,
  "results": []
}
```

**Gemini's Analysis (Evidence-Based):**
```json
{
  "date_analyzed": "2024-12-08",
  "risk_level": "High Risk",
  "summary": "Google search found ZERO results for this story. No credible sources reporting these events.",
  "fact_verification": {
    "status": "Debunked",
    "details": "Searched Google for 'Morocco protest GenZ 212' - 0 results found. No coverage from BBC, Reuters, AP, Al Jazeera, or any other outlet. The complete absence of search results is strong evidence this story is fabricated.",
    "search_results_found": 0,
    "sources_confirming": [],
    "sources_denying": ["Complete absence from all news outlets"]
  }
}
```

## Benefits

### 1. No Hallucination
✅ Gemini cannot make up search results  
✅ All claims backed by real Google data  
✅ "No results" is definitive evidence  

### 2. Verifiable
✅ Search results saved for human inspection  
✅ Transparent verification process  
✅ You can check what Google actually returned  

### 3. Accurate for Recent Events
✅ Real-time data from Google's index  
✅ Catches fabricated "breaking news"  
✅ Temporal verification (article date vs search results)  

### 4. Evidence-Based Decisions
```
Search Results | Risk Assessment
---------------|----------------
0 results      | High Risk (likely fabricated)
Different      | Medium Risk (context mismatch)
Matching       | Low Risk/Verified
```

## Performance

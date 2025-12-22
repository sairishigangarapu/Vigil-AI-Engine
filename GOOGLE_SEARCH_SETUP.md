# Google Custom Search API Setup

**Date:** December 2024  
**Purpose:** Enable real-time Google News searches for fact-checking

## Overview

The fact-checking system now performs **actual Google searches** and provides the results to Gemini for comparison against articles. This ensures Gemini doesn't hallucinate search results - it compares real data.

## How It Works

### Old Approach (Didn't Work)
```
Article → Gemini (asked to "search Google") → Hallucinated results → Wrong analysis
```

### New Approach (Works!)
```
Article → Google Custom Search API → Real search results → Gemini compares → Accurate analysis
```

## Setup Instructions

### Step 1: Create Google Custom Search Engine

1. **Go to Google Programmable Search Engine:**
   - Visit: https://programmablesearchengine.google.com/

2. **Create a new search engine:**
   - Click "Add" or "Create"
   - Name: "Vigil Fact Checker"
   - What to search: "Search the entire web"
   - Click "Create"

3. **Get your Search Engine ID:**
   - After creation, click on your search engine
   - Click "Setup" or "Edit"
   - Find "Search engine ID" (looks like: `0123456789abcdefg:hijklmnop`)
   - Copy this ID

4. **Enable "Search the entire web":**
   - In setup, make sure "Search the entire web" is enabled
   - This allows searching all news sources, not just specific sites

### Step 2: Enable Custom Search API

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/

2. **Enable the API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Custom Search API"
   - Click "Enable"

3. **Your API Key:**
   - You're already using `GOOGLE_API_KEY` for Gemini
   - The same key works for Custom Search API
   - No new key needed!

### Step 3: Add to Environment Variables

Add this to your `.env` file:

```env
# Google Custom Search API (for fact-checking)
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Your existing `.env` should now have:**
```env
# Gemini API
GOOGLE_API_KEY=your_existing_gemini_api_key

# Google Custom Search API
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

## Usage Limits & Pricing

### Free Tier
- **100 queries per day** - FREE
- Perfect for testing and moderate use

### Paid Tier (if needed)
- First 100 queries/day: FREE
- Additional queries: $5 per 1000 queries
- Max: 10,000 queries per day

**For your use case:** Free tier should be sufficient unless you're processing hundreds of articles daily.

## Testing the Setup

### Method 1: Python Test Script

Create `backend/test_search.py`:

```python
import os
from dotenv import load_dotenv
from fact_checker import search_google_news

load_dotenv()

# Test search
results = search_google_news("Morocco protest", num_results=5)

if results:
    print(f"✅ Search successful! Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   Source: {result['source']}")
        print(f"   Snippet: {result['snippet'][:100]}...")
        print()
else:
    print("❌ No results found. Check your API configuration.")
```

Run it:
```bash
python backend/test_search.py
```

### Method 2: Direct API Test

```bash
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_SEARCH_ENGINE_ID&q=test"
```

## What Gets Saved

When analyzing a webpage, the system now saves:

```
analysis/[session_folder]/
├── scraped_content.json        # Original article
├── google_search_results.json  # Real Google search results ✨ NEW
├── gemini_prompt.txt           # Prompt with search results
├── gemini_response.json        # Gemini's comparison
└── gemini_response_raw.txt     # Raw response
```

## Example Search Results Format

```json
{
  "query": "Morocco protest GenZ 212",
  "num_results": 0,
  "search_date": "2024-12-08T14:23:15",
  "results": []
}
```

If NO results are found, that's powerful evidence the story is fabricated!

## How Gemini Uses Search Results

### Before (Hallucination Risk):
```
Prompt: "Search Google for 'Morocco protest'"
Gemini: "I found articles from BBC and Reuters..." (made up)
```

### After (Real Data):
```
Prompt: "Here are ACTUAL search results:
1. BBC News - Different story
2. Reuters - No mention of Morocco protest
3. Al Jazeera - Unrelated topic

Compare the article against these results."

Gemini: "The article claims X, but NONE of the search results 
mention this event. Result: Debunked."
```

## Troubleshooting

### Error: "Search results: []"

**Possible causes:**
1. `GOOGLE_SEARCH_ENGINE_ID` not set in `.env`
2. Search Engine ID is wrong
3. Custom Search API not enabled
4. API quota exceeded (100/day free limit)

**Fix:**
- Check `.env` file has the correct ID
- Verify API is enabled in Google Cloud Console
- Check quota: https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas

### Error: "Invalid API key"

**Fix:**
- Make sure `GOOGLE_API_KEY` in `.env` is correct
- Same key works for both Gemini and Custom Search

### Error: "Daily quota exceeded"

**Fix:**
- Free tier = 100 searches/day
- Wait until tomorrow, or upgrade to paid tier
- Consider caching search results for repeated queries

## Benefits of This Approach

✅ **No Hallucination:** Gemini can't make up search results - we give it real data  
✅ **Verifiable:** All search results saved in analysis session for inspection  
✅ **Accurate:** Compares actual news coverage against article claims  
✅ **Transparent:** You can see exactly what Google found (or didn't find)  
✅ **Evidence-Based:** "NO results found" is strong evidence of fabrication  

## Future Enhancements

### Potential Improvements:
1. **Cache search results** to reduce API calls
2. **Search multiple queries** (title + key claims)
3. **Date filtering** (only recent news)
4. **Source filtering** (prioritize BBC, Reuters, AP)
5. **Similarity scoring** between article and search results

### Alternative APIs (if needed):
- **NewsAPI** - 100 requests/day free, news-focused
- **SerpAPI** - Google search scraping, 100 searches/month free
- **Bing News Search API** - Microsoft alternative

## Cost Estimate

**Typical usage:**
- 50 article fact-checks per day
- 1 search per article
- **Cost: $0/month** (within free tier)

**Heavy usage:**
- 500 article fact-checks per day
- 2 searches per article (title + claims)
- 1000 searches/day = 900 paid queries
- **Cost: $4.50/month**

## Related Documentation

- **OPENAI_REVERSION.md** - Why we use Gemini only
- **NATURAL_PROMPTS_UPDATE.md** - Prompt engineering approach
- **API.md** - General API documentation

## Conclusion

This setup enables **real fact-checking with actual search results**. Instead of asking Gemini to hallucinate what Google might say, we give it real Google News data to compare against articles.

**Result:** More accurate, verifiable, evidence-based fact-checking! 🎯

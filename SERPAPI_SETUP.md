# SerpAPI Setup Guide

**Date:** December 2024  
**Purpose:** Enable real-time Google Search with AI Overview for fact-checking

## Why SerpAPI?

SerpAPI is **better than Google Custom Search API** for our use case:

| Feature | SerpAPI | Google Custom Search |
|---------|---------|---------------------|
| **AI Overview** | ✅ Included | ❌ Not available |
| **Organic Results** | ✅ Full access | ✅ Limited |
| **News Results** | ✅ Dedicated endpoint | ⚠️ Requires config |
| **Free Tier** | 100 searches/month | 100 searches/day |
| **Setup Complexity** | Simple (just API key) | Complex (engine + API) |
| **Result Quality** | High (real SERP data) | Lower |
| **Pricing** | $50/5000 searches | $5/1000 searches |

**For this project:** SerpAPI gives you Google's AI Overview, which is valuable for fact-checking!

## Setup Instructions

### Step 1: Create SerpAPI Account

1. **Visit SerpAPI:**
   - Go to: https://serpapi.com/

2. **Sign Up (Free):**
   - Click "Sign Up" or "Get Started"
   - Use email or Google account
   - **No credit card required** for free tier

3. **Verify Email:**
   - Check your email for verification link
   - Click to verify

### Step 2: Get Your API Key

1. **Go to Dashboard:**
   - After login: https://serpapi.com/dashboard

2. **Copy Your API Key:**
   - You'll see "Your Secret API Key"
   - Looks like: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t`
   - Click "Copy" button

3. **Check Your Quota:**
   - Free tier: **100 searches per month**
   - Resets on the 1st of each month
   - Enough for testing and moderate use

### Step 3: Add to Environment Variables

Open `backend/.env` and add:

```env
# SerpAPI (for Google Search with AI Overview)
SERPAPI_KEY=your_serpapi_key_here
```

**Complete `.env` file should look like:**
```env
# Gemini API
GOOGLE_API_KEY=your_existing_gemini_key

# SerpAPI
SERPAPI_KEY=your_serpapi_key_here
```

### Step 4: Install Dependencies (if needed)

The code only uses `requests` which is already in `requirements.txt`. No new packages needed!

## Testing

### Test Script

Run the test:
```bash
python backend/test_search.py
```

**Expected output:**
```
================================================================================
SERPAPI GOOGLE SEARCH TEST
================================================================================

Environment Configuration:
  SERPAPI_KEY: ✅ Set

Testing search query: 'Morocco protest'

✅ GOOGLE AI OVERVIEW FOUND:
================================================================================
Title: Morocco Protests
Snippet: Recent demonstrations in Morocco have focused on...
Source: bbc.com

✅ ORGANIC SEARCH RESULTS: Found 5 results
================================================================================

1. Morocco announces new economic reforms
   Source: reuters.com
   Link: https://...
   Snippet: Morocco's government unveiled...
   Date: 2024-12-01
```

## What You Get

### 1. AI Overview (Google's AI Summary)

SerpAPI uses a **two-step process** to fetch detailed AI Overview:

**Step 1: Regular search**
```json
{
  "ai_overview": {
    "page_token": "KIVu-nictZPdjrI4GMeTPdkrWU8c..."  // Token for detailed fetch
  }
}
```

**Step 2: AI Overview API** (automatic in our code)
```json
{
  "ai_overview": {
    "text_blocks": [
      {
        "type": "paragraph",
        "snippet": "Thermodynamics is the branch of physics that deals with...",
        "reference_indexes": [0, 1, 2]
      },
      {
        "type": "list",
        "list": [
          {
            "title": "First Law",
            "snippet": "Energy cannot be created or destroyed..."
          }
        ]
      }
    ],
    "references": [
      {
        "title": "Thermodynamics - Wikipedia",
        "link": "https://...",
        "source": "Wikipedia",
        "index": 0
      }
    ]
  }
}
```

**Why it's valuable:**
- Google's AI has already analyzed multiple sources
- Structured data with references to original sources
- Shows if topic is widely covered (presence indicates legitimacy)
- If NO AI Overview exists, topic might be obscure/fabricated
- Text blocks can include: paragraphs, lists, comparisons, headings
- Each text block has reference indexes linking to sources

### 2. Organic Search Results

Regular search results from Google:

```json
{
  "organic_results": [
    {
      "title": "Morocco announces reforms...",
      "snippet": "The Moroccan government...",
      "source": "reuters.com",
      "link": "https://...",
      "date": "2024-12-01"
    }
  ]
}
```

### 3. Search Metadata

```json
{
  "search_info": {
    "query": "Morocco protest",
    "total_results": "1,240,000",
    "time_taken": "0.58 seconds"
  }
}
```

## Usage Limits & Pricing

### Free Tier
- **100 searches per month**
- Perfect for:
  - Development and testing
  - Small-scale fact-checking
  - Personal projects
  - Hackathons

### Paid Tiers (if you need more)

**Developer Plan: $50/month**
- 5,000 searches
- $0.01 per search
- Good for moderate use

**Production Plan: $250/month**
- 30,000 searches
- $0.0083 per search
- For high-volume applications

**For your hackathon:** Free tier (100/month) is plenty!

## Integration Details

### How It's Used in the Code

**Location:** `backend/fact_checker.py`

**Function:** `search_google_news(query, num_results=10)`

**Two-Step Process:**

1. **Regular Search** - Get organic results and AI Overview page token:
   ```python
   # Step 1: Regular Google Search
   params = {
     "engine": "google",
     "q": query,
     "num": 10
   }
   ```

2. **AI Overview API** - Fetch detailed structured AI Overview:
   ```python
   # Step 2: If page_token exists
   if data["ai_overview"].get("page_token"):
     ai_params = {
       "engine": "google_ai_overview",
       "page_token": data["ai_overview"]["page_token"]
     }
   ```

**Returns:**
```python
{
  "ai_overview": {
    "text_blocks": [
      # Structured paragraphs, lists, comparisons, etc.
    ],
    "references": [
      # Source citations with links
    ],
    "summary": "Readable text extracted from text_blocks",
    "thumbnail": "URL to image if present"
  },
  "organic_results": [
    {"title": "...", "snippet": "...", ...}
  ],
  "search_info": {
    "total_results": "1,240,000",
    "time_taken": "0.58 seconds"
  },
  "error": None
}
```

### How Gemini Uses It

**Old way (doesn't work):**
```
Prompt: "Search Google and verify this article"
Gemini: *hallucinates fake search results*
```

**New way (with SerpAPI):**
```
Prompt: "Here's what Google's AI Overview says: [real data]
And here are 10 real search results: [real data]
Compare the article against this ACTUAL data."

Gemini: *analyzes real search results, can't hallucinate*
```

## What Gets Saved

**File:** `backend/analysis/[session]/google_search_results.json`

**Example:**
```json
{
  "query": "Morocco protest GenZ 212",
  "search_date": "2024-12-08T15:30:00",
  "ai_overview": {
    "text_blocks": [
      {
        "type": "paragraph",
        "snippet": "Morocco has seen various protests...",
        "reference_indexes": [0, 1]
      },
      {
        "type": "list",
        "list": [
          {
            "title": "Economic Reforms",
            "snippet": "Recent protests focused on...",
            "reference_indexes": [2]
          }
        ]
      }
    ],
    "references": [
      {
        "title": "Morocco announces reforms",
        "link": "https://reuters.com/...",
        "source": "Reuters",
        "index": 0
      },
      {
        "title": "Protests in Morocco",
        "link": "https://bbc.com/...",
        "source": "BBC News",
        "index": 1
      }
    ],
    "summary": "Morocco has seen various protests...\n\nEconomic Reforms\nRecent protests focused on...",
    "thumbnail": null
  },
  "organic_results": [
    {
      "title": "Morocco economic reforms announced",
      "snippet": "Different story than article claims...",
      "source": "reuters.com",
      "link": "https://...",
      "date": "2024-12-01"
    }
  ],
  "num_organic_results": 1,
  "search_info": {
    "total_results": "45,000",
    "time_taken": "0.42 seconds"
  },
  "error": null
}
```

## Troubleshooting

### Error: "Missing SERPAPI_KEY"

**Solution:**
```bash
# Check if .env file exists
ls backend/.env

# Add the key
echo SERPAPI_KEY=your_key_here >> backend/.env
```

### Error: "API error: 401"

**Cause:** Invalid API key

**Solution:**
1. Go to https://serpapi.com/dashboard
2. Copy the correct API key
3. Update `.env` file
4. Restart backend server

### Error: "API error: 429"

**Cause:** Monthly quota exceeded (100 searches used)

**Solutions:**
1. **Wait:** Quota resets on 1st of next month
2. **Upgrade:** Add payment method for more searches
3. **Optimize:** Cache search results for common queries

### No Results Found

**Normal scenarios:**
- Obscure topics (no news coverage)
- Misspelled queries
- Very recent events (not indexed yet)
- Fabricated stories (this is good - proves it's fake!)

**To verify API is working:**
```bash
python backend/test_search.py
```

Try a common query like "latest technology news"

## Best Practices

### 1. Query Optimization

**Good queries:**
- "Morocco protest police" ✅
- "Keir Starmer UK Prime Minister" ✅
- "Manchester synagogue attack 2024" ✅

**Bad queries:**
- Full article titles (too specific) ❌
- Questions ("Is this true?") ❌
- Very long queries (truncated) ❌

### 2. Result Caching

Consider caching results for common queries:
```python
# Future enhancement
cache = {}
if query in cache:
    return cache[query]
```

### 3. Quota Management

Monitor your usage:
- Check dashboard: https://serpapi.com/dashboard
- Log search calls
- Alert when approaching 100 searches

### 4. Fallback Strategy

If SerpAPI fails:
```python
if search_data.get("error"):
    # Fallback to Gemini-only analysis
    # Still works, just without search verification
```

## Comparison: SerpAPI vs Alternatives

### SerpAPI (Recommended) ✅
- ✅ AI Overview included
- ✅ Easy setup (just API key)
- ✅ Reliable results
- ✅ Good free tier
- ❌ Lower free quota (100/month vs 100/day)

### Google Custom Search API
- ❌ No AI Overview
- ❌ Complex setup (engine + API)
- ✅ Higher free quota (100/day)
- ✅ Cheaper at scale

### Bing Search API
- ⚠️ Different results than Google
- ✅ 1,000 free queries/month
- ❌ No AI Overview
- ❌ Less familiar to users

### NewsAPI
- ❌ Only news, not general search
- ✅ 100 requests/day free
- ❌ No AI Overview
- ⚠️ Headlines only, limited content

**Verdict:** SerpAPI is best for this use case because AI Overview is valuable for fact-checking!

## Security Notes

### Protecting Your API Key

**DO:**
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variables
- ✅ Rotate key if exposed

**DON'T:**
- ❌ Commit API key to git
- ❌ Share key publicly
- ❌ Use in client-side code

### Example `.gitignore`:
```
.env
.env.local
*.env
```

## Next Steps

1. ✅ Get SerpAPI key
2. ✅ Add to `.env`
3. ✅ Run test script
4. ✅ Analyze a webpage
5. ✅ Check `google_search_results.json`
6. ✅ Review Gemini's evidence-based analysis

## Resources

- **SerpAPI Dashboard:** https://serpapi.com/dashboard
- **Documentation:** https://serpapi.com/search-api
- **Google News Search:** https://serpapi.com/google-news-api
- **Pricing:** https://serpapi.com/pricing

## Conclusion

SerpAPI makes it simple to get real Google search results including AI Overview. This transforms your fact-checking from "AI guessing" to "AI analyzing real evidence."

**Cost:** Free for 100 searches/month  
**Setup Time:** 5 minutes  
**Value:** Massive improvement in fact-checking accuracy! 🎯

# Google AI Overview API Implementation

**Date:** October 4, 2025  
**Purpose:** Detailed documentation of SerpAPI's AI Overview API integration

## Overview

Our fact-checking system now uses **SerpAPI's Google AI Overview API** to fetch structured, AI-generated summaries from Google Search. This provides richer context than simple search results alone.

## What is AI Overview?

AI Overview is Google's AI-generated summary that appears at the top of search results. It:

- **Synthesizes information** from multiple credible sources
- **Provides structured data** (paragraphs, lists, comparisons, tables)
- **Includes references** to original sources
- **Indicates topic legitimacy** - presence suggests well-documented topic
- **Is NOT available for all searches** - obscure/fabricated topics often lack it

## Two-Step API Process

SerpAPI requires two separate API calls to get detailed AI Overview:

### Step 1: Regular Google Search

**Purpose:** Get organic results + AI Overview page token

**Endpoint:** `https://serpapi.com/search`

**Parameters:**
```json
{
  "api_key": "your_serpapi_key",
  "engine": "google",
  "q": "your search query",
  "num": 10,
  "gl": "us",
  "hl": "en"
}
```

**Response (relevant parts):**
```json
{
  "ai_overview": {
    "page_token": "KIVu-nictZPdjrI4GMeTPdkrWU8c...",  // ← This is what we need!
    "text": "Brief preview text..."
  },
  "organic_results": [...],
  "news_results": [...]
}
```

**Important:** The `page_token` expires in **4 minutes** - must be used immediately!

### Step 2: AI Overview API

**Purpose:** Get detailed structured AI Overview data

**Endpoint:** `https://serpapi.com/search`

**Parameters:**
```json
{
  "api_key": "your_serpapi_key",
  "engine": "google_ai_overview",  // ← Special engine
  "page_token": "KIVu-nictZPdjrI4GMeTPdkrWU8c..."
}
```

**Response:**
```json
{
  "ai_overview": {
    "text_blocks": [
      {
        "type": "paragraph",
        "snippet": "Thermodynamics is the branch of physics...",
        "reference_indexes": [0, 1, 2]
      },
      {
        "type": "heading",
        "snippet": "Laws of Thermodynamics"
      },
      {
        "type": "list",
        "list": [
          {
            "title": "First Law",
            "snippet": "Energy cannot be created or destroyed...",
            "reference_indexes": [3]
          },
          {
            "title": "Second Law",
            "snippet": "Entropy of isolated systems increases...",
            "reference_indexes": [4, 5]
          }
        ]
      },
      {
        "type": "comparison",
        "product_labels": ["Product A", "Product B"],
        "comparison": [
          {
            "feature": "Weight",
            "values": ["7 oz", "6.6 oz"]
          }
        ]
      }
    ],
    "references": [
      {
        "title": "Thermodynamics - Wikipedia",
        "link": "https://en.wikipedia.org/wiki/Thermodynamics",
        "snippet": "Aug 26, 2024 — Thermodynamics is a branch of...",
        "source": "Wikipedia",
        "index": 0
      },
      {
        "title": "Laws of Thermodynamics | Physics",
        "link": "https://physics.stackexchange.com/...",
        "snippet": "The laws of thermodynamics define...",
        "source": "Physics Stack Exchange",
        "index": 1
      }
    ],
    "thumbnail": "https://..."
  }
}
```

## Text Block Types

AI Overview can contain various structured block types:

### 1. Paragraph
```json
{
  "type": "paragraph",
  "snippet": "The actual text content...",
  "snippet_highlighted_words": ["important", "terms"],
  "reference_indexes": [0, 1, 2]
}
```

### 2. Heading
```json
{
  "type": "heading",
  "snippet": "Section Title"
}
```

### 3. List
```json
{
  "type": "list",
  "list": [
    {
      "title": "List item title",
      "snippet": "Item description...",
      "reference_indexes": [1]
    },
    {
      "snippet": "Simple bullet point"
    },
    {
      // Nested lists possible
      "text_blocks": [...]
    }
  ]
}
```

### 4. Expandable Section
```json
{
  "type": "expandable",
  "title": "Click to expand",
  "text_blocks": [
    // Nested text blocks
  ]
}
```

### 5. Comparison Table
```json
{
  "type": "comparison",
  "product_labels": ["iPhone 15", "Samsung S24"],
  "comparison": [
    {
      "feature": "Screen Size",
      "values": ["6.1 inches", "6.2 inches"]
    },
    {
      "feature": "Weight",
      "values": ["171g", "168g"]
    }
  ]
}
```

### 6. Table
```json
{
  "type": "table",
  "table": [
    ["Header 1", "Header 2", "Header 3"],
    ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
    ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
  ]
}
```

### 7. Math Equations
```json
{
  "type": "paragraph",
  "snippet": "The solution is $x^{2}=0$, therefore $x=0$"
  // LaTeX formatting for math
}
```

## Our Implementation

### Code Location
`backend/fact_checker.py` → `search_google_news()` function

### Implementation Flow

```python
def search_google_news(query: str, num_results: int = 10) -> dict:
    # STEP 1: Regular search
    response = requests.get("https://serpapi.com/search", params={
        "engine": "google",
        "q": query,
        "num": num_results
    })
    
    data = response.json()
    
    # Extract organic results
    organic_results = data.get("news_results", []) or data.get("organic_results", [])
    
    # STEP 2: Check for AI Overview
    ai_overview_data = None
    if "ai_overview" in data and data["ai_overview"].get("page_token"):
        page_token = data["ai_overview"]["page_token"]
        
        # Fetch detailed AI Overview
        ai_response = requests.get("https://serpapi.com/search", params={
            "engine": "google_ai_overview",
            "page_token": page_token
        })
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            ai_overview_data = {
                "text_blocks": ai_data["ai_overview"]["text_blocks"],
                "references": ai_data["ai_overview"]["references"],
                "summary": _extract_ai_overview_summary(ai_data["ai_overview"])
            }
    
    return {
        "ai_overview": ai_overview_data,
        "organic_results": organic_results,
        "search_info": {...}
    }
```

### Helper Function: Extract Summary

We convert structured `text_blocks` into readable text:

```python
def _extract_ai_overview_summary(ai_overview_raw: dict) -> str:
    """Convert structured text_blocks to readable summary."""
    summary_parts = []
    
    for block in ai_overview_raw.get("text_blocks", []):
        if block["type"] == "paragraph":
            summary_parts.append(block["snippet"])
        
        elif block["type"] == "heading":
            summary_parts.append(f"\n{block['snippet']}\n")
        
        elif block["type"] == "list":
            for item in block["list"]:
                if "title" in item:
                    summary_parts.append(f"• {item['title']}")
                    if "snippet" in item:
                        summary_parts.append(f"  {item['snippet']}")
                elif "snippet" in item:
                    summary_parts.append(f"• {item['snippet']}")
    
    return "\n".join(summary_parts)
```

## How Gemini Uses AI Overview

When analyzing articles, Gemini receives:

1. **AI Overview Summary** - Readable text extracted from structured data
2. **AI Overview References** - List of credible sources Google used
3. **Organic Search Results** - Raw search results
4. **Search Metadata** - Total results, search time

### Prompt Example

```
**GOOGLE AI OVERVIEW:**
Google's AI analyzed multiple sources and provided this summary:

Thermodynamics is the branch of physics that deals with heat, work, and energy.

Laws of Thermodynamics
• First Law: Energy cannot be created or destroyed, only transferred
• Second Law: Entropy of isolated systems always increases
• Third Law: As temperature approaches absolute zero, entropy approaches minimum

References from AI Overview:
1. Thermodynamics - Wikipedia (https://...)
2. Laws of Thermodynamics | Physics (https://...)

**ORGANIC SEARCH RESULTS:**
1. Title: "Introduction to Thermodynamics"
   Source: MIT OpenCourseWare
   Snippet: Thermodynamics is the study of...
   
2. Title: "What is Thermodynamics?"
   Source: Physics.org
   Snippet: The science of energy transfer...
```

## Benefits for Fact-Checking

### 1. **Pre-Analyzed Context**
- Google's AI has already synthesized information from multiple sources
- Saves Gemini from making up interpretations

### 2. **Source Attribution**
- Each text block references specific sources via `reference_indexes`
- Gemini can cite which sources confirm/deny claims

### 3. **Structured Data**
- Easy to parse comparisons, lists, facts
- Better than unstructured text snippets

### 4. **Legitimacy Indicator**
- **AI Overview present** → Topic is well-documented across sources
- **No AI Overview** → Topic might be obscure, recent, or fabricated

### 5. **Multi-Source Synthesis**
- Single AI Overview might reference 5-10+ sources
- More comprehensive than individual search results

## Example: Fake News Detection

### Scenario: Analyzing "Morocco GenZ 212 Protest" Article

**Step 1: Search Query**
```
Query: "Morocco GenZ 212 protest"
```

**Step 2: Response Analysis**

**Case A: Fabricated Story**
```json
{
  "ai_overview": null,  // ← No AI Overview
  "organic_results": [],  // ← No search results
  "search_info": {
    "total_results": "0"
  }
}
```

**Gemini's Assessment:**
```
Risk Level: HIGH RISK - Likely Fabricated

Evidence:
- NO GOOGLE AI OVERVIEW: Google's AI found no credible information
- ZERO SEARCH RESULTS: No major news outlet has covered this
- The story appears to be completely fabricated
```

**Case B: Real Story (Different Context)**
```json
{
  "ai_overview": {
    "summary": "Morocco has seen recent protests focused on economic reforms...",
    "references": [
      {"title": "Morocco announces reforms", "source": "Reuters"},
      {"title": "Protests in Rabat", "source": "BBC News"}
    ]
  },
  "organic_results": [
    {
      "title": "Morocco's economic protest continues",
      "snippet": "Different from article's claims about 'GenZ 212'..."
    }
  ]
}
```

**Gemini's Assessment:**
```
Risk Level: MEDIUM RISK - Misleading Context

Evidence from AI Overview:
- Google's AI confirms protests in Morocco (verified via Reuters, BBC)
- However: AI Overview mentions "economic reforms", NOT "GenZ 212"
- Search results show economic protests, not the specific event claimed

Assessment:
- Real protests exist (confirmed by AI Overview references)
- Article appears to misrepresent or fabricate specific details
- "GenZ 212" terminology not found in any credible source
```

## Cost Implications

### API Usage Count

**Important:** Each complete search uses **2 API calls**:
1. Regular search (always executed)
2. AI Overview API (only if `page_token` exists)

**Free Tier:** 100 searches/month = **50 complete searches** with AI Overview

### Optimization Strategies

1. **Cache Results**
   ```python
   # Cache common queries
   if query in cache:
       return cache[query]
   ```

2. **Skip AI Overview for Non-Critical Searches**
   ```python
   # Option to disable AI Overview fetch
   if fetch_ai_overview and page_token:
       # Fetch detailed AI Overview
   ```

3. **Fallback to Simple Overview**
   ```python
   # Use basic AI Overview from Step 1 if available
   if "ai_overview" in data and not page_token:
       simple_overview = data["ai_overview"].get("text")
   ```

## Limitations & Considerations

### 1. **Not All Queries Have AI Overview**
- Obscure topics
- Very recent events (< 24 hours)
- Controversial/sensitive topics
- Regional/local news

**Solution:** This is actually useful - absence indicates lack of coverage!

### 2. **Page Token Expires in 4 Minutes**
- Must fetch immediately after Step 1
- Don't cache page tokens

**Solution:** Our code executes both steps sequentially

### 3. **Two API Calls Per Search**
- Doubles API usage
- 100 free searches = 50 with AI Overview

**Solution:** Monitor usage, implement caching for common queries

### 4. **Complex Structured Data**
- Not all text block types need to be displayed
- Some have nested structures

**Solution:** Our `_extract_ai_overview_summary()` flattens to readable text

## Testing

### Test Script
```bash
python backend/test_search.py
```

**Expected Output:**
```
✅ GOOGLE AI OVERVIEW FOUND:
================================================================================
Summary: Thermodynamics is the branch of physics that deals with...

📊 Structured Data: 5 text blocks
📚 References: 8 sources

Top References:
  1. Thermodynamics - Wikipedia...
     Source: Wikipedia
  2. Laws of Thermodynamics...
     Source: Physics.org
```

### Manual Testing

```python
from fact_checker import search_google_news

# Test with topic that likely has AI Overview
result = search_google_news("what is thermodynamics", num_results=5)

print(f"AI Overview: {bool(result['ai_overview'])}")
print(f"Text Blocks: {len(result['ai_overview']['text_blocks']) if result['ai_overview'] else 0}")
print(f"References: {len(result['ai_overview']['references']) if result['ai_overview'] else 0}")
```

## Troubleshooting

### Issue: "No AI Overview found"

**Causes:**
- Query doesn't trigger AI Overview (normal)
- Page token expired (shouldn't happen in our implementation)
- API error fetching AI Overview

**Debug:**
```python
# Check if page_token was present
if "ai_overview" in data:
    print(f"Page token: {data['ai_overview'].get('page_token')}")
```

### Issue: "AI Overview API returns 400/401"

**Causes:**
- Invalid or expired page token
- Incorrect API key
- Invalid parameters

**Solution:**
- Ensure using `engine=google_ai_overview` (not `google`)
- Check page token is from recent search (< 4 minutes)
- Verify API key is correct

### Issue: "Empty text_blocks array"

**Cause:** AI Overview exists but has no structured data

**Solution:** Fall back to simple text from Step 1:
```python
if not ai_overview_data["text_blocks"] and "ai_overview" in data:
    simple_text = data["ai_overview"].get("text")
```

## References

- **SerpAPI AI Overview Docs:** https://serpapi.com/google-ai-overview-api
- **SerpAPI Dashboard:** https://serpapi.com/dashboard
- **Our Implementation:** `backend/fact_checker.py` (lines 22-165)
- **Test Script:** `backend/test_search.py`

## Summary

The Google AI Overview API provides **structured, multi-source intelligence** that dramatically improves fact-checking accuracy:

✅ **Evidence-based** - Real sources, not AI hallucinations  
✅ **Structured data** - Easy to parse and reference  
✅ **Source attribution** - Know which sources confirm claims  
✅ **Legitimacy indicator** - Presence/absence signals topic coverage  
✅ **Cost-effective** - Free tier supports moderate usage  

The two-step process is handled automatically by our `search_google_news()` function, providing seamless integration with the fact-checking pipeline.

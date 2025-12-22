
# fact_checker.py
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure the Gemini API
try:
  genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
  print(f"Error configuring Gemini API: {e}")
  logger.error(f"Error configuring Gemini API: {e}")


def search_google_news(query: str, num_results: int = 10) -> dict:
  """
  Search Google News using SerpAPI for recent articles related to the query.
  Returns both AI Overview (using separate AI Overview API) and organic search results.
  
  Uses SerpAPI two-step process:
  1. Regular search to get page_token and organic results
  2. AI Overview API to get detailed AI-generated summary with structured data
  
  Returns:
    dict with:
      - ai_overview: Detailed AI Overview with text_blocks and references
      - organic_results: News articles from search
      - search_info: Metadata about the search
  """
  try:
    serpapi_key = os.getenv("SERPAPI_KEY")
    
    if not serpapi_key:
      logger.warning("SerpAPI key not configured (missing SERPAPI_KEY in .env)")
      return {
        "ai_overview": None,
        "organic_results": [],
        "error": "SerpAPI not configured"
      }
    
    # STEP 1: Regular Google search to get page_token and organic results
    url = "https://serpapi.com/search"
    
    params = {
      "api_key": serpapi_key,
      "engine": "google",
      "q": query,
      "num": min(num_results, 10),
      "gl": "us",  # Country
      "hl": "en",  # Language
    }
    
    logger.info(f"🔍 Step 1: Searching Google via SerpAPI: '{query}'")
    response = requests.get(url, params=params, timeout=15)
    
    if response.status_code != 200:
      logger.error(f"SerpAPI error: {response.status_code} - {response.text}")
      return {
        "ai_overview": None,
        "organic_results": [],
        "error": f"API error: {response.status_code}"
      }
    
    data = response.json()
    
    # Extract organic results (news or regular)
    organic_results = []
    
    # Try news_results first (if searching with tbm=nws)
    for item in data.get("news_results", [])[:num_results]:
      organic_results.append({
        "title": item.get("title", ""),
        "snippet": item.get("snippet", ""),
        "source": item.get("source", ""),
        "link": item.get("link", ""),
        "date": item.get("date", "Unknown"),
        "thumbnail": item.get("thumbnail", "")
      })
    
    # Fallback to organic_results if no news_results
    if not organic_results:
      for item in data.get("organic_results", [])[:num_results]:
        organic_results.append({
          "title": item.get("title", ""),
          "snippet": item.get("snippet", ""),
          "source": item.get("displayed_link", item.get("link", "")),
          "link": item.get("link", ""),
          "date": item.get("date", "Unknown"),
          "thumbnail": ""
        })
    
    # STEP 2: Check for AI Overview page_token and fetch detailed AI Overview
    ai_overview_data = None
    page_token = None
    
    # Check if AI Overview is available in the main search
    if "ai_overview" in data and data["ai_overview"].get("page_token"):
      page_token = data["ai_overview"]["page_token"]
      logger.info(f"🤖 Step 2: AI Overview available - fetching detailed data...")
      
      # Fetch detailed AI Overview using the AI Overview API
      ai_overview_params = {
        "api_key": serpapi_key,
        "engine": "google_ai_overview",
        "page_token": page_token
      }
      
      try:
        ai_response = requests.get(url, params=ai_overview_params, timeout=15)
        
        if ai_response.status_code == 200:
          ai_data = ai_response.json()
          
          # Extract structured AI Overview data
          if "ai_overview" in ai_data:
            ai_overview_raw = ai_data["ai_overview"]
            
            # Format the AI Overview data for Gemini analysis
            ai_overview_data = {
              "text_blocks": ai_overview_raw.get("text_blocks", []),
              "references": ai_overview_raw.get("references", []),
              "thumbnail": ai_overview_raw.get("thumbnail"),
              "summary": _extract_ai_overview_summary(ai_overview_raw)
            }
            logger.info(f"✅ Fetched detailed AI Overview with {len(ai_overview_data.get('text_blocks', []))} blocks")
        else:
          logger.warning(f"AI Overview API error: {ai_response.status_code}")
      
      except Exception as e:
        logger.warning(f"Could not fetch detailed AI Overview: {e}")
    
    # Fallback: Extract basic AI Overview from main search if detailed fetch failed
    if not ai_overview_data:
      if "answer_box" in data:
        answer_box = data["answer_box"]
        
        # Extract content based on answer_box type
        summary_text = ""
        title_text = answer_box.get("title", "")
        
        # Dictionary definition
        if answer_box.get("type") == "dictionary_results":
          word = answer_box.get("word", query)
          definitions = answer_box.get("definitions", [])
          if definitions:
            summary_text = f"{word}: {definitions[0]}" if isinstance(definitions, list) else str(definitions)
          title_text = f"Definition: {word}"
        
        # Organic answer (paragraph)
        elif "snippet" in answer_box:
          summary_text = answer_box.get("snippet", "")
          title_text = answer_box.get("title", "Answer")
        
        # List-type answer
        elif "list" in answer_box:
          summary_text = "\n".join(answer_box.get("list", []))
          title_text = answer_box.get("title", "Answer")
        
        ai_overview_data = {
          "summary": summary_text,
          "title": title_text,
          "source": answer_box.get("link", "Google"),
          "text_blocks": [],
          "references": []
        }
      elif "ai_overview" in data:
        ai_overview_data = {
          "summary": data["ai_overview"].get("text", ""),
          "title": "AI Overview",
          "source": "Google AI",
          "text_blocks": [],
          "references": []
        }
    
    logger.info(f"✅ Search complete - AI Overview: {bool(ai_overview_data)}, Organic: {len(organic_results)}")
    
    return {
      "ai_overview": ai_overview_data,
      "organic_results": organic_results,
      "search_info": {
        "query": query,
        "total_results": data.get("search_information", {}).get("total_results", "0"),
        "time_taken": data.get("search_information", {}).get("time_taken_displayed", "")
      },
      "error": None
    }
    
  except Exception as e:
    logger.error(f"Error searching via SerpAPI: {e}")
    return {
      "ai_overview": None,
      "organic_results": [],
      "error": str(e)
    }


def _extract_ai_overview_summary(ai_overview_raw: dict) -> str:
  """
  Extract a readable summary from AI Overview text_blocks.
  Converts structured text_blocks into a single summary string.
  """
  summary_parts = []
  
  for block in ai_overview_raw.get("text_blocks", []):
    block_type = block.get("type")
    
    if block_type == "paragraph":
      summary_parts.append(block.get("snippet", ""))
    
    elif block_type == "heading":
      summary_parts.append(f"\n{block.get('snippet', '')}\n")
    
    elif block_type == "list":
      for item in block.get("list", []):
        if "title" in item:
          summary_parts.append(f"• {item['title']}")
          if "snippet" in item:
            summary_parts.append(f"  {item['snippet']}")
        elif "snippet" in item:
          summary_parts.append(f"• {item['snippet']}")
  
  return "\n".join(summary_parts) if summary_parts else "AI Overview available (structured data)"

def analyze_with_gemini(video_metadata: dict, keyframe_paths: list[str], audio_info: dict = None, session_path: str = None) -> dict:
  """
  Analyzes video assets using the Gemini multi-modal model.
  Now includes Google Search verification for claims made in the video.
  
  Args:
    video_metadata: Dictionary containing video metadata
    keyframe_paths: List of paths to keyframe images
    audio_info: Dictionary containing audio file path and info
    session_path: Optional path to save analysis data for inspection
  """
  logger.info(f"🤖 Starting Gemini analysis")
  logger.info(f"   Video: {video_metadata.get('title', 'N/A')}")
  logger.info(f"   Keyframes: {len(keyframe_paths)}")
  logger.info(f"   Audio: {'Yes' if audio_info and audio_info.get('audio_path') else 'No'}")
  
  # Perform Google Search for video title/claims
  video_title = video_metadata.get('title', '')
  search_data = {"ai_overview": None, "organic_results": [], "error": None}
  
  if video_title:
    logger.info(f"🔍 Searching Google for video topic: '{video_title[:100]}'")
    search_data = search_google_news(video_title, num_results=10)
    
    # If no results with full title, try with keywords
    if not search_data.get("organic_results") and len(video_title.split()) > 3:
      keywords = ' '.join([w for w in video_title.split() if len(w) > 4][:5])
      logger.info(f"🔍 Trying search with keywords: '{keywords}'")
      search_data = search_google_news(keywords, num_results=10)
  
  # Format search results for prompt
  search_results_text = ""
  
  # Include AI Overview if present
  if search_data.get("ai_overview"):
    ai_overview = search_data["ai_overview"]
    has_structured = bool(ai_overview.get('text_blocks')) or bool(ai_overview.get('references'))
    has_summary = bool(ai_overview.get('summary'))
    
    if has_structured or has_summary:
      search_results_text += "\n**VERIFIED INFORMATION SUMMARY:**\n"
      search_results_text += f"Analysis of multiple authoritative sources on this topic:\n\n"
      
      if ai_overview.get('title'):
        search_results_text += f"**{ai_overview['title']}**\n"
      
      if has_summary:
        search_results_text += f"{ai_overview['summary']}\n\n"
      
      if ai_overview.get('references'):
        search_results_text += f"Sources consulted: {', '.join([r.get('source', 'N/A') for r in ai_overview['references'][:5]])}\n\n"
  
  # Include organic search results
  organic_results = search_data.get("organic_results", [])
  if organic_results:
    search_results_text += f"\n**CREDIBLE NEWS SOURCES ({len(organic_results)} results found):**\n"
    for idx, result in enumerate(organic_results, 1):
      search_results_text += f"{idx}. {result['title']} - {result['source']}\n"
      search_results_text += f"   {result['snippet'][:150]}...\n\n"
  else:
    search_results_text += "\n**VERIFICATION CHECK:**\n"
    search_results_text += "⚠️ No credible news coverage found for this topic - may be fabricated or unreported.\n\n"
  
  model = genai.GenerativeModel('gemini-3-flash-preview')
  prompt_parts = [
    f"I need you to analyze this video for authenticity and verify its claims. I've provided you with verified information to compare against.\n\n",
    f"**IMPORTANT:** You are an AI and do not have access to current dates. DO NOT use dates to judge credibility. Focus ONLY on factual content verification.\n\n",
    f"**Video Information:**\n- Title: {video_metadata.get('title')}\n- Uploader: {video_metadata.get('uploader')}\n- Platform: {video_metadata.get('platform', 'Unknown')}\n\n",
    search_results_text,
    "**Your Analysis Task:**\n",
    "1. **Verify Claims:**\n",
    "   - Use the verified information above to check video claims\n",
    "   - If information provided shows this is well-documented, it's likely real\n",
    "   - If NO verified information exists, claims are likely false\n",
    "   - DO NOT mention 'search results' or 'Google' in your response - phrase findings as verified facts\n",
    "   - IGNORE dates - verify facts, events, people only\n\n",
    "2. **Visual Analysis:**\n",
    "   - Look for signs of deepfakes (unnatural faces, weird lighting, distortions)\n",
    "   - Check if visuals match the claimed context\n",
    "   - Look for editing artifacts or manipulation\n\n",
    "3. **Audio/Caption Analysis:**\n",
    "   - What claims are being made?\n",
    "   - Does audio match the visuals?\n",
    "   - Any signs of audio manipulation?\n\n",
  ]
  
  # Add caption text if available
  has_captions = audio_info and audio_info.get('caption_text')
  has_audio = audio_info and audio_info.get('audio_path')
  
  if has_captions:
    prompt_parts.append(f"**Captions/Subtitles:**\n{audio_info['caption_text']}\n\n")
  
  prompt_parts.append("**Visual Content:**\n")
  prompt_parts.append(f"{len(keyframe_paths)} keyframes extracted from the video at equal intervals.\n")
  
  if has_audio:
    prompt_parts.append(f"Complete audio track included ({audio_info.get('duration', 0):.2f} seconds).\n\n")
  elif has_captions:
    prompt_parts.append(f"Captions/subtitles provided.\n\n")
  else:
    prompt_parts.append("No audio or captions available.\n\n")
  
  # Add JSON response format instruction
  prompt_parts.append(
    "**Response Format (JSON ONLY, no extra text):**\n"
    "IMPORTANT: In your response, DO NOT mention 'search results', 'Google', 'AI Overview', or 'verified information provided'. Write as if you independently verified these facts.\n"
    "IMPORTANT: DO NOT use dates for verification - you cannot determine if dates are current. Focus on factual content only.\n\n"
    "{\n"
    '  "risk_level": "High Risk/Medium Risk/Low Risk/Verified",\n'
    '  "summary": "Single-sentence finding (WITHOUT mentioning search/verification sources or dates)",\n'
    '  "context_check": {\n'
    '    "status": "Context Match/Mismatch/No Earlier Context Found",\n'
    '    "details": "Your assessment (DO NOT mention search or dates)"\n'
    '  },\n'
    '  "audio_visual_analysis": {\n'
    '    "key_claims": ["Claims from video"],\n'
    '    "audio_visual_match": "Assessment",\n'
    '    "manipulation_detected": "Any issues?"\n'
    '  },\n'
    '  "claim_verification": {\n'
    '    "status": "Verified/Unverified/Debunked",\n'
    '    "details": "State what you found (use phrases like \'well-documented event\', \'no credible reporting\', \'contradicts established facts\', WITHOUT mentioning dates)"\n'
    '  },\n'
    '  "visual_red_flags": ["Observed anomalies"]\n'
    '}\n'
  )
  
  # Build the complete prompt text for logging
  prompt_text = "".join([p for p in prompt_parts if isinstance(p, str)])
  
  # Save analysis data if session_path is provided
  if session_path:
    import video_processor
    import json
    
    video_processor.save_analysis_data(
      session_path=session_path,
      video_metadata=video_metadata,
      keyframe_paths=keyframe_paths,
      audio_info=audio_info,
      gemini_prompt=prompt_text
    )
    
    # Save search results
    try:
      if not os.path.exists(session_path):
        logger.error(f"❌ Session path does not exist: {session_path}")
        os.makedirs(session_path, exist_ok=True)
        logger.info(f"📁 Created session directory: {session_path}")
      
      search_results_path = os.path.join(session_path, "google_search_results.json")
      logger.info(f"💾 Attempting to save search results to: {search_results_path}")
      
      with open(search_results_path, 'w', encoding='utf-8') as f:
        json.dump({
          "query": video_title,
          "search_date": datetime.now().isoformat(),
          "ai_overview": search_data.get("ai_overview"),
          "organic_results": search_data.get("organic_results", []),
          "num_organic_results": len(search_data.get("organic_results", [])),
          "search_info": search_data.get("search_info", {}),
          "error": search_data.get("error")
        }, f, indent=2, ensure_ascii=False)
      logger.info(f"✅ Saved search results to: google_search_results.json")
    except Exception as save_error:
      logger.error(f"❌ Failed to save search results: {save_error}")
      logger.error(f"   Session path: {session_path}")
      logger.error(f"   Path exists: {os.path.exists(session_path) if session_path else 'N/A'}")
  
  # Add image data to the prompt
  content_parts = []
  for idx, path in enumerate(keyframe_paths):
    logger.info(f"   Loading image {idx+1}/{len(keyframe_paths)}: {os.path.basename(path)}")
    try:
      if not os.path.exists(path):
        logger.error(f"❌ Image file not found: {path}")
        continue
      with open(path, "rb") as img_file:
        content_parts.append({"mime_type": "image/jpeg", "data": img_file.read()})
    except Exception as img_error:
      logger.error(f"❌ Failed to load image {path}: {img_error}")
  
  # Add audio data if available (only if no captions, since captions are more reliable)
  if has_audio and not has_captions:
    audio_path = audio_info['audio_path']
    logger.info(f"   Loading audio: {os.path.basename(audio_path)}")
    try:
      if not os.path.exists(audio_path):
        logger.error(f"❌ Audio file not found: {audio_path}")
      else:
        with open(audio_path, 'rb') as f:
          audio_data = f.read()
        content_parts.append({"mime_type": "audio/mp3", "data": audio_data})
        logger.info(f"   Audio loaded successfully ({len(audio_data) / (1024*1024):.2f} MB)")
    except Exception as audio_error:
      logger.error(f"❌ Failed to load audio {audio_path}: {audio_error}")
  
  # Final instruction to the model
  instruction = "\n\nBased on all evidence (visual, audio/captions, and search results), generate ONLY a valid JSON object."
  
  logger.info(f"📤 Sending request to Gemini API...")
  logger.info(f"   Content: {len(content_parts)} parts (images + audio if included)")
  response = model.generate_content(prompt_parts + content_parts + [instruction])
  logger.info(f"✅ Received response from Gemini API")
  response = model.generate_content(prompt_parts + content_parts + [instruction])
  logger.info(f"✅ Received response from Gemini API")
  
  # Clean up the response to be valid JSON
  cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
  
  # Save the Gemini response if session_path is provided
  if session_path:
    try:
      if not os.path.exists(session_path):
        logger.error(f"❌ Session path does not exist when saving response: {session_path}")
        os.makedirs(session_path, exist_ok=True)
        logger.info(f"📁 Created session directory: {session_path}")
      
      response_path = os.path.join(session_path, "gemini_response.json")
      logger.info(f"💾 Attempting to save response to: {response_path}")
      
      with open(response_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_response)
      logger.info(f"✅ Saved Gemini response to: {os.path.basename(response_path)}")
      
      # Also save raw response for debugging
      raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
      with open(raw_response_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
      logger.info(f"✅ Saved raw response to: {os.path.basename(raw_response_path)}")
    except Exception as save_error:
      logger.error(f"❌ Failed to save Gemini response: {save_error}")
      logger.error(f"   Session path: {session_path}")
      logger.error(f"   Path exists: {os.path.exists(session_path) if session_path else 'N/A'}")
    
    # Also save raw response
    raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
    with open(raw_response_path, 'w', encoding='utf-8') as f:
      f.write(response.text)
    logger.info(f"💾 Saved raw Gemini response to: {os.path.basename(raw_response_path)}")
  
  import json
  return json.loads(cleaned_response)


def analyze_youtube_with_gemini(youtube_url: str, video_title: str, uploader: str, session_path: str = None) -> dict:
  """
  Analyzes a YouTube video by sending the URL directly to Gemini.
  Gemini can process YouTube URLs natively without downloading.
  
  Args:
    youtube_url: The YouTube video URL
    video_title: Title of the video
    uploader: Channel name
    session_path: Path to save analysis data for inspection
  """
  logger.info(f"🤖 Starting Gemini analysis for YouTube URL")
  logger.info(f"   Video: {video_title}")
  logger.info(f"   Uploader: {uploader}")
  logger.info(f"   URL: {youtube_url}")
  
  model = genai.GenerativeModel('gemini-3-flash-preview')
  
  prompt = f"""You are 'Vigil AI', a world-class OSINT (Open-Source Intelligence) video analyst. Your mission is to investigate a YouTube video for signs of misinformation, manipulation, or deepfakery and produce a structured JSON 'Trust Report'.

You have been provided with a YouTube video URL. Watch the video and perform the following analysis:

1. **Contextual Investigation:** Determine if this footage has appeared online before in a different context. Note any discrepancies between the original context and the claims in the video's metadata.

2. **Audio/Visual Analysis:** Review both the visual content and audio. Identify claims, statements, or narratives. Check if the audio matches the visual content. Note any inconsistencies or manipulation.

3. **Claim Corroboration:** Based on the video's title, audio content, and visual content, what is the central claim? Find credible, independent reports that either confirm or deny this event or claim.

4. **Visual Anomaly Detection:** Examine the video for common visual artifacts associated with deepfakes or digital manipulation (e.g., unnatural faces, inconsistent lighting, distorted backgrounds) and check if it seems to be AI generated.

**Video Information:**
- Title: {video_title}
- Uploader: {uploader}
- YouTube URL: {youtube_url}

Based on your analysis of the video, generate ONLY a valid JSON object with the following structure:
{{
  "risk_level": "High Risk/Medium Risk/Low Risk/Verified",
  "summary": "A single-sentence summary of your most critical finding.",
  "context_check": {{
    "status": "Context Match/Mismatch/No Earlier Context Found",
    "details": "Detailed explanation of contextual findings."
  }},
  "audio_visual_analysis": {{
    "key_claims": ["list of main claims from the video"],
    "audio_visual_match": "Assessment of whether audio matches visual content",
    "manipulation_detected": "Any signs of manipulation or inconsistencies"
  }},
  "claim_verification": {{
    "status": "Corroborated/Uncorroborated/Debunked",
    "details": "Detailed fact-checking results with sources if available."
  }},
  "visual_red_flags": ["List of observed visual anomalies or concerns."]
}}"""
  
  # Save the prompt if session_path is provided
  if session_path:
    os.makedirs(session_path, exist_ok=True)
    prompt_path = os.path.join(session_path, "gemini_prompt.txt")
    with open(prompt_path, 'w', encoding='utf-8') as f:
      f.write("="*80 + "\n")
      f.write("PROMPT TEXT:\n")
      f.write("="*80 + "\n")
      f.write(prompt + "\n\n")
      f.write("="*80 + "\n")
      f.write("CONTENT SENT:\n")
      f.write("="*80 + "\n")
      f.write(f"YouTube URL: {youtube_url}\n")
    logger.info(f"💾 Saved prompt to: {os.path.basename(prompt_path)}")
  
  try:
    logger.info(f"📤 Sending YouTube URL to Gemini API...")
    logger.info(f"   Content being sent: [Prompt + YouTube URL: {youtube_url}]")
    
    # Use dictionary format as shown in Gemini documentation
    # The model.generate_content accepts a list with text and file_data parts
    response = model.generate_content([
        prompt,
        {
            'file_data': {
                'file_uri': youtube_url
            }
        }
    ])
    
    logger.info(f"✅ Received response from Gemini API")
    
    # Clean up the response to be valid JSON
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    
    # Save responses if session_path is provided
    if session_path:
      response_path = os.path.join(session_path, "gemini_response.json")
      with open(response_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_response)
      logger.info(f"💾 Saved Gemini response to: {os.path.basename(response_path)}")
      
      # Also save raw response
      raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
      with open(raw_response_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
      logger.info(f"💾 Saved raw Gemini response to: {os.path.basename(raw_response_path)}")
    
    import json
    return json.loads(cleaned_response)
    
  except Exception as e:
    logger.error(f"❌ Gemini analysis failed: {str(e)}")
    # Return a fallback response
    return {
      "risk_level": "Error",
      "summary": f"Analysis failed: {str(e)}",
      "context_check": {"status": "Error", "details": "Unable to analyze"},
      "audio_visual_analysis": {
        "key_claims": [],
        "audio_visual_match": "Unknown",
        "manipulation_detected": "Unable to determine"
      },
      "claim_verification": {"status": "Error", "details": "Analysis incomplete"},
      "visual_red_flags": []
    }


def analyze_webpage_with_gemini(url: str, scraped_data: dict, session_path: str = None) -> dict:
  """
  Analyzes a web page's content for misinformation using Gemini.
  
  Args:
    url: The webpage URL
    scraped_data: Dictionary containing scraped content
    session_path: Path to save analysis data for inspection
  """
  logger.info(f"🤖 Starting Gemini analysis for webpage")
  logger.info(f"   Title: {scraped_data.get('title', 'N/A')}")
  logger.info(f"   URL: {url}")
  logger.info(f"   Content length: {scraped_data.get('word_count', 0)} words")
  
  model = genai.GenerativeModel('gemini-3-flash-preview')
  
  # Extract domain from URL to help contextualize the source
  from urllib.parse import urlparse
  source_domain = urlparse(url).netloc.replace('www.', '')
  
  # Perform actual Google searches for the article's main claims
  title_query = scraped_data.get('title', '')
  search_data = {"ai_overview": None, "organic_results": [], "error": None}
  
  if title_query:
    logger.info(f"🔍 Searching Google News for: '{title_query[:100]}'")
    search_data = search_google_news(title_query, num_results=10)
    
    # If no results with full title, try with key terms
    if not search_data.get("organic_results") and len(title_query.split()) > 3:
      # Extract key terms (remove common words)
      keywords = ' '.join([w for w in title_query.split() if len(w) > 4][:5])
      logger.info(f"🔍 Trying search with keywords: '{keywords}'")
      search_data = search_google_news(keywords, num_results=10)
  
  # Format search results for the prompt
  search_results_text = ""
  
  # Include AI Overview if present
  if search_data.get("ai_overview"):
    ai_overview = search_data["ai_overview"]
    
    # Check if we have structured AI Overview or simple overview
    has_structured = bool(ai_overview.get('text_blocks')) or bool(ai_overview.get('references'))
    has_summary = bool(ai_overview.get('summary'))
    
    if has_structured or has_summary:
      search_results_text += "\n\n**VERIFIED INFORMATION SUMMARY:**\n"
      search_results_text += f"Analysis of multiple authoritative sources:\n\n"
      
      if ai_overview.get('title'):
        search_results_text += f"**{ai_overview['title']}**\n"
      
      if has_summary:
        search_results_text += f"{ai_overview['summary']}\n\n"
      
      # Include references if available (from structured AI Overview)
      if ai_overview.get('references'):
        search_results_text += f"**Referenced Sources ({len(ai_overview['references'])} consulted):**\n"
        for idx, ref in enumerate(ai_overview['references'][:5], 1):
          search_results_text += f"  {idx}. {ref.get('title', 'N/A')} - {ref.get('source', 'N/A')}\n"
          if ref.get('link'):
            search_results_text += f"     {ref['link']}\n"
        search_results_text += "\n"
      
      if ai_overview.get('source') and ai_overview['source'] not in ['Google AI', 'Google']:
        search_results_text += f"Primary Source: {ai_overview['source']}\n"
      
      search_results_text += "\n"
  
  # Include organic search results
  organic_results = search_data.get("organic_results", [])
  if organic_results:
    search_results_text += "\n**CREDIBLE NEWS COVERAGE:**\n"
    search_results_text += f"Topic: '{title_query}'\n"
    search_results_text += f"Verified sources found: {len(organic_results)}\n"
    search_info = search_data.get("search_info", {})
    if search_info.get("total_results"):
      search_results_text += f"Total coverage: {search_info['total_results']} articles\n"
    search_results_text += f"Verification date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    for idx, result in enumerate(organic_results, 1):
      search_results_text += f"{idx}. **{result['title']}**\n"
      search_results_text += f"   Source: {result['source']}\n"
      search_results_text += f"   Snippet: {result['snippet']}\n"
      search_results_text += f"   Link: {result['link']}\n"
      if result.get('date') != 'Unknown':
        search_results_text += f"   Published: {result['date']}\n"
      search_results_text += "\n"
  else:
    search_results_text += "\n\n**VERIFICATION CHECK:**\n"
    search_results_text += f"Topic: '{title_query}'\n"
    search_results_text += "⚠️ NO CREDIBLE COVERAGE FOUND - No reputable news sources are reporting this story.\n"
    if search_data.get("error"):
      search_results_text += f"Note: {search_data['error']}\n"
    search_results_text += "\n"
  
  prompt = f"""I need you to fact-check this article. I've provided verified information from authoritative sources to compare against.

**IMPORTANT:** You are an AI and do not have access to current dates or real-time information. DO NOT use publication dates, article dates, or any temporal references to judge credibility. Focus ONLY on factual content verification.

**Your task:**
Compare the article's claims against the verified information I'm providing. Analyze what I've given you.

{search_results_text}

**How to analyze:**

1. **Verified Information (if present):**
   - What do authoritative sources say about this topic?
   - Does it support or contradict the article's claims?

2. **Compare article against credible coverage:**
   - Do ANY verified sources support the article's main claims?
   - Are the events, people, or facts mentioned in the article also in verified sources?
   - Do verified sources contradict the article?
   - If NO coverage found, that's strong evidence the story is fabricated or unreported.

3. **Source credibility:** 
   - What is "{source_domain}"? Is it among the verified sources?
   - Are the verified sources credible (BBC, Reuters, AP, etc.)?

4. **Content analysis:**
   - What are the specific factual claims in the article?
   - Do these claims match verified information?
   - IGNORE dates - verify facts, names, places, events only

**Article being fact-checked:**
- URL: {url}
- Source: {source_domain}
- Title: {scraped_data.get('title', 'N/A')}
- Description: {scraped_data.get('description', 'N/A')}
- Length: {scraped_data.get('word_count', 0)} words

**Article text:**
{scraped_data.get('text_content', 'No content available')[:8000]}

**Critical instructions:**
- Base your verification ONLY on the verified information provided above
- If there are NO verified sources, mark as "Uncorroborated" or "High Risk"  
- If verified sources contradict the article, mark as "Debunked" or "High Risk"
- If verified sources confirm it, mark as "Verified" or "Low Risk"
- In your response, do NOT explicitly mention "search results", "AI Overview", or "Google" - instead phrase your findings as if you analyzed the credibility yourself
- Write as an authoritative fact-checker, not as someone who Googled something
- Use language like "credible sources confirm", "established fact", "no credible reporting", "contradicts verified information"
- DO NOT use publication dates or article dates for verification - you cannot determine if dates are current
- IGNORE any future dates or past dates in articles - focus only on factual content verification

**Response format:**
Give me ONLY a JSON object with this exact structure (no extra text before or after):
{{
  "risk_level": "High Risk/Medium Risk/Low Risk/Verified",
  "summary": "Single-sentence critical finding (DO NOT mention search results - just state the facts)",
  "source_credibility": {{
    "status": "Credible/Questionable/Not Credible",
    "details": "Assessment of source reliability based on verification (DO NOT mention search or dates)"
  }},
  "claim_analysis": {{
    "topic_category": "Politics/Gaming/Entertainment/Technology/Sports/Science/Business/Local News/etc.",
    "main_claims": ["list of main claims from article"],
    "claim_types": "Factual/Opinion/Mixed",
    "sensationalism_detected": "Assessment of emotional manipulation"
  }},
  "fact_verification": {{
    "status": "Verified/Uncorroborated/Debunked/Mixed",
    "details": "State what can be verified about these claims (DO NOT mention search results, dates, or Google - use phrases like 'credible sources confirm', 'established historical fact', 'no credible reporting exists', 'contradicts verified information')",
    "credible_sources_found": {len(search_data.get("organic_results", []))},
    "verification_notes": ["Key findings from verification (WITHOUT mentioning search/Google/dates)"]
  }},
  "content_red_flags": ["Specific issues found (WITHOUT mentioning search comparison or dates)"]
}}"""
  
  # Save the prompt if session_path is provided
  if session_path:
    os.makedirs(session_path, exist_ok=True)
    prompt_path = os.path.join(session_path, "gemini_prompt.txt")
    with open(prompt_path, 'w', encoding='utf-8') as f:
      f.write("="*80 + "\n")
      f.write("PROMPT TEXT:\n")
      f.write("="*80 + "\n")
      f.write(prompt)
    logger.info(f"💾 Saved prompt to: {os.path.basename(prompt_path)}")
    
    # Save scraped data
    scraped_data_path = os.path.join(session_path, "scraped_content.json")
    with open(scraped_data_path, 'w', encoding='utf-8') as f:
      import json
      json.dump(scraped_data, f, indent=2, ensure_ascii=False)
    logger.info(f"💾 Saved scraped content to: {os.path.basename(scraped_data_path)}")
    
    # Save search results (SerpAPI format with AI Overview + organic results)
    search_results_path = os.path.join(session_path, "google_search_results.json")
    with open(search_results_path, 'w', encoding='utf-8') as f:
      json.dump({
        "query": title_query,
        "search_date": datetime.now().isoformat(),
        "ai_overview": search_data.get("ai_overview"),
        "organic_results": search_data.get("organic_results", []),
        "num_organic_results": len(search_data.get("organic_results", [])),
        "search_info": search_data.get("search_info", {}),
        "error": search_data.get("error")
      }, f, indent=2, ensure_ascii=False)
    
    results_count = len(search_data.get("organic_results", []))
    has_ai_overview = bool(search_data.get("ai_overview"))
    logger.info(f"💾 Saved search results: AI Overview={has_ai_overview}, Organic={results_count}")
  
  try:
    logger.info(f"📤 Sending webpage content to Gemini API...")
    organic_count = len(search_data.get("organic_results", []))
    ai_overview_status = "with AI Overview" if search_data.get("ai_overview") else "no AI Overview"
    logger.info(f"   Content: {scraped_data.get('word_count', 0)} words + {organic_count} search results ({ai_overview_status})")
    
    response = model.generate_content(prompt)
    
    logger.info(f"✅ Received response from Gemini API")
    
    # Extract the response text
    response_text = response.text.strip()
    
    # Clean up the response to be valid JSON
    cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
    
    # Save responses if session_path is provided
    if session_path:
      response_path = os.path.join(session_path, "gemini_response.json")
      with open(response_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_response)
      logger.info(f"💾 Saved Gemini response to: {os.path.basename(response_path)}")
      
      # Also save raw response
      raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
      with open(raw_response_path, 'w', encoding='utf-8') as f:
        f.write(response_text)
      logger.info(f"💾 Saved raw Gemini response to: {os.path.basename(raw_response_path)}")
    
    import json
    return json.loads(cleaned_response)
    
  except Exception as e:
    logger.error(f"❌ Gemini analysis failed: {str(e)}")
    return {
      "risk_level": "Error",
      "summary": f"Analysis failed: {str(e)}",
      "source_credibility": {"status": "Unknown", "details": "Unable to analyze"},
      "claim_analysis": {
        "main_claims": [],
        "claim_types": "Unknown",
        "sensationalism_detected": "Unable to determine"
      },
      "fact_verification": {"status": "Error", "details": "Analysis incomplete", "search_results_found": 0},
      "content_red_flags": []
    }


def analyze_audio_with_gemini(audio_path: str, filename: str, session_path: str = None) -> dict:
  """
  Analyzes uploaded audio files for misinformation, deepfakes, and authenticity using Gemini.
  Now includes Google Search verification for claims made in the audio.
  """
  logger.info(f"🎤 Analyzing uploaded audio with Gemini: {filename}")
  
  try:
    # Verify audio file exists and is accessible
    if not os.path.exists(audio_path):
      raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    logger.info(f"   Audio file size: {os.path.getsize(audio_path)} bytes")
    
    # Perform Google Search based on filename (often contains topic)
    # Remove file extension and clean up filename for search
    search_query = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
    search_data = {"ai_overview": None, "organic_results": [], "error": None}
    
    if len(search_query) > 3:  # Only search if filename is meaningful
      logger.info(f"🔍 Searching Google for audio topic: '{search_query[:100]}'")
      search_data = search_google_news(search_query, num_results=10)
    
    # Format search results for prompt
    search_results_text = ""
    
    # Include AI Overview if present
    if search_data.get("ai_overview"):
      ai_overview = search_data["ai_overview"]
      if ai_overview.get('summary') or ai_overview.get('title'):
        search_results_text += "\n**VERIFIED INFORMATION:**\n"
        if ai_overview.get('title'):
          search_results_text += f"**{ai_overview['title']}**\n"
        if ai_overview.get('summary'):
          search_results_text += f"{ai_overview['summary']}\n\n"
    
    # Include organic search results
    organic_results = search_data.get("organic_results", [])
    if organic_results:
      search_results_text += f"\n**CREDIBLE SOURCES ({len(organic_results)} found):**\n"
      for idx, result in enumerate(organic_results, 1):
        search_results_text += f"{idx}. {result['title']} - {result['source']}\n"
        search_results_text += f"   {result['snippet'][:120]}...\n\n"
    elif search_query:
      search_results_text += f"\n**VERIFICATION CHECK:** No credible coverage found for '{search_query}'\n\n"
    
    # Use Gemini 2.0 Flash Exp for audio analysis
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""I need you to analyze this audio file for authenticity and verify claims. I've provided verified information to compare against.

**Audio file:** "{filename}"
**IMPORTANT:** You are an AI and do not have access to current dates. DO NOT use dates to judge credibility. Focus ONLY on factual content verification.

{search_results_text}

**Your Analysis Task:**

1. **Listen and Transcribe:**
   - What's being said in the audio?
   - Who might be speaking (if identifiable)?
   - What are the main claims?

2. **Verify Claims:**
   - Use the verified information above to check audio claims
   - If information shows this is well-documented, it's likely accurate
   - If NO verified information exists, claims may be fabricated
   - DO NOT mention 'search results' or 'Google' in your response
   - IGNORE dates - verify facts, events, people only

3. **Audio Quality Assessment:**
   - Evidence of manipulation or deepfake?
   - Unnatural artifacts, glitches, or inconsistencies?
   - Natural speech patterns?

4. **Content Verification:**
   - Are factual claims verifiable?
   - Any sensationalism or fear-mongering?
   - Out of context usage?

**Response format (JSON ONLY, no extra text):**
IMPORTANT: DO NOT mention 'search results', 'Google', 'AI Overview', or 'verified information' in your response. Write as if you independently verified these facts.
IMPORTANT: DO NOT use dates for verification - you cannot determine if dates are current. Focus on factual content only.

{{
  "audio_authenticity_assessment": {{
    "transcription_summary": "What was said",
    "manipulation_indicators": "Signs of manipulation or deepfake",
    "audio_quality": "Assessment of audio quality"
  }},
  "content_analysis": {{
    "main_claims_or_statements": "Key claims",
    "speaker_identification": "Speaker if determinable",
    "emotional_tone_and_intent": "Tone analysis",
    "context_and_setting": "Context clues"
  }},
  "fact_verification": {{
    "status": "Verified/Unverified/Debunked",
    "details": "What you found (use phrases like 'well-documented', 'no credible reporting', 'contradicts established facts', WITHOUT mentioning dates)",
    "sensationalism_tactics": "Emotional manipulation"
  }},
  "red_flags": ["Specific concerns"],
  "risk_level": "High Risk/Medium Risk/Low Risk/Verified",
  "final_verdict": "Assessment with confidence (WITHOUT mentioning search/verification sources or dates)"
}}"""

    # Save prompt and search results
    if session_path:
      import json
      
      try:
        if not os.path.exists(session_path):
          logger.error(f"❌ Session path does not exist: {session_path}")
          os.makedirs(session_path, exist_ok=True)
          logger.info(f"📁 Created session directory: {session_path}")
        
        prompt_path = os.path.join(session_path, "gemini_prompt.txt")
        logger.info(f"💾 Attempting to save prompt to: {prompt_path}")
        
        with open(prompt_path, 'w', encoding='utf-8') as f:
          f.write(prompt)
        logger.info(f"✅ Saved prompt")
      except Exception as save_error:
        logger.error(f"❌ Failed to save prompt: {save_error}")
        logger.error(f"   Session path: {session_path}")
      
      # Save search results
      try:
        search_results_path = os.path.join(session_path, "google_search_results.json")
        logger.info(f"💾 Attempting to save search results to: {search_results_path}")
        
        with open(search_results_path, 'w', encoding='utf-8') as f:
          json.dump({
            "query": search_query,
            "search_date": datetime.now().isoformat(),
            "ai_overview": search_data.get("ai_overview"),
            "organic_results": search_data.get("organic_results", []),
            "num_organic_results": len(search_data.get("organic_results", [])),
            "search_info": search_data.get("search_info", {}),
            "error": search_data.get("error")
          }, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Saved search results")
      except Exception as save_error:
        logger.error(f"❌ Failed to save search results: {save_error}")
        logger.error(f"   Session path: {session_path}")
    
    # Upload audio file to Gemini
    logger.info(f"   📤 Uploading audio to Gemini...")
    
    # Check if audio file exists before uploading
    if not os.path.exists(audio_path):
      raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    logger.info(f"   Audio file exists: {audio_path} ({os.path.getsize(audio_path)} bytes)")
    audio_file = genai.upload_file(path=audio_path)
    logger.info(f"   ✅ Audio uploaded, processing...")
    
    # Send to Gemini with audio
    response = model.generate_content([prompt, audio_file])
    
    response_text = response.text.strip()
    logger.info(f"   ✅ Analysis complete")
    
    # Save raw response
    if session_path:
      try:
        if not os.path.exists(session_path):
          logger.error(f"❌ Session path does not exist when saving raw response: {session_path}")
          os.makedirs(session_path, exist_ok=True)
          logger.info(f"📁 Created session directory: {session_path}")
        
        raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
        logger.info(f"💾 Attempting to save raw response to: {raw_response_path}")
        
        with open(raw_response_path, 'w', encoding='utf-8') as f:
          f.write(response_text)
        logger.info(f"✅ Saved raw response")
      except Exception as save_error:
        logger.error(f"❌ Failed to save raw response: {save_error}")
        logger.error(f"   Session path: {session_path}")
    
    # Try to extract JSON
    import json
    import re
    
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
      result = json.loads(json_match.group(1))
    else:
      # Try without code blocks
      cleaned = response_text.replace("```json", "").replace("```", "").strip()
      result = json.loads(cleaned)
    
    # Save JSON response
    if session_path:
      json_response_path = os.path.join(session_path, "gemini_response.json")
      with open(json_response_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
      logger.info(f"   💾 Saved JSON response")
    
    logger.info(f"✅ Gemini audio analysis complete")
    return result
    
  except FileNotFoundError as e:
    logger.error(f"❌ Audio file not found: {e}")
    return {
      "error": f"File not found: {str(e)}",
      "audio_authenticity_assessment": {"status": "Error"},
      "content_analysis": {"main_claims_or_statements": "Error accessing file"},
      "red_flags": ["Audio file could not be accessed"],
      "final_verdict": "Error: File not found"
    }
  except Exception as e:
    logger.error(f"❌ Gemini audio analysis failed: {e}")
    import traceback
    logger.error(f"   Stack trace: {traceback.format_exc()}")
    return {
      "error": str(e),
      "authenticity": {"status": "Error", "confidence": 0},
      "content_analysis": {"main_claims": [], "concerns": []},
      "red_flags": [f"Analysis failed: {str(e)}"],
      "final_verdict": f"Error: {str(e)}"
    }


def analyze_document_with_gemini(filename: str, extracted_text: str, session_path: str = None, embedded_images: list[str] = None) -> dict:
  """
  Analyzes uploaded documents (PDF, Word, etc.) for misinformation and credibility.
  Can optionally include embedded images for visual analysis.
  """
  logger.info(f"📄 Analyzing uploaded document with Gemini: {filename}")
  
  try:
    # Verify extracted text is not empty
    if not extracted_text or len(extracted_text.strip()) == 0:
      raise ValueError("Extracted text is empty")
    
    logger.info(f"   Document text length: {len(extracted_text)} characters")
    
    # Load embedded images if provided
    image_objects = []
    if embedded_images:
      import PIL.Image
      logger.info(f"   📸 Loading {len(embedded_images)} embedded image(s)...")
      for img_path in embedded_images:
        try:
          img = PIL.Image.open(img_path)
          image_objects.append(img)
          logger.info(f"   ✅ Loaded: {os.path.basename(img_path)}")
        except Exception as e:
          logger.warning(f"   ⚠️ Failed to load {img_path}: {e}")
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Truncate very long texts
    max_chars = 50000
    if len(extracted_text) > max_chars:
      logger.warning(f"   ⚠️ Document too long ({len(extracted_text)} chars), truncating to {max_chars}")
      extracted_text = extracted_text[:max_chars] + "\n\n[... Document truncated ...]"
    
    # Add note about embedded images if present
    images_note = ""
    if image_objects:
      images_note = f"\n\n**Note:** This document contains {len(image_objects)} embedded image(s). Analyze them for relevance, authenticity, and any signs of manipulation."
    
    prompt = f"""I need you to analyze this document for credibility and verify the information in it. This is real document analysis.

**Document:** "{filename}"{images_note}

**What you need to do:**
- Check today's date first for temporal context
- Use Google Search to verify all factual claims, statistics, and references mentioned
- Search for information about any authors, organizations, or sources cited
- Look up dates, events, and information to confirm accuracy
- Verify authenticity of any quotes, data, or citations
- Search for corroboration before deciding something is false

**Document content:**
{extracted_text}

**What to analyze:**

1. **Is this document credible?**
   - Can you identify the source or publisher?
   - Is the author credible? (search for them)
   - What's the publication context?
   - Any signs this document is authentic or fabricated?

2. **What does it say?**
   - What are the main claims being made?
   - What evidence is provided?
   - Is there detectable bias?
   - Does the logic hold up?

3. **Are the facts accurate?**
   - Which facts can be verified? (search for them)
   - What claims lack verification?
   - Any statistical manipulation?
   - How good are the citations?

4. **Any red flags?**
   - Sensationalism or fear-mongering?
   - Cherry-picking data to support a narrative?
   - Information taken out of context?
   - Misleading framing or presentation?

**Response format:**
Give me ONLY a JSON object with this structure (no extra text):

{{
  "date_analyzed": "[Today's date]",
  "document_credibility": {{
    "source_identification": "your analysis",
    "author_credibility": "your analysis",
    "publication_context": "your analysis",
    "authenticity_indicators": "your analysis"
  }},
  "content_analysis": {{
    "main_claims": "your analysis",
    "evidence_provided": "your analysis",
    "bias_detection": "your analysis",
    "logical_consistency": "your analysis"
  }},
  "fact_verification": {{
    "verifiable_facts": "your analysis",
    "unverified_claims": "your analysis",
    "statistical_manipulation": "your analysis",
    "citation_quality": "your analysis"
  }},
  "misinformation_indicators": {{
    "sensationalism": "your analysis",
    "cherry_picking": "your analysis",
    "false_context": "your analysis",
    "misleading_framing": "your analysis"
  }},
  "red_flags": ["list", "of", "specific", "concerns"],
  "final_verdict": "Overall assessment of document reliability and trustworthiness"
}}"""

    # Save prompt
    if session_path:
      prompt_path = os.path.join(session_path, "gemini_prompt.txt")
      with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
      logger.info(f"   💾 Saved prompt")
    
    # Send to Gemini (with images if available)
    logger.info(f"   📤 Sending document to Gemini for analysis...")
    if image_objects:
      # Include images in the analysis
      content = [prompt] + image_objects
      response = model.generate_content(content)
      logger.info(f"   ✅ Sent text + {len(image_objects)} image(s) to Gemini")
    else:
      # Text only
      response = model.generate_content(prompt)
      logger.info(f"   ✅ Sent text to Gemini")
    
    # Save raw response
    if session_path:
      raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
      with open(raw_response_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
      logger.info(f"   💾 Saved raw response")
    
    # Extract JSON
    response_text = response.text
    import json
    import re
    
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
      result = json.loads(json_match.group(1))
    else:
      json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
      if json_match:
        result = json.loads(json_match.group(0))
      else:
        result = {"raw_analysis": response_text}
    
    # Save JSON response
    if session_path:
      json_response_path = os.path.join(session_path, "gemini_response.json")
      with open(json_response_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
      logger.info(f"   💾 Saved JSON response")
    
    logger.info(f"✅ Gemini document analysis complete")
    return result
    
  except ValueError as e:
    logger.error(f"❌ Document validation failed: {e}")
    return {
      "error": f"Invalid document: {str(e)}",
      "credibility": {"status": "Error", "confidence": 0},
      "content_analysis": {"main_claims": [], "concerns": []},
      "red_flags": ["Document could not be read or is empty"],
      "final_verdict": "Error: Document is empty or unreadable"
    }
  except Exception as e:
    logger.error(f"❌ Gemini document analysis failed: {e}")
    import traceback
    logger.error(f"   Stack trace: {traceback.format_exc()}")
    return {
      "error": str(e),
      "credibility": {"status": "Error", "confidence": 0},
      "content_analysis": {"main_claims": [], "concerns": []},
      "red_flags": [f"Analysis failed: {str(e)}"],
      "final_verdict": f"Error: {str(e)}"
    }


def analyze_image_with_gemini(image_path: str, filename: str, session_path: str = None) -> dict:
  """
  Analyzes uploaded images for manipulation, deepfakes, and misinformation.
  """
  logger.info(f"🖼️ Analyzing uploaded image with Gemini: {filename}")
  
  try:
    # Verify image file exists and is accessible
    if not os.path.exists(image_path):
      raise FileNotFoundError(f"Image file not found: {image_path}")
    
    logger.info(f"   Image file size: {os.path.getsize(image_path)} bytes")
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Upload image file to Gemini
    logger.info(f"   Uploading image file to Gemini...")
    image_file = genai.upload_file(image_path)
    logger.info(f"   ✅ Image uploaded successfully")
    
    prompt = f"""You are an expert OSINT analyst specializing in image forensics and misinformation detection.

Analyze this uploaded image: "{filename}"

Provide a comprehensive analysis in the following JSON structure (use these exact field names):

{{
  "image_authenticity_assessment": {{
    "digital_manipulation_signs": "your analysis",
    "metadata_concerns": "your analysis",
    "compression_artifacts": "your analysis",
    "lighting_shadow_inconsistencies": "your analysis",
    "reverse_image_search_notes": "your analysis"
  }},
  "content_analysis": {{
    "image_description": "your analysis",
    "context_and_setting": "your analysis",
    "visible_elements": "your analysis",
    "text_or_captions": "your analysis"
  }},
  "manipulation_detection": {{
    "ai_generated_indicators": "your analysis",
    "cloning_splicing_evidence": "your analysis",
    "color_grading_anomalies": "your analysis",
    "resolution_inconsistencies": "your analysis",
    "deepfake_indicators": "your analysis"
  }},
  "misinformation_context": {{
    "misuse_potential": "your analysis",
    "sensational_elements": "your analysis",
    "historical_context_usage": "your analysis",
    "viral_patterns": "your analysis"
  }},
  "red_flags": ["list", "of", "specific", "concerns"],
  "final_verdict": "Is this image authentic, manipulated, or AI-generated? Include confidence level."
}}

Respond ONLY with valid JSON using this exact structure."""

    # Save prompt
    if session_path:
      prompt_path = os.path.join(session_path, "gemini_prompt.txt")
      with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
      logger.info(f"   💾 Saved prompt")
    
    # Send to Gemini
    logger.info(f"   📤 Sending image to Gemini for analysis...")
    response = model.generate_content([prompt, image_file])
    
    # Save raw response
    if session_path:
      raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
      with open(raw_response_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
      logger.info(f"   💾 Saved raw response")
    
    # Extract JSON
    response_text = response.text
    import json
    import re
    
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
      result = json.loads(json_match.group(1))
    else:
      json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
      if json_match:
        result = json.loads(json_match.group(0))
      else:
        result = {"raw_analysis": response_text}
    
    # Save JSON response
    if session_path:
      json_response_path = os.path.join(session_path, "gemini_response.json")
      with open(json_response_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
      logger.info(f"   💾 Saved JSON response")
    
    logger.info(f"✅ Gemini image analysis complete")
    return result
    
  except FileNotFoundError as e:
    logger.error(f"❌ Image file not found: {e}")
    return {
      "error": f"File not found: {str(e)}",
      "authenticity": {"status": "Error", "confidence": 0},
      "manipulation_detection": {"indicators": [], "concerns": []},
      "red_flags": ["Image file could not be accessed"],
      "final_verdict": "Error: File not found"
    }
  except Exception as e:
    logger.error(f"❌ Gemini image analysis failed: {e}")
    import traceback
    logger.error(f"   Stack trace: {traceback.format_exc()}")
    return {
      "error": str(e),
      "authenticity": {"status": "Error", "confidence": 0},
      "manipulation_detection": {"indicators": [], "concerns": []},
      "red_flags": [f"Analysis failed: {str(e)}"],
      "final_verdict": f"Error: {str(e)}"
    }


def analyze_document_images_with_gemini(image_paths: list[str], filename: str, session_path: str = None) -> dict:
  """
  Analyzes image-based PDF documents using Gemini Vision API.
  Reads text directly from document images without OCR.
  """
  try:
    import PIL.Image
    import json
    import re
    
    logger.info(f"🤖 Analyzing image-based document with Gemini Vision API...")
    logger.info(f"   📄 Document: {filename}")
    logger.info(f"   🖼️ Pages: {len(image_paths)}")
    
    # Load all page images
    page_images = []
    for i, img_path in enumerate(image_paths, 1):
      img = PIL.Image.open(img_path)
      page_images.append(img)
      logger.info(f"   ✅ Loaded page {i}/{len(image_paths)}")
    
    # Create prompt for document analysis
    prompt = f"""You are an expert document analyst and fact-checker. Analyze this document carefully.

**Document:** {filename}
**Pages:** {len(page_images)}

**Your Task:**
1. Read ALL the text from every page of this document
2. Analyze the document's credibility, authenticity, and potential misinformation
3. Check for signs of manipulation, forgery, or suspicious content
4. Verify factual claims if possible
5. Assess the overall trustworthiness of the document

**Respond ONLY with valid JSON using this exact structure:**

{{
  "document_credibility": {{
    "status": "Authentic/Suspicious/Manipulated/Uncertain",
    "confidence": 0-100,
    "reasoning": "Detailed explanation of credibility assessment"
  }},
  "extracted_text_summary": {{
    "full_text": "Complete text extracted from all pages",
    "key_points": ["List of main points from the document"],
    "document_type": "Type of document (e.g., invoice, contract, certificate, etc.)"
  }},
  "content_analysis": {{
    "main_claims": ["List of key claims or statements"],
    "factual_accuracy": "Assessment of factual claims",
    "context": "Additional context or background information"
  }},
  "authenticity_indicators": {{
    "positive_signs": ["Signs that indicate authenticity"],
    "concerns": ["Any red flags or suspicious elements"],
    "document_quality": "Assessment of formatting, logos, signatures, etc."
  }},
  "misinformation_indicators": {{
    "detected": true/false,
    "type": "Type of potential misinformation if detected",
    "severity": "low/medium/high",
    "explanation": "Detailed explanation"
  }},
  "red_flags": [
    "List of specific concerns or red flags found"
  ],
  "final_verdict": {{
    "conclusion": "Overall assessment",
    "trustworthiness_score": 0-100,
    "recommendation": "Specific recommendations for the user"
  }}
}}

Be thorough, objective, and specific. Extract ALL visible text from the document."""

    # Save prompt
    if session_path:
      prompt_path = os.path.join(session_path, "gemini_prompt.txt")
      with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
      logger.info(f"   💾 Saved prompt")
    
    # Configure Gemini model for vision
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    # Send all pages to Gemini
    logger.info(f"   🚀 Sending {len(page_images)} pages to Gemini Vision API...")
    content = [prompt] + page_images
    response = model.generate_content(content)
    
    logger.info(f"   ✅ Received response from Gemini")
    
    # Save raw response
    if session_path:
      raw_response_path = os.path.join(session_path, "gemini_response_raw.txt")
      with open(raw_response_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
      logger.info(f"   💾 Saved raw response")
    
    # Extract JSON
    response_text = response.text
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
      result = json.loads(json_match.group(1))
    else:
      json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
      if json_match:
        result = json.loads(json_match.group(0))
      else:
        result = {"raw_analysis": response_text}
    
    # Save JSON response
    if session_path:
      json_response_path = os.path.join(session_path, "gemini_response.json")
      with open(json_response_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
      logger.info(f"   💾 Saved JSON response")
    
    logger.info(f"✅ Gemini document image analysis complete")
    return result
    
  except Exception as e:
    logger.error(f"❌ Gemini document image analysis failed: {e}")
    import traceback
    logger.error(f"   Stack trace: {traceback.format_exc()}")
    return {
      "error": str(e),
      "document_credibility": {"status": "Error", "confidence": 0},
      "content_analysis": {"main_claims": [], "factual_accuracy": "Error"},
      "red_flags": [f"Analysis failed: {str(e)}"],
      "final_verdict": {"conclusion": f"Error: {str(e)}", "trustworthiness_score": 0}
    }


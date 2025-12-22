#!/usr/bin/env python3
"""
Debug script to see raw SerpAPI AI Overview response
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

serpapi_key = os.getenv("SERPAPI_KEY")

if not serpapi_key:
    print("❌ SERPAPI_KEY not found in .env")
    exit(1)

# Test query - use something that typically triggers full AI Overview
# Try a comparison query which often triggers AI Overview
query = "iphone 15 vs samsung galaxy s24"

# Make API call
url = "https://serpapi.com/search"
params = {
    "api_key": serpapi_key,
    "engine": "google",
    "q": query,
    "num": 5,
    "gl": "us",
    "hl": "en"
}

print(f"Testing query: '{query}'")
print("="*80)

response = requests.get(url, params=params, timeout=15)

if response.status_code != 200:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

# Check for AI Overview
print("\n🔍 CHECKING FOR AI OVERVIEW IN RESPONSE:")
print("="*80)

if "ai_overview" in data:
    print("✅ 'ai_overview' field found in response!")
    print("\nAI Overview data:")
    print(json.dumps(data["ai_overview"], indent=2))
    
    if "page_token" in data["ai_overview"]:
        print("\n🎯 PAGE TOKEN FOUND!")
        print(f"Token: {data['ai_overview']['page_token'][:50]}...")
        print("\nNow fetching detailed AI Overview...")
        
        # Fetch detailed AI Overview
        ai_params = {
            "api_key": serpapi_key,
            "engine": "google_ai_overview",
            "page_token": data["ai_overview"]["page_token"]
        }
        
        ai_response = requests.get(url, params=ai_params, timeout=15)
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            print("\n✅ DETAILED AI OVERVIEW FETCHED!")
            print("\nStructure:")
            if "ai_overview" in ai_data:
                overview = ai_data["ai_overview"]
                print(f"  - text_blocks: {len(overview.get('text_blocks', []))} blocks")
                print(f"  - references: {len(overview.get('references', []))} sources")
                
                if overview.get('text_blocks'):
                    print("\n📝 First text block:")
                    first = overview['text_blocks'][0]
                    print(json.dumps(first, indent=2))
                
                if overview.get('references'):
                    print("\n📚 First reference:")
                    print(json.dumps(overview['references'][0], indent=2))
        else:
            print(f"\n❌ AI Overview API error: {ai_response.status_code}")
            print(ai_response.text)
    else:
        print("\nℹ️  No 'page_token' in ai_overview")
        print("   (AI Overview data is embedded in main response)")
        
elif "answer_box" in data:
    print("✅ 'answer_box' field found (alternative AI Overview format)")
    print("\nAnswer Box data:")
    print(json.dumps(data["answer_box"], indent=2))
else:
    print("ℹ️  No AI Overview or Answer Box found for this query")
    print("\nAvailable fields in response:")
    print(list(data.keys()))

print("\n" + "="*80)
print("Done!")

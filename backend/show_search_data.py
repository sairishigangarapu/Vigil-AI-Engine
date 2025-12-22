#!/usr/bin/env python3
"""
Show what AI Overview data we actually get from SerpAPI
"""

import os
import sys
from dotenv import load_dotenv
import json

sys.path.insert(0, os.path.dirname(__file__))
from fact_checker import search_google_news

load_dotenv()

print("="*80)
print("REAL SEARCH DATA ANALYSIS")
print("="*80)
print()

# Test with the original thermodynamics query
query = "What is thermodynamics"
print(f"Query: '{query}'")
print()

result = search_google_news(query, num_results=5)

print("📊 COMPLETE SEARCH RESULT DATA:")
print("="*80)
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)

ai = result.get("ai_overview")
if ai:
    print(f"✅ AI Overview present: Yes")
    print(f"   - Has text_blocks: {bool(ai.get('text_blocks'))}")
    print(f"   - Has references: {bool(ai.get('references'))}")
    print(f"   - Has summary: {bool(ai.get('summary'))}")
    print(f"   - Has title: {bool(ai.get('title'))}")
    
    if ai.get('summary'):
        print(f"\n   Summary preview:")
        print(f"   {ai['summary'][:200]}...")
else:
    print("❌ No AI Overview")

print(f"\nOrganic results: {len(result.get('organic_results', []))}")
print(f"Total Google results: {result.get('search_info', {}).get('total_results', 'N/A')}")

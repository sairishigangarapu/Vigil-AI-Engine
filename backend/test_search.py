#!/usr/bin/env python3
"""
Test script for SerpAPI Google Search integration.
Tests the search_google_news function to verify API configuration.
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from fact_checker import search_google_news

load_dotenv()

def main():
    print("="*80)
    print("SERPAPI GOOGLE SEARCH TEST")
    print("="*80)
    print()
    
    # Check environment variables
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    print("Environment Configuration:")
    print(f"  SERPAPI_KEY: {'✅ Set' if serpapi_key else '❌ Not set'}")
    print()
    
    if not serpapi_key:
        print("❌ ERROR: Missing SERPAPI_KEY environment variable!")
        print()
        print("Please add to your .env file:")
        print("  SERPAPI_KEY=your_serpapi_key_here")
        print()
        print("Get your free API key at: https://serpapi.com/")
        print("  - 100 free searches/month")
        print("  - No credit card required for free tier")
        return
    
    # Test search
    test_query = "What is thermodynamics"
    print(f"Testing search query: '{test_query}'")
    print()
    
    # Enable debug mode
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        search_data = search_google_news(test_query, num_results=5)
        
        # Check for errors
        if search_data.get("error"):
            print(f"❌ Search error: {search_data['error']}")
            print()
            print("Troubleshooting:")
            print("1. Check that SERPAPI_KEY is correct in .env file")
            print("2. Verify you haven't exceeded monthly quota (100 searches/month free)")
            print("3. Visit https://serpapi.com/dashboard to check your account")
            return
        
        # Display AI Overview if present
        ai_overview = search_data.get("ai_overview")
        if ai_overview:
            print("✅ GOOGLE AI OVERVIEW FOUND:")
            print("="*80)
            
            # Display summary
            if ai_overview.get('summary'):
                summary = ai_overview['summary']
                # Truncate if too long
                if len(summary) > 500:
                    print(f"Summary: {summary[:500]}...")
                else:
                    print(f"Summary: {summary}")
                print()
            
            # Display structured data info
            text_blocks = ai_overview.get('text_blocks', [])
            references = ai_overview.get('references', [])
            
            if text_blocks:
                print(f"📊 Structured Data: {len(text_blocks)} text blocks")
                # Show first text block as example
                first_block = text_blocks[0]
                print(f"\nExample Text Block (type: {first_block.get('type', 'unknown')}):")
                snippet = first_block.get('snippet', '')
                if snippet:
                    print(f"  {snippet[:200]}{'...' if len(snippet) > 200 else ''}")
                print()
            
            if references:
                print(f"📚 References: {len(references)} sources")
                print("\nTop References:")
                for i, ref in enumerate(references[:3], 1):
                    print(f"  {i}. {ref.get('title', 'N/A')[:60]}...")
                    print(f"     Source: {ref.get('source', 'N/A')}")
                    print(f"     Link: {ref.get('link', 'N/A')[:50]}...")
            else:
                print("ℹ️  AI Overview found but no detailed structured data")
                print("   (Fallback to simple AI Overview)")
                # Show fallback data if available
                if ai_overview.get('title'):
                    print(f"   Title: {ai_overview.get('title')}")
                if ai_overview.get('snippet'):
                    print(f"   Snippet: {ai_overview.get('snippet')[:200]}...")
            
            print()
        else:
            print("ℹ️  No AI Overview found for this query")
            print("   (AI Overview is not available for all searches)")
            print()
        
        # Display organic results
        organic_results = search_data.get("organic_results", [])
        if organic_results:
            print(f"✅ ORGANIC SEARCH RESULTS: Found {len(organic_results)} results")
            print("="*80)
            print()
            
            for i, result in enumerate(organic_results, 1):
                print(f"{i}. {result['title']}")
                print(f"   Source: {result['source']}")
                print(f"   Link: {result['link']}")
                print(f"   Snippet: {result['snippet'][:150]}...")
                if result.get('date') != 'Unknown':
                    print(f"   Date: {result['date']}")
                print()
            
            print("="*80)
            print("✅ SerpAPI is working correctly!")
            print()
            print("Search Info:")
            search_info = search_data.get("search_info", {})
            if search_info.get("total_results"):
                print(f"  Total results in Google: {search_info['total_results']}")
            if search_info.get("time_taken"):
                print(f"  Search time: {search_info['time_taken']}")
            print()
            print("Next steps:")
            print("1. The search function is integrated into webpage analysis")
            print("2. Real search results (including AI Overview) will be provided to Gemini")
            print("3. Results saved as 'google_search_results.json' in analysis sessions")
            
        else:
            print("⚠️  No organic results found")
            print()
            print("This could mean:")
            print("1. No news articles match this query (normal for some searches)")
            print("2. Try a more common search term")
            print()
            print("Let me try a different query...")
            
            # Try alternative search
            alt_query = "latest news technology"
            print(f"\nTesting with: '{alt_query}'")
            alt_data = search_google_news(alt_query, num_results=3)
            
            alt_results = alt_data.get("organic_results", [])
            if alt_results:
                print(f"✅ Found {len(alt_results)} results with alternative query")
                print("API is working - first query just had no matches")
            else:
                print("❌ Still no results - this might be a configuration issue")
    
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        print()
        print("Please check:")
        print("1. Your SERPAPI_KEY is valid")
        print("2. You have searches remaining in your quota")
        print("3. Your internet connection is working")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Check SerpAPI quota and usage
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv('SERPAPI_KEY')

print("="*80)
print("SERPAPI QUOTA CHECK")
print("="*80)
print()

if not SERPAPI_KEY:
    print("❌ SERPAPI_KEY not found in .env file")
    exit(1)

print(f"API Key: {SERPAPI_KEY[:20]}...")
print()

# Try a simple search to check status
url = "https://serpapi.com/account"
params = {
    "api_key": SERPAPI_KEY
}

try:
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Account Status:")
        print(f"   Plan: {data.get('plan', 'Unknown')}")
        print(f"   Searches this month: {data.get('this_month_usage', 'Unknown')}")
        print(f"   Total searches: {data.get('total_searches', 'Unknown')}")
        print()
        
        if data.get('plan') == 'free':
            remaining = 100 - int(data.get('this_month_usage', 100))
            print(f"🔢 Free tier remaining: {remaining}/100 searches")
            if remaining <= 0:
                print("❌ You've exhausted your free quota!")
                print("   Solutions:")
                print("   1. Wait until next month (resets on 1st)")
                print("   2. Upgrade: https://serpapi.com/pricing")
                print("   3. Create new account with different email")
    
    elif response.status_code == 429:
        print("❌ 429 TOO MANY REQUESTS")
        print("   You've exceeded your SerpAPI quota for this month")
        print()
        print("Solutions:")
        print("1. Wait until next month (resets on 1st)")
        print("2. Upgrade plan: https://serpapi.com/pricing")
        print("3. Get new free account: https://serpapi.com/users/sign_up")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Failed to check quota: {e}")

print()
print("="*80)
print("Dashboard: https://serpapi.com/dashboard")
print("="*80)

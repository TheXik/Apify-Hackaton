"""
Test script for Twitter Scraper.
Run: python test_twitter_scraper.py
"""

import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "talent-scout"))

from src.scrapers.twitter_scraper import TwitterScraper


def main():
    # Check for API token
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        print("❌ Error: APIFY_TOKEN environment variable not set")
        return
    
    print("🐦 Twitter Scraper Test")
    print("=" * 50)
    
    # Test query building
    scraper = TwitterScraper(apify_token)
    
    position = "AI ML Engineer"
    query = scraper.build_search_query(position)
    print(f"Position: {position}")
    print(f"Search query: {query}")
    print("=" * 50)
    
    # Search Twitter
    print(f"\n⏳ Searching Twitter for candidates...")
    candidates = scraper.search(position=position, max_items=10)
    
    print(f"\n🎯 Found {len(candidates)} candidates:")
    print("=" * 50)
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n#{i} {candidate['name']} (@{candidate.get('username', 'N/A')})")
        print(f"   Profile: {candidate['profileUrls'].get('twitter', 'N/A')}")
        if candidate.get('skills'):
            print(f"   Skills: {', '.join(candidate['skills'])}")
        print(f"   Bio: {candidate['bio'][:100]}...")
    
    # Save results
    output_file = "twitter_candidates.json"
    with open(output_file, "w") as f:
        json.dump({"candidates": candidates}, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to {output_file}")


if __name__ == "__main__":
    main()

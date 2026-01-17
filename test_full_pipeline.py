"""
Full Pipeline Test - Scrapers + AI Ranking

Tests the complete flow:
1. Scrape candidates from Twitter
2. Normalize to unified format
3. Rank with AI (semantic search + LLM)

Run: python test_full_pipeline.py
"""

import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add talent-scout src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "talent-scout"))

from src.scrapers.twitter_scraper import TwitterScraper
from src.candidate_ranker import CandidateRanker


def main():
    print("🚀 Talent Scout - Full Pipeline Test")
    print("=" * 60)
    
    # Check for required env vars
    apify_token = os.getenv("APIFY_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not apify_token:
        print("❌ Error: APIFY_TOKEN not set")
        return
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return
    
    # Job input
    job_input = {
        "jobTitle": "AI ML Engineer",
        "jobDescription": """
        We are looking for an experienced AI/ML Engineer to join our team.
        You will be responsible for:
        - Building and deploying machine learning models
        - Working with large language models (LLMs)
        - Developing RAG pipelines and AI agents
        - Collaborating with product and engineering teams
        
        The ideal candidate has strong Python skills and hands-on experience
        with modern ML frameworks.
        """,
        "requiredSkills": ["Python", "Machine Learning", "LLM", "AI"],
        "niceToHave": ["RAG", "LangChain", "NLP", "Computer Vision"],
        "experienceYears": 2
    }
    
    print(f"🎯 Job: {job_input['jobTitle']}")
    print(f"📋 Required Skills: {', '.join(job_input['requiredSkills'])}")
    print("=" * 60)
    
    # Step 1: Scrape Twitter
    print("\n📱 Step 1: Scraping Twitter...")
    twitter_scraper = TwitterScraper(apify_token)
    twitter_candidates = twitter_scraper.search(
        position=job_input["jobTitle"],
        max_items=15
    )
    print(f"   ✅ Found {len(twitter_candidates)} candidates from Twitter")
    
    # Step 2: Combine candidates (in real scenario, would also scrape LinkedIn, GitHub)
    print("\n🔗 Step 2: Combining candidates from all sources...")
    all_candidates = twitter_candidates  # Would add LinkedIn, GitHub here
    print(f"   ✅ Total candidates: {len(all_candidates)}")
    
    if not all_candidates:
        print("❌ No candidates found. Exiting.")
        return
    
    # Step 3: AI Ranking
    print("\n🤖 Step 3: AI Ranking (Semantic Search + LLM)...")
    ranker = CandidateRanker(openai_key)
    ranked_candidates = ranker.rank_candidates(
        job_input=job_input,
        candidates=all_candidates,
        top_k=5
    )
    print(f"   ✅ Ranked top {len(ranked_candidates)} candidates")
    
    # Results
    print("\n" + "=" * 60)
    print("🏆 TOP RANKED CANDIDATES")
    print("=" * 60)
    
    for i, candidate in enumerate(ranked_candidates, 1):
        print(f"\n#{i} {candidate['name']}")
        print(f"   Score: {candidate.get('score', 'N/A')}/100")
        print(f"   Source: {candidate.get('source', 'unknown')}")
        
        if candidate.get('matchedSkills'):
            print(f"   ✅ Matched: {', '.join(candidate['matchedSkills'])}")
        if candidate.get('missingSkills'):
            print(f"   ❌ Missing: {', '.join(candidate['missingSkills'])}")
        if candidate.get('summary'):
            print(f"   📝 {candidate['summary'][:150]}...")
        
        profile_url = candidate.get('profileUrls', {}).get('twitter', '')
        if profile_url:
            print(f"   🔗 {profile_url}")
    
    # Save results
    output = {
        "job": job_input,
        "totalCandidates": len(all_candidates),
        "rankedCandidates": ranked_candidates
    }
    
    output_file = "full_pipeline_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Full results saved to {output_file}")


if __name__ == "__main__":
    main()

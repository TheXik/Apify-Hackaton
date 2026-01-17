"""
Multi-Source Pipeline Test - All Scrapers + AI Ranking

Tests the complete flow with all sources:
1. Twitter (via TwitterScraper)
2. GitHub (via Google Search → GitHub profile URLs)
3. LinkedIn (via HarvestAPI Actor)
4. AI Ranking (semantic search + LLM)

Run: python test_all_sources.py
"""

import json
import os
import sys
import re
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "talent-scout", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from apify_client import ApifyClient
from src.candidate_ranker import CandidateRanker
from scrapers.twitter_scraper import TwitterScraper


# Actor IDs
GOOGLE_ACTOR_ID = "apify/google-search-scraper"
LINKEDIN_ACTOR_ID = "harvestapi/linkedin-profile-search"


def is_github_profile_url(url: str) -> bool:
    """Check if URL is a GitHub user profile."""
    if not url or "github.com" not in url:
        return False
    
    excluded_paths = [
        "/orgs/", "/topics/", "/explore", "/trending", "/collections",
        "/sponsors/", "/features/", "/enterprise", "/pricing",
        "/pulls", "/issues", "/actions", "/projects", "/security",
        "/blog/", "/customers/", "/events/", "/readme/",
    ]
    
    for path in excluded_paths:
        if path in url.lower():
            return False
    
    pattern = r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)(?:\?.*)?$"
    match = re.match(pattern, url)
    
    if match:
        username = match.group(1)
        if username.lower() not in ["login", "join", "search", "notifications"]:
            return True
    
    return False


def search_github_via_google(client: ApifyClient, job_title: str, skills: list, max_results: int = 10) -> list:
    """Search Google for GitHub profiles matching job requirements."""
    
    # Build search query
    query_parts = [job_title]
    if skills:
        query_parts.extend(skills[:3])
    query = " ".join(query_parts) + " site:github.com"
    
    print(f"   Query: {query}")
    
    google_input = {
        "queries": query,
        "maxPagesPerQuery": 2,
        "resultsPerPage": 10,
        "countryCode": "us",
        "languageCode": "en",
    }
    
    try:
        run = client.actor(GOOGLE_ACTOR_ID).call(
            run_input=google_input,
            timeout_secs=120,
        )
        
        profiles = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            for result in item.get("organicResults", []):
                url = result.get("url", "")
                
                if is_github_profile_url(url):
                    username_match = re.search(r"github\.com/([a-zA-Z0-9_-]+)", url)
                    username = username_match.group(1) if username_match else None
                    
                    title = result.get("title", "")
                    name = re.sub(r"\s*[-·|]\s*GitHub.*$", "", title, flags=re.IGNORECASE)
                    name = re.sub(r"\s*\(.*?\)\s*$", "", name)
                    
                    profiles.append({
                        "name": name.strip() if " " in name else username,
                        "username": username,
                        "bio": result.get("description", ""),
                        "skills": result.get("emphasizedKeywords", []),
                        "profileUrls": {"github": f"https://github.com/{username}"},
                        "source": "github",
                    })
                    
                    if len(profiles) >= max_results:
                        break
            
            if len(profiles) >= max_results:
                break
        
        return profiles
        
    except Exception as e:
        print(f"   ❌ Google/GitHub search failed: {e}")
        return []


def search_linkedin(client: ApifyClient, job_title: str, location: str, max_results: int = 10) -> list:
    """Search LinkedIn for candidate profiles."""
    
    linkedin_input = {
        "profileScraperMode": "Full",
        "searchQuery": job_title,
        "maxItems": max_results,
        "startPage": 1,
    }
    
    if location:
        linkedin_input["locations"] = [location]
    
    try:
        run = client.actor(LINKEDIN_ACTOR_ID).call(
            run_input=linkedin_input,
            timeout_secs=180,
        )
        
        profiles = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            profiles.append({
                "name": item.get("fullName", item.get("name", "Unknown")),
                "bio": item.get("headline", item.get("summary", "")),
                "skills": item.get("skills", []),
                "experience": item.get("experience", ""),
                "location": item.get("location", ""),
                "profileUrls": {"linkedin": item.get("profileUrl", item.get("url", ""))},
                "source": "linkedin",
            })
        
        return profiles
        
    except Exception as e:
        print(f"   ❌ LinkedIn search failed: {e}")
        return []


def main():
    print("🚀 TALENT SCOUT - MULTI-SOURCE PIPELINE TEST")
    print("=" * 70)
    
    # Check env vars
    apify_token = os.getenv("APIFY_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not apify_token:
        print("❌ APIFY_TOKEN not set")
        return
    if not openai_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    client = ApifyClient(apify_token)
    
    # Job requirements
    job_input = {
        "jobTitle": "Frontend Developer",
        "jobDescription": """
        We are looking for a Frontend Developer to join our team.
        You will build modern, responsive web applications using React and TypeScript.
        Experience with Next.js and testing is a plus.
        """,
        "requiredSkills": ["React", "TypeScript", "JavaScript", "CSS"],
        "niceToHave": ["Next.js", "Testing", "GraphQL"],
        "location": "Prague",
        "experienceYears": 2
    }
    
    print(f"\n🎯 Job: {job_input['jobTitle']}")
    print(f"📋 Skills: {', '.join(job_input['requiredSkills'])}")
    print(f"📍 Location: {job_input['location']}")
    print("=" * 70)
    
    all_candidates = []
    
    # 1. Twitter
    print("\n📱 [1/3] Searching Twitter...")
    try:
        twitter_scraper = TwitterScraper(apify_token)
        twitter_candidates = twitter_scraper.search(
            position=job_input["jobTitle"],
            max_items=10
        )
        print(f"   ✅ Found {len(twitter_candidates)} candidates")
        all_candidates.extend(twitter_candidates)
    except Exception as e:
        print(f"   ❌ Twitter failed: {e}")
    
    # 2. GitHub via Google
    print("\n🐙 [2/3] Searching GitHub (via Google)...")
    github_candidates = search_github_via_google(
        client=client,
        job_title=job_input["jobTitle"],
        skills=job_input["requiredSkills"],
        max_results=10
    )
    print(f"   ✅ Found {len(github_candidates)} candidates")
    all_candidates.extend(github_candidates)
    
    # 3. LinkedIn
    print("\n💼 [3/3] Searching LinkedIn...")
    linkedin_candidates = search_linkedin(
        client=client,
        job_title=job_input["jobTitle"],
        location=job_input["location"],
        max_results=10
    )
    print(f"   ✅ Found {len(linkedin_candidates)} candidates")
    all_candidates.extend(linkedin_candidates)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"📊 TOTAL CANDIDATES: {len(all_candidates)}")
    print(f"   Twitter: {len([c for c in all_candidates if c.get('source') == 'twitter'])}")
    print(f"   GitHub: {len([c for c in all_candidates if c.get('source') == 'github'])}")
    print(f"   LinkedIn: {len([c for c in all_candidates if c.get('source') == 'linkedin'])}")
    
    if not all_candidates:
        print("❌ No candidates found. Exiting.")
        return
    
    # AI Ranking
    print("\n🤖 AI RANKING (Semantic Search + LLM)...")
    ranker = CandidateRanker(openai_key)
    ranked = ranker.rank_candidates(
        job_input=job_input,
        candidates=all_candidates,
        top_k=10
    )
    print(f"   ✅ Ranked top {len(ranked)} candidates")
    
    # Results
    print("\n" + "=" * 70)
    print("🏆 TOP RANKED CANDIDATES")
    print("=" * 70)
    
    for i, c in enumerate(ranked, 1):
        source = c.get("source", "?")
        source_emoji = {"twitter": "📱", "github": "🐙", "linkedin": "💼"}.get(source, "❓")
        
        print(f"\n#{i} {c.get('name', 'Unknown')} {source_emoji}")
        print(f"   Score: {c.get('score', 'N/A')}/100 | Source: {source}")
        if c.get("matchedSkills"):
            print(f"   ✅ Matched: {', '.join(c['matchedSkills'][:5])}")
        if c.get("summary"):
            print(f"   📝 {c['summary'][:120]}...")
        
        # Profile URL
        urls = c.get("profileUrls", {})
        url = urls.get(source) or urls.get("twitter") or urls.get("github") or urls.get("linkedin")
        if url:
            print(f"   🔗 {url}")
    
    # Save
    output = {
        "job": job_input,
        "sources": ["twitter", "github", "linkedin"],
        "totalCandidates": len(all_candidates),
        "breakdown": {
            "twitter": len([c for c in all_candidates if c.get("source") == "twitter"]),
            "github": len([c for c in all_candidates if c.get("source") == "github"]),
            "linkedin": len([c for c in all_candidates if c.get("source") == "linkedin"]),
        },
        "rankedCandidates": ranked,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    with open("all_sources_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to all_sources_results.json")


if __name__ == "__main__":
    main()

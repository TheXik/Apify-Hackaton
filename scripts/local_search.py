import sys
import json
import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add talent-scout directory to path so we can import 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'talent-scout'))

# Load environment variables from the root .env file
root_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(root_env_path)

from apify_client import ApifyClient
from src.scrapers import LinkedInScraper, TwitterScraper, GitHubScraper
from src.candidate_ranker import CandidateRanker

async def run_search(input_data):
    job_title = input_data.get("jobTitle")
    location = input_data.get("location", "")
    skills = input_data.get("requiredSkills", [])
    max_candidates = input_data.get("maxCandidates", 5)
    
    apify_token = os.environ.get("APIFY_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not apify_token:
        sys.stderr.write("Error: APIFY_TOKEN not found in environment or .env file\n")
        print(json.dumps({"error": "APIFY_TOKEN not set", "candidates": []}))
        return

    all_candidates = []
    sources_used = []

    # 1. LinkedIn
    try:
        sys.stderr.write(f"🔗 Searching LinkedIn for '{job_title}' in '{location}'...\n")
        scraper = LinkedInScraper(apify_token)
        c = scraper.search(job_title, location, skills, max_items=max_candidates)
        all_candidates.extend(c)
        if c:
            sources_used.append("linkedin")
            sys.stderr.write(f"   Found {len(c)} LinkedIn profiles\n")
    except Exception as e:
        sys.stderr.write(f"LinkedIn error: {e}\n")

    # 2. Twitter
    try:
        sys.stderr.write(f"🐦 Searching Twitter for '{job_title}'...\n")
        scraper = TwitterScraper(apify_token)
        c = scraper.search(job_title, max_items=max_candidates)
        all_candidates.extend(c)
        if c:
            sources_used.append("twitter")
            sys.stderr.write(f"   Found {len(c)} Twitter candidates\n")
    except Exception as e:
        sys.stderr.write(f"Twitter error: {e}\n")

    # 3. GitHub (via Google search for profiles)
    try:
        sys.stderr.write(f"🐙 Searching GitHub for '{job_title}' in '{location}'...\n")
        scraper = GitHubScraper(apify_token)
        c = scraper.find_candidates_via_google(job_title, location, skills, max_results=max_candidates)
        all_candidates.extend(c)
        if c:
            sources_used.append("github")
            sys.stderr.write(f"   Found {len(c)} GitHub profiles\n")
    except Exception as e:
        sys.stderr.write(f"GitHub error: {e}\n")

    sys.stderr.write(f"📊 Total candidates before ranking: {len(all_candidates)}\n")

    # Ranking
    ranked = False
    if openai_key and all_candidates:
        try:
            sys.stderr.write(f"🧠 AI Ranking candidates...\n")
            ranker = CandidateRanker(openai_key)
            job_input = {
                "jobTitle": job_title,
                "jobDescription": input_data.get("jobDescription", job_title),
                "requiredSkills": skills,
                "location": location,
                "experienceYears": input_data.get("experienceYears", 2)
            }
            all_candidates = ranker.rank_candidates(job_input, all_candidates, top_k=max_candidates)
            ranked = True
            sys.stderr.write(f"   Ranked top {len(all_candidates)} candidates\n")
        except Exception as e:
            sys.stderr.write(f"Ranking error: {e}\n")

    # Output
    result = {
        "jobTitle": job_title,
        "totalFound": len(all_candidates),
        "ranked": ranked,
        "sources": sources_used,
        "candidates": all_candidates,
        "metadata": {
            "searchQuery": job_title,
            "location": location,
            "sources": sources_used,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    print(json.dumps(result))

if __name__ == "__main__":
    try:
        input_str = sys.stdin.read()
        input_data = json.loads(input_str)
        asyncio.run(run_search(input_data))
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

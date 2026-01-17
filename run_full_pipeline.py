"""
Full Pipeline Test - Scrape + Rank

This script:
1. Loads scraped GitHub profiles from talent-scout dataset
2. Ranks them using CandidateRanker (embeddings + LLM)
3. Outputs ranked results
"""

import json
import os
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.candidate_ranker import CandidateRanker


def load_scraped_profiles():
    """Load GitHub profiles from talent-scout dataset."""
    profiles = []
    dataset_path = "talent-scout/storage/datasets/default"
    
    for filepath in sorted(glob.glob(f"{dataset_path}/*.json")):
        if "__metadata__" in filepath:
            continue
        
        with open(filepath, "r") as f:
            profile = json.load(f)
            
        # Convert to ranker format
        profiles.append({
            "name": profile.get("name") or profile.get("username"),
            "bio": profile.get("bio", ""),
            "skills": profile.get("skills", []),
            "location": "",  # GitHub profiles don't always have location
            "profileUrl": profile.get("profileUrl", ""),
            "source": "github",
        })
    
    return profiles


def main():
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Run: export OPENAI_API_KEY='your-key'")
        return
    
    print("=" * 60)
    print("🚀 TALENT SCOUT - FULL PIPELINE TEST")
    print("=" * 60)
    
    # Step 1: Load scraped profiles
    print("\n📂 Loading scraped GitHub profiles...")
    profiles = load_scraped_profiles()
    print(f"   Found {len(profiles)} profiles")
    
    if not profiles:
        print("❌ No profiles found. Run 'apify run' in talent-scout first.")
        return
    
    # Show profiles
    print("\n📋 Scraped Profiles:")
    for i, p in enumerate(profiles, 1):
        print(f"   {i}. {p['name']}")
    
    # Job requirements
    job_input = {
        "jobTitle": "Senior Frontend Developer",
        "jobDescription": "We are looking for an experienced frontend developer with strong React and TypeScript skills. You will work on our main product, building modern UI components.",
        "requiredSkills": ["React", "TypeScript", "JavaScript", "CSS"],
        "niceToHave": ["Next.js", "GraphQL", "Testing"],
        "location": "Prague",
        "experienceYears": 3,
    }
    
    print(f"\n🎯 Job: {job_input['jobTitle']}")
    print(f"   Skills: {', '.join(job_input['requiredSkills'])}")
    print(f"   Location: {job_input['location']}")
    
    # Step 2: Rank with AI
    print("\n⏳ Ranking candidates with AI...")
    print("   - Generating embeddings (text-embedding-3-small)")
    print("   - Semantic search (cosine similarity)")
    print("   - LLM evaluation (GPT-4o-mini)")
    
    ranker = CandidateRanker(api_key)
    ranked = ranker.rank_candidates(
        job_input=job_input,
        candidates=profiles,
        top_k=5,
    )
    
    # Step 3: Show results
    print("\n" + "=" * 60)
    print("🏆 RANKED CANDIDATES")
    print("=" * 60)
    
    for i, candidate in enumerate(ranked, 1):
        score = candidate.get("score", "N/A")
        name = candidate.get("name", "Unknown")
        matched = ", ".join(candidate.get("matchedSkills", [])[:3])
        summary = candidate.get("summary", "")[:100]
        
        print(f"\n#{i} {name}")
        print(f"   Score: {score}/100")
        print(f"   Matched: {matched}")
        print(f"   {summary}...")
    
    # Save results
    output = {
        "job": job_input,
        "totalCandidates": len(profiles),
        "rankedCandidates": ranked,
    }
    
    with open("pipeline_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ Results saved to pipeline_results.json")
    print("=" * 60)


if __name__ == "__main__":
    main()

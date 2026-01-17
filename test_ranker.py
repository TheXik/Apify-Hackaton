"""
Simple test script to verify the candidate ranker works.
Run: python test_ranker.py
"""

import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.candidate_ranker import CandidateRanker


def main():
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Load test input
    with open("test_input.json", "r") as f:
        test_data = json.load(f)
    
    print("🚀 Talent Scout - Candidate Ranker Test")
    print("=" * 50)
    print(f"Job: {test_data['jobTitle']}")
    print(f"Candidates: {len(test_data['candidates'])}")
    print("=" * 50)
    
    # Initialize ranker
    ranker = CandidateRanker(api_key)
    
    # Build job input
    job_input = {
        "jobTitle": test_data["jobTitle"],
        "jobDescription": test_data["jobDescription"],
        "requiredSkills": test_data.get("requiredSkills", []),
        "niceToHave": test_data.get("niceToHave", []),
        "location": test_data.get("location", ""),
        "experienceYears": test_data.get("experienceYears", 0)
    }
    
    # Rank candidates
    print("\n⏳ Generating embeddings and ranking candidates...")
    ranked = ranker.rank_candidates(
        job_input=job_input,
        candidates=test_data["candidates"],
        top_k=test_data.get("topK", 5)
    )
    
    # Print results
    print("\n🏆 RANKED CANDIDATES:")
    print("=" * 50)
    
    for i, candidate in enumerate(ranked, 1):
        print(f"\n#{i} {candidate['name']} - Score: {candidate.get('score', 'N/A')}/100")
        print(f"   Matched Skills: {', '.join(candidate.get('matchedSkills', []))}")
        if candidate.get('missingSkills'):
            print(f"   Missing Skills: {', '.join(candidate['missingSkills'])}")
        if candidate.get('summary'):
            print(f"   Summary: {candidate['summary']}")
    
    # Save results
    output_file = "ranked_candidates.json"
    with open(output_file, "w") as f:
        json.dump({"candidates": ranked}, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to {output_file}")


if __name__ == "__main__":
    main()

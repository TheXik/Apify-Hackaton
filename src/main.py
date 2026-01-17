"""
Talent Scout - AI Powered Candidate Finder

Apify Actor entry point for ranking job candidates using 
semantic search and LLM evaluation.
"""

import os
from apify import Actor
from candidate_ranker import CandidateRanker


async def main():
    """Main Actor entry point."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Validate required fields
        job_title = actor_input.get("jobTitle")
        job_description = actor_input.get("jobDescription")
        
        if not job_title or not job_description:
            await Actor.fail("Missing required input: jobTitle and jobDescription are required")
            return
        
        # Get OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            await Actor.fail("Missing OPENAI_API_KEY environment variable")
            return
        
        # Get candidates (from input or would come from scraping in future)
        candidates = actor_input.get("candidates", [])
        
        if not candidates:
            await Actor.set_status_message("No candidates provided. Returning empty results.")
            await Actor.push_data({
                "jobTitle": job_title,
                "candidates": [],
                "message": "No candidates to evaluate. Provide candidates in input or integrate with scraping."
            })
            return
        
        # Initialize ranker
        await Actor.set_status_message(f"Ranking {len(candidates)} candidates for: {job_title}")
        ranker = CandidateRanker(openai_api_key)
        
        # Build job input
        job_input = {
            "jobTitle": job_title,
            "jobDescription": job_description,
            "requiredSkills": actor_input.get("requiredSkills", []),
            "niceToHave": actor_input.get("niceToHave", []),
            "location": actor_input.get("location", ""),
            "experienceYears": actor_input.get("experienceYears", 0)
        }
        
        # Rank candidates
        top_k = actor_input.get("topK", 10)
        ranked_candidates = ranker.rank_candidates(
            job_input=job_input,
            candidates=candidates,
            top_k=top_k
        )
        
        # Push results
        await Actor.push_data({
            "jobTitle": job_title,
            "totalCandidates": len(candidates),
            "rankedCandidates": len(ranked_candidates),
            "candidates": ranked_candidates
        })
        
        await Actor.set_status_message(
            f"Done! Ranked {len(ranked_candidates)} candidates from {len(candidates)} total."
        )

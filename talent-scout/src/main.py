"""Talent Scout - AI Powered Candidate Finder.

Combines multi-source scraping (LinkedIn, Twitter, GitHub) with AI-powered candidate ranking.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from apify import Actor
from apify_client import ApifyClient

from .candidate_ranker import CandidateRanker
from .scrapers import TwitterScraper


# Actor IDs
LINKEDIN_ACTOR_ID = "harvestapi/linkedin-profile-search"


async def main() -> None:
    """Main entry point for Talent Scout Actor."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        job_title = actor_input.get("jobTitle")
        job_description = actor_input.get("jobDescription", "")
        location = actor_input.get("location")
        max_candidates = actor_input.get("maxCandidates", 20)
        required_skills = actor_input.get("requiredSkills", [])
        nice_to_have = actor_input.get("niceToHave", [])
        experience_years = actor_input.get("experienceYears", 0)
        enable_ranking = actor_input.get("enableRanking", True)
        top_k = actor_input.get("topK", 10)
        
        # Source toggles
        sources = actor_input.get("sources", ["linkedin", "twitter"])
        
        # Validate required inputs
        if not job_title:
            await Actor.fail("Missing required input: jobTitle is required")
            return
        
        Actor.log.info(f"🎯 Searching for: {job_title}")
        Actor.log.info(f"📍 Location: {location or 'Any'}")
        Actor.log.info(f"📊 Max candidates: {max_candidates}")
        Actor.log.info(f"🔍 Sources: {', '.join(sources)}")
        Actor.log.info(f"🤖 AI Ranking: {'Enabled' if enable_ranking else 'Disabled'}")
        
        all_candidates = []
        
        # Search LinkedIn
        if "linkedin" in sources:
            await Actor.set_status_message("Searching LinkedIn for candidates...")
            linkedin_profiles = await search_linkedin(
                job_title=job_title,
                location=location,
                max_items=max_candidates,
            )
            
            if linkedin_profiles:
                Actor.log.info(f"✅ Found {len(linkedin_profiles)} profiles from LinkedIn")
                for profile in linkedin_profiles:
                    all_candidates.append({
                        "name": profile.get("fullName", profile.get("name", "Unknown")),
                        "bio": profile.get("headline", profile.get("summary", "")),
                        "skills": profile.get("skills", []),
                        "experience": profile.get("experience", ""),
                        "location": profile.get("location", ""),
                        "profileUrls": {
                            "linkedin": profile.get("profileUrl", profile.get("url", ""))
                        },
                        "source": "linkedin",
                        "rawProfile": profile
                    })
        
        # Search Twitter
        if "twitter" in sources:
            await Actor.set_status_message("Searching Twitter for candidates...")
            try:
                twitter_scraper = TwitterScraper()
                twitter_candidates = twitter_scraper.search(
                    position=job_title,
                    max_items=max_candidates
                )
                
                if twitter_candidates:
                    Actor.log.info(f"✅ Found {len(twitter_candidates)} profiles from Twitter")
                    all_candidates.extend(twitter_candidates)
                    
            except Exception as e:
                Actor.log.warning(f"Twitter search failed: {e}")
        
        # Check if we found any candidates
        if not all_candidates:
            Actor.log.warning("No candidates found from any source")
            await Actor.push_data({
                "candidates": [],
                "metadata": {
                    "totalFound": 0,
                    "searchQuery": job_title,
                    "sources": sources,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            })
            return
        
        Actor.log.info(f"📊 Total candidates from all sources: {len(all_candidates)}")
        
        # AI Ranking (if enabled and OpenAI key available)
        if enable_ranking:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            
            if openai_api_key and job_description:
                await Actor.set_status_message(f"Ranking {len(all_candidates)} candidates with AI...")
                Actor.log.info("🤖 Starting AI ranking...")
                
                try:
                    ranker = CandidateRanker(openai_api_key)
                    
                    job_input = {
                        "jobTitle": job_title,
                        "jobDescription": job_description,
                        "requiredSkills": required_skills,
                        "niceToHave": nice_to_have,
                        "location": location or "",
                        "experienceYears": experience_years
                    }
                    
                    ranked_candidates = ranker.rank_candidates(
                        job_input=job_input,
                        candidates=all_candidates,
                        top_k=top_k
                    )
                    
                    Actor.log.info(f"✅ Ranked {len(ranked_candidates)} candidates")
                    
                    # Push ranked results
                    await Actor.push_data({
                        "jobTitle": job_title,
                        "totalFound": len(all_candidates),
                        "ranked": True,
                        "sources": sources,
                        "candidates": ranked_candidates,
                        "metadata": {
                            "searchQuery": job_title,
                            "location": location,
                            "sources": sources,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    })
                    
                    await Actor.set_status_message(
                        f"Done! Ranked {len(ranked_candidates)} of {len(all_candidates)} candidates"
                    )
                    return
                    
                except Exception as e:
                    Actor.log.error(f"AI ranking failed: {e}")
                    Actor.log.info("Falling back to unranked results...")
            else:
                if not openai_api_key:
                    Actor.log.warning("OPENAI_API_KEY not set - skipping AI ranking")
                if not job_description:
                    Actor.log.warning("No job description provided - skipping AI ranking")
        
        # Fallback: Push unranked candidates
        await Actor.push_data({
            "jobTitle": job_title,
            "totalFound": len(all_candidates),
            "ranked": False,
            "sources": sources,
            "candidates": all_candidates,
            "metadata": {
                "searchQuery": job_title,
                "location": location,
                "sources": sources,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        })
        
        await Actor.set_status_message(f"Done! Found {len(all_candidates)} candidates (unranked)")


async def search_linkedin(
    job_title: str,
    location: str | None,
    max_items: int,
) -> list[dict]:
    """Search LinkedIn for candidates using the HarvestAPI Actor."""
    
    # Get Apify token from environment
    apify_token = os.environ.get("APIFY_TOKEN")
    if not apify_token:
        Actor.log.error("APIFY_TOKEN not found in environment")
        return []
    
    client = ApifyClient(apify_token)
    
    # Prepare LinkedIn search input
    linkedin_input = {
        "profileScraperMode": "Full",
        "searchQuery": job_title,
        "maxItems": max_items,
        "startPage": 1,
    }
    
    # Add location filter if provided
    if location:
        linkedin_input["locations"] = [location]
    
    Actor.log.info(f"Calling LinkedIn Actor with: {json.dumps(linkedin_input, indent=2)}")
    
    try:
        # Run the LinkedIn search Actor
        run = client.actor(LINKEDIN_ACTOR_ID).call(run_input=linkedin_input)
        
        # Get results from dataset
        profiles = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            profiles.append(item)
        
        return profiles
        
    except Exception as e:
        Actor.log.error(f"LinkedIn search failed: {e}")
        return []

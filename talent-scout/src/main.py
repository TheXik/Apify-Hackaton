"""Talent Scout - AI Powered Candidate Finder.

MVP v1: Just scrape LinkedIn data, no AI scoring yet.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from apify import Actor
from apify_client import ApifyClient


# LinkedIn Search Actor ID
LINKEDIN_ACTOR_ID = "harvestapi/linkedin-profile-search"


async def main() -> None:
    """Main entry point for Talent Scout Actor."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        job_title = actor_input.get("jobTitle")
        location = actor_input.get("location")
        max_candidates = actor_input.get("maxCandidates", 20)
        
        # Validate required inputs
        if not job_title:
            await Actor.fail("Missing required input: jobTitle is required")
            return
        
        Actor.log.info(f"🎯 Searching for: {job_title}")
        Actor.log.info(f"📍 Location: {location or 'Any'}")
        Actor.log.info(f"📊 Max candidates: {max_candidates}")
        
        # Search LinkedIn for candidates
        await Actor.set_status_message("Searching LinkedIn for candidates...")
        profiles = await search_linkedin(
            job_title=job_title,
            location=location,
            max_items=max_candidates,
        )
        
        if not profiles:
            Actor.log.warning("No candidates found on LinkedIn")
            await Actor.push_data({
                "candidates": [],
                "metadata": {
                    "totalFound": 0,
                    "searchQuery": job_title,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            })
            return
        
        Actor.log.info(f"✅ Found {len(profiles)} profiles")
        
        # Push each profile as a separate data item
        for profile in profiles:
            await Actor.push_data(profile)
        
        await Actor.set_status_message(f"Done! Found {len(profiles)} candidates")


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

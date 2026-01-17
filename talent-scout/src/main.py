"""
Talent Scout - GitHub Profile Finder

Finds GitHub developer profiles using Google Search and stores them in dataset.
Searches for developers matching job requirements on GitHub.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from apify import Actor
from apify_client import ApifyClient


# Google Search Actor ID
GOOGLE_ACTOR_ID = "apify/google-search-scraper"


async def main() -> None:
    """Main entry point for Talent Scout Actor."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        job_title = actor_input.get("jobTitle")
        job_description = actor_input.get("jobDescription", "")
        required_skills = actor_input.get("requiredSkills", [])
        location = actor_input.get("location")
        max_results = actor_input.get("maxResults", 30)
        
        # Validate required input
        if not job_title:
            await Actor.fail("Missing required input: jobTitle is required")
            return
        
        Actor.log.info(f"🎯 Searching for: {job_title}")
        Actor.log.info(f"🔧 Skills: {', '.join(required_skills) if required_skills else 'Any'}")
        Actor.log.info(f"📍 Location: {location or 'Any'}")
        
        # Get Apify client
        apify_token = os.environ.get("APIFY_TOKEN")
        if not apify_token:
            await Actor.fail("APIFY_TOKEN not found in environment")
            return
        
        client = ApifyClient(apify_token)
        
        # Build Google search query for GitHub profiles
        search_query = build_github_search_query(
            job_title=job_title,
            skills=required_skills,
            location=location,
        )
        
        Actor.log.info(f"🔍 Google query: {search_query}")
        await Actor.set_status_message("Searching for GitHub profiles...")
        
        # Run Google Search
        profiles = await search_github_profiles(
            client=client,
            query=search_query,
            max_results=max_results,
        )
        
        if not profiles:
            Actor.log.warning("No GitHub profiles found")
            await Actor.push_data({
                "status": "no_results",
                "query": search_query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return
        
        Actor.log.info(f"✅ Found {len(profiles)} GitHub profiles")
        
        # Store each profile in dataset
        for profile in profiles:
            await Actor.push_data(profile)
        
        await Actor.set_status_message(f"Done! Found {len(profiles)} GitHub profiles")


def build_github_search_query(
    job_title: str,
    skills: list[str],
    location: str | None,
) -> str:
    """Build optimized Google search query for GitHub profiles."""
    
    parts = [job_title]
    
    # Add top skills (max 3)
    if skills:
        parts.extend(skills[:3])
    
    # Add location if specified
    if location:
        parts.append(location)
    
    # Restrict to GitHub user profiles only
    query = " ".join(parts) + " site:github.com"
    
    return query


async def search_github_profiles(
    client: ApifyClient,
    query: str,
    max_results: int,
) -> list[dict]:
    """Search Google for GitHub profiles and extract profile data."""
    
    # Calculate pages needed (10 results per page)
    pages_needed = min((max_results + 9) // 10, 10)  # Max 10 pages
    
    google_input = {
        "queries": query,
        "maxPagesPerQuery": pages_needed,
        "resultsPerPage": 10,
        "countryCode": "us",
        "languageCode": "en",
    }
    
    Actor.log.info(f"Calling Google Search Actor...")
    Actor.log.debug(f"Input: {json.dumps(google_input, indent=2)}")
    
    try:
        # Run Google Search Actor
        run = client.actor(GOOGLE_ACTOR_ID).call(
            run_input=google_input,
            timeout_secs=300,
        )
        
        # Extract and normalize profiles
        profiles = []
        
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            # Google returns organic results as array
            for result in item.get("organicResults", []):
                url = result.get("url", "")
                
                # Filter: only GitHub user profile URLs (not repos, gists, etc.)
                if is_github_profile_url(url):
                    profile = normalize_github_result(result)
                    profiles.append(profile)
                    
                    if len(profiles) >= max_results:
                        break
            
            if len(profiles) >= max_results:
                break
        
        return profiles
        
    except Exception as e:
        Actor.log.error(f"Google Search failed: {e}")
        return []


def is_github_profile_url(url: str) -> bool:
    """Check if URL is a GitHub user profile (not repo, gist, etc.)."""
    
    if not url or "github.com" not in url:
        return False
    
    # Pattern: github.com/username (but not github.com/username/repo)
    # Also exclude: github.com/orgs, github.com/topics, github.com/explore, etc.
    
    excluded_paths = [
        "/orgs/", "/topics/", "/explore", "/trending", "/collections",
        "/sponsors/", "/features/", "/enterprise", "/pricing",
        "/about/", "/github/", "/settings", "/marketplace",
        "/pulls", "/issues", "/actions", "/projects", "/security",
        "/blog/", "/customers/", "/events/", "/readme/",
    ]
    
    for path in excluded_paths:
        if path in url.lower():
            return False
    
    # Check if it's a user profile: github.com/username or github.com/username?tab=...
    # Not a repo: github.com/username/reponame
    pattern = r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)(?:\?.*)?$"
    match = re.match(pattern, url)
    
    if match:
        username = match.group(1)
        # Exclude common non-user paths
        if username.lower() not in ["login", "join", "search", "notifications"]:
            return True
    
    return False


def normalize_github_result(result: dict) -> dict:
    """Normalize Google result to GitHub profile format."""
    
    url = result.get("url", "")
    title = result.get("title", "")
    description = result.get("description", "")
    
    # Extract username from URL
    username_match = re.search(r"github\.com/([a-zA-Z0-9_-]+)", url)
    username = username_match.group(1) if username_match else None
    
    # Try to extract name from title (usually "Name - GitHub" or "Name (username)")
    name = extract_name_from_title(title)
    
    # Extract skills from emphasized keywords
    skills = result.get("emphasizedKeywords", [])
    
    return {
        "source": "github",
        "username": username,
        "name": name,
        "url": url,
        "profileUrl": f"https://github.com/{username}" if username else url,
        "bio": description,
        "skills": skills,
        "title": title,
        "googlePosition": result.get("position"),
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
    }


def extract_name_from_title(title: str) -> str | None:
    """Extract person's name from Google result title."""
    
    if not title:
        return None
    
    # Remove common suffixes
    title = re.sub(r"\s*[-·|]\s*GitHub.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\(.*?\)\s*$", "", title)  # Remove (username)
    
    # If title looks like a name (not a username)
    if title and " " in title and not title.startswith("@"):
        return title.strip()
    
    return None

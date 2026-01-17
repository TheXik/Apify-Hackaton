"""
Talent Scout - Multi-Source Developer Finder

Combines multi-source scraping (LinkedIn, Twitter, GitHub) with AI-powered candidate ranking.
Searches for developers matching job requirements across multiple platforms.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from apify import Actor
from apify_client import ApifyClient

from .candidate_ranker import CandidateRanker
from .scrapers import TwitterScraper, GitHubScraper, LinkedInScraper


# Actor IDs
GOOGLE_ACTOR_ID = "apify/google-search-scraper"


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
        
        # Validate required input
        if not job_title:
            await Actor.fail("Missing required input: jobTitle is required")
            return
        
        Actor.log.info(f"🎯 Searching for: {job_title}")
        Actor.log.info(f"🔧 Skills: {', '.join(required_skills) if required_skills else 'Any'}")
        Actor.log.info(f"📍 Location: {location or 'Any'}")
        Actor.log.info(f"📊 Max candidates: {max_candidates}")
        Actor.log.info(f"🔍 Sources: {', '.join(sources)}")
        Actor.log.info(f"🤖 AI Ranking: {'Enabled' if enable_ranking else 'Disabled'}")
        
        all_candidates = []
        
        # Get Apify client for external actors
        apify_token = os.environ.get("APIFY_TOKEN")
        client = ApifyClient(apify_token) if apify_token else None
        
        # Search LinkedIn
        if "linkedin" in sources:
            await Actor.set_status_message("Searching LinkedIn for candidates...")
            try:
                linkedin_scraper = LinkedInScraper()
                linkedin_profiles = linkedin_scraper.search(
                    job_title=job_title,
                    location=location,
                    skills=required_skills,
                    max_items=max_candidates,
                )
                
                if linkedin_profiles:
                    Actor.log.info(f"✅ Found {len(linkedin_profiles)} profiles from LinkedIn")
                    all_candidates.extend(linkedin_profiles)
                else:
                    Actor.log.info("No profiles found from LinkedIn")
                    
            except Exception as e:
                Actor.log.warning(f"LinkedIn search failed: {e}")
        
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
        
        # Search GitHub (Google Search -> GitHub Profile Scraper)
        if "github" in sources and client:
            await Actor.set_status_message("Searching for GitHub profiles via Google...")
            try:
                # Step 1: Use Google to find GitHub profile URLs
                search_query = build_github_search_query(
                    job_title=job_title,
                    skills=required_skills,
                    location=location,
                )
                
                google_results = await search_github_via_google(
                    client=client,
                    query=search_query,
                    max_results=max_candidates,
                )
                
                if google_results:
                    Actor.log.info(f"✅ Found {len(google_results)} GitHub URLs via Google")
                    
                    # Step 2: Enrich with actual GitHub profile data
                    await Actor.set_status_message(f"Enriching {len(google_results)} GitHub profiles...")
                    
                    try:
                        github_scraper = GitHubScraper()
                        profile_urls = [r.get("profileUrl", r.get("url", "")) for r in google_results]
                        
                        enriched_profiles = github_scraper.scrape_profiles(
                            profile_urls=profile_urls,
                            max_items=max_candidates,
                        )
                        
                        if enriched_profiles:
                            Actor.log.info(f"✅ Enriched {len(enriched_profiles)} GitHub profiles")
                            all_candidates.extend(enriched_profiles)
                        else:
                            # Fallback to Google results if scraping fails
                            Actor.log.warning("GitHub enrichment failed, using Google results")
                            for profile in google_results:
                                all_candidates.append({
                                    "name": profile.get("name", profile.get("username", "Unknown")),
                                    "bio": profile.get("bio", ""),
                                    "skills": profile.get("skills", []),
                                    "experience": "",
                                    "location": "",
                                    "profileUrls": {
                                        "github": profile.get("profileUrl", profile.get("url", ""))
                                    },
                                    "source": "github",
                                    "rawProfile": profile
                                })
                                
                    except Exception as enrich_error:
                        Actor.log.warning(f"GitHub enrichment failed: {enrich_error}, using Google results")
                        for profile in google_results:
                            all_candidates.append({
                                "name": profile.get("name", profile.get("username", "Unknown")),
                                "bio": profile.get("bio", ""),
                                "skills": profile.get("skills", []),
                                "experience": "",
                                "location": "",
                                "profileUrls": {
                                    "github": profile.get("profileUrl", profile.get("url", ""))
                                },
                                "source": "github",
                                "rawProfile": profile
                            })
                else:
                    Actor.log.info("No GitHub profiles found via Google")
                        
            except Exception as e:
                Actor.log.warning(f"GitHub search failed: {e}")
        
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
        
        Actor.log.info(f"📊 Total candidates from all sources (before dedup): {len(all_candidates)}")
        
        # Deduplicate candidates from multiple sources
        all_candidates = deduplicate_candidates(all_candidates)
        Actor.log.info(f"📊 Unique candidates after deduplication: {len(all_candidates)}")
        
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


def deduplicate_candidates(candidates: list[dict]) -> list[dict]:
    """
    Deduplicate candidates that appear from multiple sources.
    
    Merges profile data when the same person is found on multiple platforms.
    Uses profile URLs and username matching to identify duplicates.
    
    Args:
        candidates: List of candidate dicts from all sources
        
    Returns:
        Deduplicated list with merged profile data
    """
    if not candidates:
        return []
    
    # Track unique candidates by normalized identifiers
    seen_urls = {}  # url -> candidate index
    seen_usernames = {}  # normalized username -> candidate index
    unique_candidates = []
    
    for candidate in candidates:
        # Extract identifiers
        profile_urls = candidate.get("profileUrls", {})
        username = candidate.get("username", "").lower()
        name = candidate.get("name", "").lower().strip()
        
        # Check if we've seen this candidate before
        matched_idx = None
        
        # Match by profile URLs
        for platform, url in profile_urls.items():
            if url:
                normalized_url = normalize_url(url)
                if normalized_url in seen_urls:
                    matched_idx = seen_urls[normalized_url]
                    break
        
        # Match by username (if no URL match)
        if matched_idx is None and username:
            if username in seen_usernames:
                matched_idx = seen_usernames[username]
        
        if matched_idx is not None:
            # Merge with existing candidate
            unique_candidates[matched_idx] = merge_candidates(
                unique_candidates[matched_idx], 
                candidate
            )
        else:
            # New unique candidate
            idx = len(unique_candidates)
            unique_candidates.append(candidate)
            
            # Register identifiers
            for platform, url in profile_urls.items():
                if url:
                    seen_urls[normalize_url(url)] = idx
            if username:
                seen_usernames[username] = idx
    
    return unique_candidates


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    if not url:
        return ""
    
    # Remove protocol, www, trailing slashes
    url = url.lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    
    # Normalize x.com to twitter.com
    url = url.replace('x.com/', 'twitter.com/')
    
    return url


def merge_candidates(existing: dict, new: dict) -> dict:
    """
    Merge two candidate profiles from different sources.
    
    Combines profile URLs and takes best available data for each field.
    
    Args:
        existing: Existing candidate dict
        new: New candidate dict to merge
        
    Returns:
        Merged candidate dict
    """
    merged = existing.copy()
    
    # Merge profile URLs
    existing_urls = merged.get("profileUrls", {})
    new_urls = new.get("profileUrls", {})
    merged["profileUrls"] = {**existing_urls, **new_urls}
    
    # Track sources
    existing_sources = merged.get("sources", [merged.get("source", "unknown")])
    if isinstance(existing_sources, str):
        existing_sources = [existing_sources]
    new_source = new.get("source", "unknown")
    if new_source not in existing_sources:
        existing_sources.append(new_source)
    merged["sources"] = existing_sources
    merged["source"] = "multi"  # Mark as multi-source
    
    # Merge skills (combine and deduplicate)
    existing_skills = set(merged.get("skills", []))
    new_skills = set(new.get("skills", []))
    merged["skills"] = list(existing_skills | new_skills)
    
    # Take non-empty values for other fields
    for field in ["name", "bio", "experience", "location", "company", "email"]:
        if not merged.get(field) and new.get(field):
            merged[field] = new[field]
    
    # Merge stats if available
    if new.get("stats"):
        existing_stats = merged.get("stats", {})
        merged["stats"] = {**existing_stats, **new.get("stats", {})}
    
    # Keep raw profiles from all sources
    if "rawProfiles" not in merged:
        merged["rawProfiles"] = {}
        if merged.get("rawProfile"):
            merged["rawProfiles"][merged.get("source", "unknown")] = merged.pop("rawProfile")
    
    if new.get("rawProfile"):
        merged["rawProfiles"][new.get("source", "unknown")] = new["rawProfile"]
    
    return merged


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


async def search_github_via_google(
    client: ApifyClient,
    query: str,
    max_results: int,
) -> list[dict]:
    """Search Google for GitHub profile URLs."""
    
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

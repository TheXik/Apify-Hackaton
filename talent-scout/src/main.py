"""
Talent Scout - Multi-Source Developer Finder

Combines multi-source scraping (LinkedIn, Twitter, GitHub) with AI-powered candidate ranking.
Searches for developers matching job requirements across multiple platforms.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Dict, Any

from apify import Actor
from apify_client import ApifyClient

from .candidate_ranker import CandidateRanker
from .scrapers import TwitterScraper, GitHubScraper, LinkedInScraper


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
        sources = actor_input.get("sources", ["linkedin", "twitter"])
        
        # Validate required input
        if not job_title:
            await Actor.fail("Missing required input: jobTitle is required")
            return
        
        _log_execution_plan(job_title, required_skills, location, max_candidates, sources, enable_ranking)
        
        all_candidates = []
        
        # Execute Scrapers
        if "linkedin" in sources:
            candidates = await _run_linkedin_search(job_title, location, required_skills, max_candidates)
            all_candidates.extend(candidates)
            
        if "twitter" in sources:
            candidates = await _run_twitter_search(job_title, max_candidates)
            all_candidates.extend(candidates)
            
        if "github" in sources:
            candidates = await _run_github_search(job_title, location, required_skills, max_candidates)
            all_candidates.extend(candidates)
        
        # Check results
        if not all_candidates:
            await _handle_no_results(job_title, sources, location)
            return
        
        Actor.log.info(f"📊 Total candidates from all sources (before dedup): {len(all_candidates)}")
        
        # Deduplicate
        all_candidates = deduplicate_candidates(all_candidates)
        Actor.log.info(f"📊 Unique candidates after deduplication: {len(all_candidates)}")
        
        # AI Ranking
        if enable_ranking and os.environ.get("OPENAI_API_KEY") and job_description:
            await _run_ranking_pipeline(
                all_candidates, 
                job_title, 
                job_description, 
                required_skills, 
                nice_to_have, 
                location, 
                experience_years, 
                top_k,
                sources
            )
        else:
            await _push_unranked_results(all_candidates, job_title, location, sources)


# --- Source Runners ---

async def _run_linkedin_search(job_title: str, location: str, skills: list, max_items: int) -> list:
    """Execute LinkedIn scraping strategy."""
    await Actor.set_status_message("Searching LinkedIn for candidates...")
    try:
        scraper = LinkedInScraper()
        profiles = scraper.search(
            job_title=job_title,
            location=location,
            skills=skills,
            max_items=max_items,
        )
        _log_results("LinkedIn", len(profiles))
        return profiles
    except Exception as e:
        Actor.log.warning(f"LinkedIn search failed: {e}")
        return []


async def _run_twitter_search(job_title: str, max_items: int) -> list:
    """Execute Twitter scraping strategy."""
    await Actor.set_status_message("Searching Twitter for candidates...")
    try:
        scraper = TwitterScraper()
        profiles = scraper.search(
            position=job_title,
            max_items=max_items
        )
        _log_results("Twitter", len(profiles))
        return profiles
    except Exception as e:
        Actor.log.warning(f"Twitter search failed: {e}")
        return []


async def _run_github_search(job_title: str, location: str, skills: list, max_items: int) -> list:
    """Execute GitHub scraping strategy (Google Search -> Enrichment)."""
    await Actor.set_status_message("Searching for GitHub profiles via Google...")
    try:
        scraper = GitHubScraper()
        
        # Step 1: Discovery via Google
        google_profiles = scraper.find_candidates_via_google(
            job_title=job_title,
            skills=skills,
            location=location,
            max_results=max_items
        )
        
        if not google_profiles:
            Actor.log.info("No GitHub profiles found via Google")
            return []
            
        Actor.log.info(f"✅ Found {len(google_profiles)} GitHub URLs via Google")
        
        # Step 2: Enrichment
        await Actor.set_status_message(f"Enriching {len(google_profiles)} GitHub profiles...")
        
        try:
            profile_urls = [p["profileUrl"] for p in google_profiles]
            enriched = scraper.scrape_profiles(profile_urls, max_items)
            
            if enriched:
                _log_results("GitHub", len(enriched))
                return enriched
                
        except Exception as e:
            Actor.log.warning(f"GitHub enrichment failed: {e}")
            
        # Fallback: Use Google results if enrichment fails or returns nothing
        Actor.log.warning("Using Google results as fallback for GitHub")
        return [_convert_google_fallback(p) for p in google_profiles]
        
    except Exception as e:
        Actor.log.warning(f"GitHub search failed: {e}")
        return []


# --- Pipeline Helpers ---

async def _run_ranking_pipeline(
    candidates: list,
    job_title: str,
    job_description: str,
    skills: list,
    nice_to_have: list,
    location: str,
    experience: int,
    top_k: int,
    sources: list
) -> None:
    """Run AI ranking and push results."""
    await Actor.set_status_message(f"Ranking {len(candidates)} candidates with AI...")
    Actor.log.info("🤖 Starting AI ranking...")
    
    try:
        ranker = CandidateRanker(os.environ["OPENAI_API_KEY"])
        job_input = {
            "jobTitle": job_title,
            "jobDescription": job_description,
            "requiredSkills": skills,
            "niceToHave": nice_to_have,
            "location": location or "",
            "experienceYears": experience
        }
        
        ranked = ranker.rank_candidates(job_input, candidates, top_k)
        
        Actor.log.info(f"✅ Ranked {len(ranked)} candidates")
        await _push_results(ranked, job_title, location, sources, ranked=True, total=len(candidates))
        await Actor.set_status_message(f"Done! Ranked {len(ranked)} of {len(candidates)} candidates")
        
    except Exception as e:
        Actor.log.error(f"AI ranking failed: {e}")
        Actor.log.info("Falling back to unranked results...")
        await _push_unranked_results(candidates, job_title, location, sources)


async def _push_unranked_results(candidates: list, job_title: str, location: str, sources: list) -> None:
    """Push candidates without ranking."""
    await _push_results(candidates, job_title, location, sources, ranked=False, total=len(candidates))
    await Actor.set_status_message(f"Done! Found {len(candidates)} candidates (unranked)")


async def _push_results(candidates: list, job_title: str, location: str, sources: list, ranked: bool, total: int) -> None:
    """Push final dataset."""
    await Actor.push_data({
        "jobTitle": job_title,
        "totalFound": total,
        "ranked": ranked,
        "sources": sources,
        "candidates": candidates,
        "metadata": {
            "searchQuery": job_title,
            "location": location,
            "sources": sources,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


async def _handle_no_results(job_title: str, sources: list, location: str) -> None:
    """Handle case where no candidates were found."""
    Actor.log.warning("No candidates found from any source")
    await Actor.push_data({
        "candidates": [],
        "metadata": {
            "totalFound": 0,
            "searchQuery": job_title,
            "location": location,
            "sources": sources,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


def _log_execution_plan(title: str, skills: list, location: str, max_c: int, sources: list, rank: bool) -> None:
    """Log execution parameters."""
    Actor.log.info(f"🎯 Searching for: {title}")
    Actor.log.info(f"🔧 Skills: {', '.join(skills) if skills else 'Any'}")
    Actor.log.info(f"📍 Location: {location or 'Any'}")
    Actor.log.info(f"📊 Max candidates: {max_c}")
    Actor.log.info(f"🔍 Sources: {', '.join(sources)}")
    Actor.log.info(f"🤖 AI Ranking: {'Enabled' if rank else 'Disabled'}")


def _log_results(source: str, count: int) -> None:
    if count > 0:
        Actor.log.info(f"✅ Found {count} profiles from {source}")
    else:
        Actor.log.info(f"No profiles found from {source}")


def _convert_google_fallback(profile: dict) -> dict:
    """Convert Google result to candidate format for fallback."""
    return {
        "name": profile.get("name") or profile.get("username") or "Unknown",
        "bio": profile.get("bio", ""),
        "skills": profile.get("skills", []),
        "experience": "",
        "location": "",
        "profileUrls": {"github": profile.get("profileUrl", profile.get("url", ""))},
        "source": "github",
        "rawProfile": profile
    }


def deduplicate_candidates(candidates: list[dict]) -> list[dict]:
    """
    Deduplicate candidates that appear from multiple sources.
    Uses profile URLs and username matching.
    """
    if not candidates:
        return []
    
    seen_urls = {}  # url -> index
    seen_usernames = {}  # username -> index
    unique_candidates = []
    
    for candidate in candidates:
        profile_urls = candidate.get("profileUrls", {})
        username = candidate.get("username", "").lower()
        
        # Try to find match
        matched_idx = None
        
        # 1. Match by URL
        for url in profile_urls.values():
            if not url: continue
            norm_url = normalize_url(url)
            if norm_url in seen_urls:
                matched_idx = seen_urls[norm_url]
                break
        
        # 2. Match by username
        if matched_idx is None and username:
            matched_idx = seen_usernames.get(username)
            
        if matched_idx is not None:
            # Merge
            unique_candidates[matched_idx] = merge_candidates(
                unique_candidates[matched_idx], candidate
            )
        else:
            # Add new
            idx = len(unique_candidates)
            unique_candidates.append(candidate)
            
            # Register identifiers
            for url in profile_urls.values():
                if url: seen_urls[normalize_url(url)] = idx
            if username: seen_usernames[username] = idx
            
    return unique_candidates


def normalize_url(url: str) -> str:
    """Normalize URL for comparison (remove protocol, www, trailing slash)."""
    if not url: return ""
    url = url.lower()
    url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    url = url.rstrip("/")
    return url.replace("x.com/", "twitter.com/")


def merge_candidates(existing: dict, new: dict) -> dict:
    """Merge two candidate profiles."""
    merged = existing.copy()
    
    # Merge URLs
    merged["profileUrls"] = {**existing.get("profileUrls", {}), **new.get("profileUrls", {})}
    
    # Merge Sources
    sources = set(existing.get("sources", [existing.get("source", "unknown")]))
    if isinstance(sources, str): sources = {sources} # handle legacy
    sources.add(new.get("source", "unknown"))
    merged["sources"] = list(sources)
    merged["source"] = "multi"
    
    # Merge Skills
    all_skills = set(existing.get("skills", []) + new.get("skills", []))
    merged["skills"] = list(all_skills)
    
    # Merge other fields (prefer existing if set, else new)
    for field in ["name", "bio", "experience", "location", "email"]:
        if not merged.get(field) and new.get(field):
            merged[field] = new[field]
            
    # Merge stats
    if new.get("stats"):
        merged["stats"] = {**existing.get("stats", {}), **new.get("stats", {})}
        
    return merged

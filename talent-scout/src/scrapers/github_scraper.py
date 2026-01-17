"""
GitHub Profile Scraper Service.

Scrapes GitHub profiles using the saswave/github-profile-scraper Actor.
Takes profile URLs (from Google search) and enriches them with full profile data.
"""

import os
import re
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from apify_client import ApifyClient


# Actor IDs
GITHUB_ACTOR_ID = "saswave/github-profile-scraper"
GOOGLE_ACTOR_ID = "apify/google-search-scraper"


class GitHubScraper:
    """Scrapes GitHub profiles to extract detailed developer information."""
    
    def __init__(self, apify_token: Optional[str] = None):
        """
        Initialize GitHub scraper.
        
        Args:
            apify_token: Apify API token. If not provided, uses APIFY_TOKEN env var.
        """
        self.apify_token = apify_token or os.environ.get("APIFY_TOKEN")
        if not self.apify_token:
            raise ValueError("APIFY_TOKEN is required")
        
        self.client = ApifyClient(self.apify_token)

    def find_candidates_via_google(
        self,
        job_title: str,
        skills: list[str],
        location: str | None,
        max_results: int = 20
    ) -> list[dict]:
        """
        Search Google for GitHub profiles matching job criteria.
        
        Args:
            job_title: Job title to search for
            skills: List of required skills
            location: Location filter
            max_results: Maximum number of results to return
            
        Returns:
            List of normalized profile objects from Google results
        """
        # Build optimized query
        query = self._build_google_query(job_title, skills, location)
        
        # Calculate pages needed (10 results per page)
        pages_needed = min((max_results + 9) // 10, 5)  # Cap at 5 pages
        
        google_input = {
            "queries": query,
            "maxPagesPerQuery": pages_needed,
            "resultsPerPage": 10,
            "countryCode": "us",
            "languageCode": "en",
        }
        
        try:
            # Run Google Search Actor
            run = self.client.actor(GOOGLE_ACTOR_ID).call(
                run_input=google_input,
                timeout_secs=300,
            )
            
            # Extract and normalize profiles
            profiles = []
            dataset = self.client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                for result in item.get("organicResults", []):
                    url = result.get("url", "")
                    
                    if self._is_github_profile_url(url):
                        profile = self._normalize_google_result(result)
                        profiles.append(profile)
                        
                        if len(profiles) >= max_results:
                            break
                if len(profiles) >= max_results:
                    break
            
            return profiles
            
        except Exception as e:
            print(f"Google Search failed: {e}")
            return []

    def _build_google_query(
        self,
        job_title: str,
        skills: list[str],
        location: str | None,
    ) -> str:
        """Build Google search query."""
        parts = [job_title]
        if skills:
            parts.extend(skills[:3])
        if location:
            parts.append(location)
        
        return " ".join(parts) + " site:github.com"

    def _is_github_profile_url(self, url: str) -> bool:
        """Check if URL is a GitHub user profile."""
        if not url or "github.com" not in url:
            return False
            
        # Exclude common non-profile paths
        excluded = [
            "/orgs/", "/topics/", "/explore", "/trending", "/collections",
            "/sponsors/", "/features/", "/enterprise", "/pricing",
            "/about/", "/github/", "/settings", "/marketplace",
            "/pulls", "/issues", "/actions", "/projects", "/security",
            "/blog/", "/customers/", "/events/", "/readme/"
        ]
        
        if any(path in url.lower() for path in excluded):
            return False
            
        # Match github.com/username
        match = re.match(r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)(?:\?.*)?$", url)
        if match:
            username = match.group(1).lower()
            return username not in ["login", "join", "search", "notifications"]
            
        return False

    def _normalize_google_result(self, result: dict) -> dict:
        """Normalize Google result to GitHub profile format."""
        url = result.get("url", "")
        title = result.get("title", "")
        
        # Extract username
        username = self.extract_username(url)
        
        # Extract name from title
        name = None
        clean_title = re.sub(r"\s*[-·|]\s*GitHub.*$", "", title, flags=re.IGNORECASE)
        clean_title = re.sub(r"\s*\(.*?\)\s*$", "", clean_title)
        if clean_title and " " in clean_title and not clean_title.startswith("@"):
            name = clean_title.strip()
            
        return {
            "source": "github",
            "username": username,
            "name": name,
            "url": url,
            "profileUrl": url,
            "bio": result.get("description", ""),
            "skills": result.get("emphasizedKeywords", []),
            "googlePosition": result.get("position"),
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
        }
    
    def extract_username(self, url: str) -> Optional[str]:
        """
        Extract GitHub username from profile URL.
        
        Args:
            url: GitHub profile URL
            
        Returns:
            Username string or None if not a valid profile URL
        """
        match = re.match(r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)(?:\?.*)?$', url)
        if match:
            username = match.group(1)
            # Exclude non-user paths
            excluded = ['login', 'join', 'search', 'notifications', 'settings', 
                       'marketplace', 'explore', 'topics', 'trending', 'collections',
                       'sponsors', 'features', 'enterprise', 'pricing', 'about']
            if username.lower() not in excluded:
                return username
        return None
    
    def scrape_profiles(
        self,
        profile_urls: list[str],
        max_items: int = 20
    ) -> list[dict]:
        """
        Scrape GitHub profiles from URLs.
        
        Args:
            profile_urls: List of GitHub profile URLs to scrape
            max_items: Maximum number of profiles to return
            
        Returns:
            List of enriched profile data
        """
        if not profile_urls:
            return []
        
        # Filter valid URLs
        valid_urls = []
        for url in profile_urls[:max_items]:
            if self.extract_username(url):
                valid_urls.append(url)
        
        if not valid_urls:
            return []
        
        # Prepare Actor input
        # saswave/github-profile-scraper expects "peoples_links" as a list of URLs
        actor_input = {
            "peoples_links": valid_urls,
        }
        
        try:
            # Run the GitHub Profile Scraper Actor
            run = self.client.actor(GITHUB_ACTOR_ID).call(
                run_input=actor_input,
                timeout_secs=300,
            )
            
            # Collect results
            profiles = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                profile = self._normalize_profile(item)
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"GitHub profile scraping failed: {e}")
            return []
    
    def _normalize_profile(self, raw_profile: dict) -> dict:
        """
        Normalize GitHub profile data to standard candidate format.
        
        Args:
            raw_profile: Raw profile data from saswave/github-profile-scraper
            
        Returns:
            Normalized profile dict
        """
        username = raw_profile.get("username") or ""
        # If username is missing but 'user' url is present, extract it
        if not username and raw_profile.get("user"):
             username_match = re.search(r"github\.com/([^/]+)", raw_profile.get("user", ""))
             if username_match:
                 username = username_match.group(1)

        # Extract languages/skills from pinned repos
        skills = self._extract_skills(raw_profile)
        
        # Build experience string from stats and achievements
        experience = self._build_experience_string(raw_profile)
        
        # URLs
        profile_urls = {
            "github": raw_profile.get("user") or f"https://github.com/{username}" if username else "",
        }
        if raw_profile.get("X"):
            profile_urls["twitter"] = raw_profile.get("X")
        if raw_profile.get("LinkedIn"):
            profile_urls["linkedin"] = raw_profile.get("LinkedIn")
            
        # Websites / Blog
        websites = raw_profile.get("websites", [])
        blog = websites[0] if websites else ""
        
        # Email
        emails = raw_profile.get("emails", [])
        email = emails[0] if emails else ""

        # Location
        location = raw_profile.get("location", "")
        
        # Organization / Company
        company = raw_profile.get("organization", "")

        # Stats normalization
        # Some fields might be strings like "34.9k"
        def parse_stat(val):
            if isinstance(val, int): return val
            if not val: return 0
            val = str(val).lower().replace(",", "")
            if "k" in val:
                return int(float(val.replace("k", "")) * 1000)
            return int(val) if val.isdigit() else 0

        stats = {
            "followers": parse_stat(raw_profile.get("followers", "0")),
            "following": parse_stat(raw_profile.get("following", "0")),
            "contributions": parse_stat(raw_profile.get("last_year_contribution_number", "0")),
        }

        # Repositories
        repositories = self._extract_top_repos(raw_profile)

        return {
            "name": raw_profile.get("name") or username,
            "username": username,
            "bio": raw_profile.get("bio", ""),
            "location": location,
            "company": company,
            "email": email,
            "blog": blog,
            "skills": skills,
            "experience": experience,
            "profileUrls": profile_urls,
            "source": "github",
            "stats": stats,
            "repositories": repositories,
            "achievements": raw_profile.get("achievements", []),
            "rawProfile": raw_profile,
        }
    
    def _extract_skills(self, profile: dict) -> list[str]:
        """Extract programming languages/skills from pinned repositories."""
        skills = set()
        
        # Pinned repos is a list of dicts
        pinned_repos = profile.get("pinned_repos", [])
        for repo in pinned_repos:
            # "languages" is a list of strings
            langs = repo.get("languages", [])
            for lang in langs:
                skills.add(lang)
            
            # Also check description for keywords
            description = repo.get("description", "").lower()
            keywords = ['python', 'javascript', 'typescript', 'react', 'nodejs', 
                       'docker', 'kubernetes', 'aws', 'machine learning', 'ai',
                       'deep learning', 'tensorflow', 'pytorch', 'rust', 'go',
                       'java', 'c#', 'c++', 'ruby', 'php', 'swift', 'kotlin']
            for kw in keywords:
                if kw in description:
                    # special case for c# and c++ to avoid cleaning issues later if needed, 
                    # but here we just add string
                    if kw == 'machine learning': skills.add('Machine Learning')
                    elif kw == 'deep learning': skills.add('Deep Learning')
                    else: skills.add(kw.title())
        
        return list(skills)
    
    def _build_experience_string(self, profile: dict) -> str:
        """Build experience summary from GitHub stats."""
        parts = []
        
        first_year = profile.get("first_year_commit")
        if first_year:
            parts.append(f"Coding since {first_year}")
            
        contributions = profile.get("last_year_contribution_number")
        if contributions:
            parts.append(f"{contributions} contributions last year")
            
        followers = profile.get("followers")
        if followers:
             parts.append(f"{followers} followers")

        achievements = profile.get("achievements", [])
        if achievements:
             # Take top 3 achievements
             top_achievements = achievements[:3]
             parts.append(f"Achievements: {', '.join(top_achievements)}")
        
        return ", ".join(parts) if parts else ""
    
    def _extract_top_repos(self, profile: dict, max_repos: int = 5) -> list[dict]:
        """Extract top repositories (pinned repos)."""
        pinned_repos = profile.get("pinned_repos", [])
        
        top_repos = []
        for repo in pinned_repos[:max_repos]:
            
            # Stars can be "83.2k"
            raw_stars = repo.get("stars", "0")
            stars = 0
            if isinstance(raw_stars, int):
                stars = raw_stars
            else:
                raw_stars_clean = str(raw_stars).lower().replace(",", "")
                if "k" in raw_stars_clean:
                     try:
                        stars = int(float(raw_stars_clean.replace("k", "")) * 1000)
                     except: 
                        stars = 0
                elif raw_stars_clean.isdigit():
                    stars = int(raw_stars_clean)
            
            # Forks can be "12.5k"
            raw_forks = repo.get("forks", "0")
            forks = 0
            if isinstance(raw_forks, int):
                forks = raw_forks
            else:
                raw_forks_clean = str(raw_forks).lower().replace(",", "")
                if "k" in raw_forks_clean:
                    try:
                        forks = int(float(raw_forks_clean.replace("k", "")) * 1000)
                    except:
                        forks = 0
                elif raw_forks_clean.isdigit():
                    forks = int(raw_forks_clean)

            top_repos.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", ""),
                "languages": repo.get("languages", []),  # Keep list for raw
                "language": repo.get("languages", [""])[0] if repo.get("languages") else "", # Primary language
                "stars": stars,
                "forks": forks,
                "url": repo.get("url", ""),
            })
        
        return top_repos


# Convenience function for direct use
def scrape_github_profiles(
    profile_urls: list[str],
    max_items: int = 20,
    apify_token: Optional[str] = None
) -> list[dict]:
    """
    Scrape GitHub profiles from URLs.
    
    Args:
        profile_urls: List of GitHub profile URLs
        max_items: Maximum number of profiles to scrape
        apify_token: Optional Apify token (uses env var if not provided)
        
    Returns:
        List of profile data
    """
    scraper = GitHubScraper(apify_token)
    return scraper.scrape_profiles(profile_urls, max_items)

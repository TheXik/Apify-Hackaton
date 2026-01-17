"""
GitHub Profile Scraper Service.

Scrapes GitHub profiles using the bebity/github-profile-scraper Actor.
Takes profile URLs (from Google search) and enriches them with full profile data.
"""

import os
import re
from typing import Optional

from apify_client import ApifyClient


# GitHub Profile Scraper Actor ID
GITHUB_ACTOR_ID = "bebity/github-profile-scraper"


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
        
        # Extract usernames from URLs
        usernames = []
        url_to_username = {}
        
        for url in profile_urls[:max_items]:
            username = self.extract_username(url)
            if username:
                usernames.append(username)
                url_to_username[url] = username
        
        if not usernames:
            return []
        
        # Prepare Actor input
        actor_input = {
            "usernames": usernames,
            "includeReadme": False,
            "includeRepositories": True,
            "maxRepositories": 10,
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
            raw_profile: Raw profile data from Actor
            
        Returns:
            Normalized profile dict
        """
        username = raw_profile.get("login") or raw_profile.get("username", "")
        
        # Extract languages/skills from repositories
        skills = self._extract_skills(raw_profile)
        
        # Build experience string from contribution stats
        experience = self._build_experience_string(raw_profile)
        
        return {
            "name": raw_profile.get("name") or username,
            "username": username,
            "bio": raw_profile.get("bio", ""),
            "location": raw_profile.get("location", ""),
            "company": raw_profile.get("company", ""),
            "email": raw_profile.get("email", ""),
            "blog": raw_profile.get("blog", ""),
            "skills": skills,
            "experience": experience,
            "profileUrls": {
                "github": f"https://github.com/{username}" if username else "",
            },
            "source": "github",
            "stats": {
                "publicRepos": raw_profile.get("public_repos", 0),
                "followers": raw_profile.get("followers", 0),
                "following": raw_profile.get("following", 0),
                "contributions": raw_profile.get("contributions", 0),
            },
            "repositories": self._extract_top_repos(raw_profile),
            "rawProfile": raw_profile,
        }
    
    def _extract_skills(self, profile: dict) -> list[str]:
        """Extract programming languages/skills from repositories."""
        skills = set()
        
        # Get languages from repositories
        repos = profile.get("repositories", [])
        for repo in repos:
            language = repo.get("language")
            if language:
                skills.add(language)
            
            # Also check topics/tags
            topics = repo.get("topics", [])
            for topic in topics:
                # Filter common tech-related topics
                if topic in ['python', 'javascript', 'typescript', 'react', 'nodejs', 
                            'docker', 'kubernetes', 'aws', 'machine-learning', 'ai',
                            'deep-learning', 'tensorflow', 'pytorch', 'rust', 'go',
                            'java', 'csharp', 'cpp', 'ruby', 'php', 'swift', 'kotlin']:
                    skills.add(topic.title())
        
        return list(skills)
    
    def _build_experience_string(self, profile: dict) -> str:
        """Build experience summary from GitHub stats."""
        parts = []
        
        repos = profile.get("public_repos", 0)
        if repos:
            parts.append(f"{repos} public repos")
        
        followers = profile.get("followers", 0)
        if followers:
            parts.append(f"{followers} followers")
        
        contributions = profile.get("contributions", 0)
        if contributions:
            parts.append(f"{contributions} contributions")
        
        return ", ".join(parts) if parts else ""
    
    def _extract_top_repos(self, profile: dict, max_repos: int = 5) -> list[dict]:
        """Extract top repositories by stars."""
        repos = profile.get("repositories", [])
        
        # Sort by stars
        sorted_repos = sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)
        
        top_repos = []
        for repo in sorted_repos[:max_repos]:
            top_repos.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "url": repo.get("html_url", ""),
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

"""
LinkedIn Profile Scraper Service.

Searches LinkedIn for candidates using the harvestapi/linkedin-profile-search Actor.
Extracts profile information matching job-related queries.
"""

import os
from typing import Optional

from apify_client import ApifyClient


# LinkedIn Search Actor ID
LINKEDIN_ACTOR_ID = "harvestapi/linkedin-profile-search"


class LinkedInScraper:
    """Searches LinkedIn for candidate profiles based on job criteria."""
    
    def __init__(self, apify_token: Optional[str] = None):
        """
        Initialize LinkedIn scraper.
        
        Args:
            apify_token: Apify API token. If not provided, uses APIFY_TOKEN env var.
        """
        self.apify_token = apify_token or os.environ.get("APIFY_TOKEN")
        if not self.apify_token:
            raise ValueError("APIFY_TOKEN is required")
        
        self.client = ApifyClient(self.apify_token)
    
    def search(
        self,
        job_title: str,
        location: Optional[str] = None,
        skills: Optional[list[str]] = None,
        max_items: int = 20
    ) -> list[dict]:
        """
        Search LinkedIn for candidates matching the criteria.
        
        Args:
            job_title: Job title or position to search for
            location: Geographic location filter
            skills: List of required skills
            max_items: Maximum number of profiles to fetch
            
        Returns:
            List of normalized candidate profiles
        """
        # Build search query
        search_query = self._build_search_query(job_title, skills)
        
        # Prepare Actor input
        # Validated schema: keywords (string) + locations (array)
        actor_input = {
            "keywords": search_query,
            "locations": [location] if location else [],
            "maxItems": max_items,
        }
        
        try:
            # Run the LinkedIn Scraper Actor
            run = self.client.actor(LINKEDIN_ACTOR_ID).call(
                run_input=actor_input,
                timeout_secs=300,
            )
            
            # Get results from dataset
            profiles = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                profile = self._normalize_profile(item)
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"LinkedIn search failed: {e}")
            return []
    
    def _build_search_query(self, job_title: str, skills: Optional[list[str]] = None) -> str:
        """Build LinkedIn search query string."""
        parts = [job_title]
        
        if skills:
            # Add top 3 skills to query
            parts.extend(skills[:3])
        
        return " ".join(parts)
    
    def _normalize_profile(self, raw_profile: dict) -> dict:
        """
        Normalize LinkedIn profile data to standard candidate format.
        
        Args:
            raw_profile: Raw profile data from Actor
            
        Returns:
            Normalized profile dict
        """
        # Handle different field names from different Actor versions
        # Handle different field names from different Actor versions
        name = (
            raw_profile.get("fullName") or 
            raw_profile.get("name") or 
            f"{raw_profile.get('firstName', '')} {raw_profile.get('lastName', '')}".strip() or
            "Unknown"
        )
        
        profile_url = (
            raw_profile.get("profileUrl") or 
            raw_profile.get("url") or 
            raw_profile.get("linkedinUrl") or
            ""
        )
        
        headline = (
            raw_profile.get("headline") or 
            raw_profile.get("title") or 
            raw_profile.get("occupation") or
            ""
        )
        
        # Extract skills (handle both list of strings and list of dicts)
        skills = raw_profile.get("skills", [])
        if isinstance(skills, list) and skills:
            if isinstance(skills[0], dict):
                skills = [s.get("name", "") for s in skills if s.get("name")]
            # Filter empty strings
            skills = [s for s in skills if s]
        
        # Build experience summary
        experience = self._build_experience_string(raw_profile)
        
        return {
            "name": name,
            "bio": headline,
            "skills": skills if isinstance(skills, list) else [],
            "experience": experience,
            "location": raw_profile.get("location", raw_profile.get("geoLocation", "")),
            "profileUrls": {
                "linkedin": profile_url,
            },
            "source": "linkedin",
            "company": raw_profile.get("company", raw_profile.get("currentCompany", "")),
            "connections": raw_profile.get("connections", raw_profile.get("connectionsCount", 0)),
            "rawProfile": raw_profile,
        }
    
    def _build_experience_string(self, profile: dict) -> str:
        """Build experience summary from LinkedIn profile data."""
        parts = []
        
        # Current position
        current = profile.get("currentPosition") or profile.get("position")
        if current:
            if isinstance(current, dict):
                title = current.get("title", "")
                company = current.get("company", "")
                if title and company:
                    parts.append(f"Currently {title} at {company}")
                elif title:
                    parts.append(f"Currently {title}")
            else:
                parts.append(str(current))
        
        # Experience list
        experiences = profile.get("experience", profile.get("positions", []))
        if experiences and isinstance(experiences, list):
            num_roles = len(experiences)
            if num_roles > 0:
                parts.append(f"{num_roles} previous role(s)")
        
        return ". ".join(parts) if parts else ""


# Convenience function for direct use
def search_linkedin_candidates(
    job_title: str,
    location: Optional[str] = None,
    skills: Optional[list[str]] = None,
    max_items: int = 20,
    apify_token: Optional[str] = None
) -> list[dict]:
    """
    Search LinkedIn for candidates matching job criteria.
    
    Args:
        job_title: Job title to search for
        location: Geographic location filter
        skills: List of required skills
        max_items: Maximum number of profiles to fetch
        apify_token: Optional Apify token (uses env var if not provided)
        
    Returns:
        List of candidate profiles
    """
    scraper = LinkedInScraper(apify_token)
    return scraper.search(job_title, location, skills, max_items)

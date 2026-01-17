"""
Twitter Scraper Service.

Scrapes Twitter for candidates using the Easy Twitter Search Scraper Actor.
Extracts profile information from tweets matching job-related queries.
"""

import re
import os
from typing import Optional

from apify_client import ApifyClient


# Twitter Search Actor ID
TWITTER_ACTOR_ID = "web.harvester/easy-twitter-search-scraper"


class TwitterScraper:
    """Scrapes Twitter for candidates based on job-related queries."""
    
    def __init__(self, apify_token: Optional[str] = None):
        """
        Initialize Twitter scraper.
        
        Args:
            apify_token: Apify API token. If not provided, uses APIFY_TOKEN env var.
        """
        self.apify_token = apify_token or os.environ.get("APIFY_TOKEN")
        if not self.apify_token:
            raise ValueError("APIFY_TOKEN is required")
        
        self.client = ApifyClient(self.apify_token)
    
    def build_search_query(self, position: str) -> str:
        """
        Build a Twitter search query for finding candidates.
        
        Args:
            position: The job position to search for (e.g., "AI ML Engineer")
            
        Returns:
            Search query string (e.g., "Hey, I'm an AI ML Engineer")
        """
        # Handle a/an grammar
        first_letter = position.strip()[0].lower() if position.strip() else ''
        article = "an" if first_letter in 'aeiou' else "a"
        
        return f"Hey, I'm {article} {position}"
    
    def search(
        self, 
        position: str,
        max_items: int = 50,
        custom_query: Optional[str] = None
    ) -> list[dict]:
        """
        Search Twitter for candidates matching the position.
        
        Args:
            position: Job position to search for
            max_items: Maximum number of tweets to fetch
            custom_query: Optional custom search query (overrides position-based query)
            
        Returns:
            List of extracted candidate profiles
        """
        # Build search query
        search_query = custom_query or self.build_search_query(position)
        
        # Prepare Actor input
        actor_input = {
            "searchQueries": [search_query],
            "tweetsDesired": max_items,
            "maxItems": max_items,
        }
        
        try:
            # Run the Twitter search Actor
            run = self.client.actor(TWITTER_ACTOR_ID).call(run_input=actor_input)
            
            # Get results from dataset
            tweets = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                tweets.append(item)
            
            # Extract candidate profiles from tweets
            candidates = self._extract_candidates(tweets)
            
            return candidates
            
        except Exception as e:
            print(f"Twitter search failed: {e}")
            return []
    
    def _extract_candidates(self, tweets: list[dict]) -> list[dict]:
        """
        Extract candidate profiles from tweet data.
        
        Args:
            tweets: Raw tweet data from the Actor
            
        Returns:
            List of candidate profiles with standardized format
        """
        candidates = []
        seen_urls = set()
        
        for tweet in tweets:
            tweet_url = tweet.get("url", "")
            
            # Skip duplicates
            if tweet_url in seen_urls:
                continue
            seen_urls.add(tweet_url)
            
            # Extract profile URL from tweet URL
            profile_url = self._extract_profile_url(tweet_url)
            
            # Extract name from tweet text if possible
            name = self._extract_name_from_text(tweet.get("text", ""))
            
            # Extract username from URL
            username = self._extract_username(tweet_url)
            
            candidate = {
                "name": name or username or "Unknown",
                "username": username,
                "bio": tweet.get("text", ""),
                "avatar": tweet.get("avatar", ""),
                "profileUrls": {
                    "twitter": profile_url,
                    "tweet": tweet_url
                },
                "source": "twitter",
                "engagement": {
                    "likes": tweet.get("likes", 0),
                    "retweets": tweet.get("retweets", 0),
                    "replies": tweet.get("replies", 0),
                },
                "timestamp": tweet.get("timestamp", ""),
                "searchQuery": tweet.get("searchQuery", ""),
            }
            
            # Try to extract additional info from tweet text
            extracted = self._extract_info_from_text(tweet.get("text", ""))
            if extracted.get("skills"):
                candidate["skills"] = extracted["skills"]
            if extracted.get("experience"):
                candidate["experience"] = extracted["experience"]
            
            candidates.append(candidate)
        
        return candidates
    
    def _extract_profile_url(self, tweet_url: str) -> str:
        """Extract Twitter profile URL from tweet URL."""
        # Tweet URL format: https://x.com/username/status/123456
        match = re.match(r'https?://(?:x\.com|twitter\.com)/([^/]+)', tweet_url)
        if match:
            username = match.group(1)
            return f"https://x.com/{username}"
        return ""
    
    def _extract_username(self, tweet_url: str) -> str:
        """Extract username from tweet URL."""
        match = re.match(r'https?://(?:x\.com|twitter\.com)/([^/]+)', tweet_url)
        if match:
            return match.group(1)
        return ""
    
    def _extract_name_from_text(self, text: str) -> str:
        """
        Try to extract person's name from tweet text.
        
        Looks for patterns like:
        - "I'm [Name]"
        - "Hey! I'm [Name]"
        - "[Name] here"
        """
        patterns = [
            r"(?:I'm|I am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",  # "I'm John Smith"
            r"^(?:Hey[!,]?\s*)?(?:I'm|I am)\s+([A-Z][a-z]+)",    # "Hey! I'm John"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+here",           # "John Smith here"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if name.lower() not in ['an', 'a', 'the', 'looking', 'hiring', 'open']:
                    return name
        
        return ""
    
    def _extract_info_from_text(self, text: str) -> dict:
        """
        Extract skills and experience from tweet text.
        """
        result = {"skills": [], "experience": ""}
        
        # Common tech skills to look for
        skill_patterns = [
            r'\b(Python|JavaScript|TypeScript|React|Node\.js|AWS|Docker|Kubernetes)\b',
            r'\b(ML|AI|NLP|Computer Vision|LLM|RAG|LangChain)\b',
            r'\b(TensorFlow|PyTorch|Scikit-learn|Pandas)\b',
        ]
        
        skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        result["skills"] = list(skills)
        
        # Look for years of experience
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience)?', text, re.IGNORECASE)
        if exp_match:
            result["experience"] = f"{exp_match.group(1)} years"
        
        return result


# Convenience function for direct use
def search_twitter_candidates(
    position: str,
    max_items: int = 50,
    apify_token: Optional[str] = None
) -> list[dict]:
    """
    Search Twitter for candidates matching a job position.
    
    Args:
        position: Job position to search for (e.g., "AI ML Engineer")
        max_items: Maximum number of tweets to fetch
        apify_token: Optional Apify token (uses env var if not provided)
        
    Returns:
        List of candidate profiles
    """
    scraper = TwitterScraper(apify_token)
    return scraper.search(position, max_items)

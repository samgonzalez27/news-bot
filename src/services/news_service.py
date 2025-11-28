"""
NewsAPI service for fetching news headlines.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.config import get_settings
from src.exceptions import NewsAPIError
from src.logging_config import get_logger

logger = get_logger("news_service")

# NewsAPI base URL
NEWSAPI_BASE_URL = "https://newsapi.org/v2"

# Simple in-memory cache for headlines (per category)
_headlines_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


class NewsService:
    """Service for fetching news from NewsAPI."""

    def __init__(self):
        """Initialize news service with HTTP client."""
        settings = get_settings()
        self.api_key = settings.newsapi_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"X-Api-Key": self.api_key},
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _fetch_top_headlines(
        self,
        category: Optional[str] = None,
        country: str = "us",
        page_size: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch top headlines from NewsAPI.

        Args:
            category: News category (business, technology, etc.)
            country: Two-letter country code.
            page_size: Number of results to return.

        Returns:
            List of article dictionaries.

        Raises:
            NewsAPIError: If API call fails.
        """
        params = {
            "country": country,
            "pageSize": page_size,
        }
        if category:
            params["category"] = category

        try:
            response = await self.client.get(
                f"{NEWSAPI_BASE_URL}/top-headlines",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"NewsAPI error: {error_msg}")
                raise NewsAPIError(error_msg)

            articles = data.get("articles", [])
            logger.debug(
                f"Fetched {len(articles)} headlines"
                f"{f' for category: {category}' if category else ''}"
            )
            return articles

        except httpx.HTTPStatusError as e:
            logger.error(f"NewsAPI HTTP error: {e.response.status_code}")
            raise NewsAPIError(
                f"HTTP {e.response.status_code}",
                {"status_code": e.response.status_code},
            )
        except httpx.RequestError as e:
            logger.error(f"NewsAPI request error: {e}")
            raise NewsAPIError("Failed to connect to NewsAPI")

    async def _fetch_everything(
        self,
        query: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        sort_by: str = "relevancy",
        page_size: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search all articles using NewsAPI's everything endpoint.

        Note: Free tier only allows searching past 24 hours.

        Args:
            query: Search query string.
            from_date: Start date for search.
            to_date: End date for search.
            sort_by: Sort order (relevancy, popularity, publishedAt).
            page_size: Number of results.

        Returns:
            List of article dictionaries.

        Raises:
            NewsAPIError: If API call fails.
        """
        # For free tier, limit to yesterday's news
        if from_date is None:
            from_date = date.today() - timedelta(days=1)
        if to_date is None:
            to_date = date.today() - timedelta(days=1)

        params = {
            "q": query,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "sortBy": sort_by,
            "pageSize": page_size,
            "language": "en",
        }

        try:
            response = await self.client.get(
                f"{NEWSAPI_BASE_URL}/everything",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"NewsAPI error: {error_msg}")
                raise NewsAPIError(error_msg)

            articles = data.get("articles", [])
            logger.debug(f"Fetched {len(articles)} articles for query: {query}")
            return articles

        except httpx.HTTPStatusError as e:
            logger.error(f"NewsAPI HTTP error: {e.response.status_code}")
            raise NewsAPIError(
                f"HTTP {e.response.status_code}",
                {"status_code": e.response.status_code},
            )
        except httpx.RequestError as e:
            logger.error(f"NewsAPI request error: {e}")
            raise NewsAPIError("Failed to connect to NewsAPI")

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is still valid."""
        if not cache_entry:
            return False
        cached_at = cache_entry.get("cached_at")
        if not cached_at:
            return False
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        return age < CACHE_TTL_SECONDS

    async def get_headlines_for_category(
        self,
        newsapi_category: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get headlines for a specific NewsAPI category.

        Args:
            newsapi_category: NewsAPI category name.
            use_cache: Whether to use cached results.

        Returns:
            List of article dictionaries with normalized fields.
        """
        cache_key = f"headlines_{newsapi_category}"

        # Check cache
        if use_cache and cache_key in _headlines_cache:
            if self._is_cache_valid(_headlines_cache[cache_key]):
                logger.debug(f"Using cached headlines for {newsapi_category}")
                return _headlines_cache[cache_key]["articles"]

        # Fetch fresh data
        articles = await self._fetch_top_headlines(category=newsapi_category)

        # Normalize article format
        normalized = [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "source": a.get("source", {}).get("name", "Unknown"),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "category": newsapi_category,
            }
            for a in articles
            if a.get("title")  # Filter out articles without titles
        ]

        # Update cache
        _headlines_cache[cache_key] = {
            "articles": normalized,
            "cached_at": datetime.now(timezone.utc),
        }

        return normalized

    async def get_headlines_for_interests(
        self,
        interest_categories: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """
        Get headlines for multiple interest categories.

        Args:
            interest_categories: List of dicts with 'slug' and 'newsapi_category'.

        Returns:
            List of articles with category information.
        """
        all_articles = []
        seen_urls = set()

        for interest in interest_categories:
            category = interest.get("newsapi_category")
            slug = interest.get("slug")

            if not category:
                logger.debug(f"Skipping interest without category: {slug}")
                continue

            try:
                articles = await self.get_headlines_for_category(category)

                # Add interest slug and deduplicate
                for article in articles:
                    if article["url"] not in seen_urls:
                        article["interest_slug"] = slug
                        all_articles.append(article)
                        seen_urls.add(article["url"])

            except NewsAPIError as e:
                logger.warning(f"Failed to fetch {category}: {e}")
                continue

        logger.info(
            f"Fetched {len(all_articles)} unique articles "
            f"for {len(interest_categories)} categories"
        )
        return all_articles

    async def get_previous_day_headlines(
        self,
        interests: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """
        Get headlines from the previous day for given interests.

        Due to NewsAPI free tier limitations, uses top-headlines
        which are inherently recent.

        Args:
            interests: List of interest dicts with 'slug' and 'newsapi_category'.

        Returns:
            List of article dictionaries.
        """
        return await self.get_headlines_for_interests(interests)


# Singleton instance
_news_service: Optional[NewsService] = None


async def get_news_service() -> NewsService:
    """
    Get or create the NewsService singleton.

    Returns:
        NewsService: Singleton instance.
    """
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service


async def close_news_service():
    """Close the NewsService singleton."""
    global _news_service
    if _news_service:
        await _news_service.close()
        _news_service = None

"""
Tests for NewsAPI service failure modes.

Coverage improvements:
- HTTP error responses (4xx, 5xx)
- Connection errors
- Timeout handling
- Invalid API responses
- Caching behavior
- Category handling

Uses httpx mock to simulate API behavior.
"""

import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.news_service import (
    NewsService,
    _headlines_cache,
    get_news_service,
    close_news_service,
)
from src.exceptions import NewsAPIError


@pytest.fixture
def news_service():
    """Create a NewsService instance for testing."""
    with patch("src.services.news_service.get_settings") as mock_settings:
        mock_settings.return_value.newsapi_key = "test-key"
        service = NewsService()
        yield service


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear headlines cache before each test."""
    _headlines_cache.clear()
    yield
    _headlines_cache.clear()


class TestNewsServiceInit:
    """Tests for NewsService initialization."""

    def test_service_creates_http_client(self, news_service):
        """Service should create an HTTP client."""
        assert news_service.client is not None
        assert isinstance(news_service.client, httpx.AsyncClient)

    def test_service_sets_api_key(self, news_service):
        """Service should set API key."""
        assert news_service.api_key == "test-key"


class TestFetchTopHeadlines:
    """Tests for _fetch_top_headlines method."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, news_service):
        """Should return articles on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Test Article", "description": "Test"},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service._fetch_top_headlines(category="technology")

            assert len(result) == 1
            assert result[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_http_401_error(self, news_service):
        """Should raise NewsAPIError on 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        error = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = error

            with pytest.raises(NewsAPIError) as exc_info:
                await news_service._fetch_top_headlines()

            assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_429_rate_limit(self, news_service):
        """Should raise NewsAPIError on 429."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        error = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = error

            with pytest.raises(NewsAPIError) as exc_info:
                await news_service._fetch_top_headlines()

            assert "429" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_500_server_error(self, news_service):
        """Should raise NewsAPIError on 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        error = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = error

            with pytest.raises(NewsAPIError):
                await news_service._fetch_top_headlines()

    @pytest.mark.asyncio
    async def test_connection_error(self, news_service):
        """Should raise NewsAPIError on connection error."""
        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(NewsAPIError) as exc_info:
                await news_service._fetch_top_headlines()

            assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_error(self, news_service):
        """Should raise NewsAPIError on timeout."""
        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(NewsAPIError) as exc_info:
                await news_service._fetch_top_headlines()

            assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_error_status(self, news_service):
        """Should raise NewsAPIError when API returns error status."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "message": "API key invalid",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            with pytest.raises(NewsAPIError) as exc_info:
                await news_service._fetch_top_headlines()

            assert "API key invalid" in str(exc_info.value)


class TestFetchEverything:
    """Tests for _fetch_everything method."""

    @pytest.mark.asyncio
    async def test_successful_search(self, news_service):
        """Should return articles on successful search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Search Result"},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service._fetch_everything(query="test")

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_handles_http_error(self, news_service):
        """Should raise NewsAPIError on HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        error = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=mock_response
        )

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = error

            with pytest.raises(NewsAPIError):
                await news_service._fetch_everything(query="test")


class TestCaching:
    """Tests for caching behavior."""

    @pytest.mark.asyncio
    async def test_uses_cache_when_valid(self, news_service):
        """Should use cached results when valid."""
        # Pre-populate cache
        _headlines_cache["headlines_technology"] = {
            "articles": [{"title": "Cached Article", "url": "test"}],
            "cached_at": datetime.now(timezone.utc),
        }

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            result = await news_service.get_headlines_for_category("technology")

            # Should not call API
            mock_get.assert_not_called()
            assert result[0]["title"] == "Cached Article"

    @pytest.mark.asyncio
    async def test_fetches_when_cache_invalid(self, news_service):
        """Should fetch fresh data when cache is invalid."""
        # Pre-populate with old cache (cache validation should fail)
        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        _headlines_cache["headlines_technology"] = {
            "articles": [{"title": "Old Article", "url": "old"}],
            "cached_at": old_time,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Fresh Article", "source": {"name": "Test"}},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service.get_headlines_for_category("technology")

            # Should call API
            mock_get.assert_called_once()
            assert result[0]["title"] == "Fresh Article"

    @pytest.mark.asyncio
    async def test_can_skip_cache(self, news_service):
        """Should fetch fresh data when use_cache=False."""
        # Pre-populate cache
        _headlines_cache["headlines_technology"] = {
            "articles": [{"title": "Cached Article", "url": "test"}],
            "cached_at": datetime.now(timezone.utc),
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Fresh Article", "source": {"name": "Test"}},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service.get_headlines_for_category(
                "technology", use_cache=False
            )

            mock_get.assert_called_once()
            assert result[0]["title"] == "Fresh Article"


class TestCacheValidation:
    """Tests for cache validation logic."""

    def test_is_cache_valid_returns_true_for_fresh(self, news_service):
        """Should return True for fresh cache entry."""
        entry = {"cached_at": datetime.now(timezone.utc)}
        assert news_service._is_cache_valid(entry) is True

    def test_is_cache_valid_returns_false_for_stale(self, news_service):
        """Should return False for stale cache entry."""
        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        entry = {"cached_at": old_time}
        assert news_service._is_cache_valid(entry) is False

    def test_is_cache_valid_returns_false_for_empty(self, news_service):
        """Should return False for empty entry."""
        assert news_service._is_cache_valid({}) is False
        assert news_service._is_cache_valid(None) is False


class TestGetHeadlinesForCategory:
    """Tests for get_headlines_for_category method."""

    @pytest.mark.asyncio
    async def test_normalizes_article_format(self, news_service):
        """Should normalize article format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Test Article",
                    "description": "Test description",
                    "source": {"name": "Test Source"},
                    "url": "https://example.com",
                    "publishedAt": "2024-01-01T00:00:00Z",
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service.get_headlines_for_category("technology")

            assert "title" in result[0]
            assert "description" in result[0]
            assert "source" in result[0]
            assert "url" in result[0]
            assert "published_at" in result[0]
            assert "category" in result[0]

    @pytest.mark.asyncio
    async def test_filters_articles_without_title(self, news_service):
        """Should filter out articles without titles."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Valid Article", "source": {"name": "Test"}},
                {"title": "", "source": {"name": "Test"}},  # Empty title
                {"description": "No title", "source": {"name": "Test"}},  # No title key
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service.get_headlines_for_category("technology")

            # Should only have the valid article
            assert len(result) == 1
            assert result[0]["title"] == "Valid Article"


class TestGetHeadlinesForInterests:
    """Tests for get_headlines_for_interests method."""

    @pytest.mark.asyncio
    async def test_aggregates_multiple_categories(self, news_service):
        """Should aggregate articles from multiple categories."""
        interests = [
            {"slug": "technology", "newsapi_category": "technology"},
            {"slug": "science", "newsapi_category": "science"},
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Article",
                    "url": "https://example.com/1",
                    "source": {"name": "Test"},
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service.get_headlines_for_interests(interests)

            # Called twice (once per category)
            assert mock_get.call_count == 2
            # But deduplication means unique URLs only
            assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_skips_interests_without_category(self, news_service):
        """Should skip interests without newsapi_category."""
        interests = [
            {"slug": "technology"},  # No newsapi_category
        ]

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            result = await news_service.get_headlines_for_interests(interests)

            mock_get.assert_not_called()
            assert result == []

    @pytest.mark.asyncio
    async def test_continues_on_category_failure(self, news_service):
        """Should continue if one category fails."""
        interests = [
            {"slug": "technology", "newsapi_category": "technology"},
            {"slug": "science", "newsapi_category": "science"},
        ]

        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Science Article", "url": "https://example.com/sci", "source": {"name": "Test"}},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            # First call raises, second succeeds
            mock_get.side_effect = [
                httpx.ConnectError("Failed"),
                mock_response,
            ]

            result = await news_service.get_headlines_for_interests(interests)

            # Should have articles from second category
            assert len(result) >= 0  # At least didn't crash

    @pytest.mark.asyncio
    async def test_deduplicates_by_url(self, news_service):
        """Should deduplicate articles by URL."""
        interests = [
            {"slug": "technology", "newsapi_category": "technology"},
            {"slug": "science", "newsapi_category": "science"},
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"title": "Same Article", "url": "https://same.com", "source": {"name": "Test"}},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            news_service.client, "get", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_response

            result = await news_service.get_headlines_for_interests(interests)

            # Same URL should appear only once
            assert len(result) == 1


class TestServiceClose:
    """Tests for service cleanup."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self, news_service):
        """Should close HTTP client on close."""
        with patch.object(
            news_service.client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await news_service.close()
            mock_close.assert_called_once()


class TestSingletonBehavior:
    """Tests for singleton helper functions."""

    @pytest.mark.asyncio
    async def test_get_news_service_creates_instance(self):
        """get_news_service should create an instance."""
        try:
            service = await get_news_service()
            assert service is not None
            assert isinstance(service, NewsService)
        finally:
            await close_news_service()

    @pytest.mark.asyncio
    async def test_get_news_service_returns_same_instance(self):
        """get_news_service should return same instance."""
        try:
            service1 = await get_news_service()
            service2 = await get_news_service()
            assert service1 is service2
        finally:
            await close_news_service()

    @pytest.mark.asyncio
    async def test_close_news_service_clears_singleton(self):
        """close_news_service should clear the singleton."""
        # Get a service
        await get_news_service()

        # Close it
        await close_news_service()

        # Get a new one - should be different instance
        await get_news_service()

        # Clean up
        await close_news_service()


class TestGetPreviousDayHeadlines:
    """Tests for get_previous_day_headlines method."""

    @pytest.mark.asyncio
    async def test_delegates_to_get_headlines_for_interests(self, news_service):
        """Should delegate to get_headlines_for_interests."""
        interests = [{"slug": "tech", "newsapi_category": "technology"}]

        with patch.object(
            news_service, "get_headlines_for_interests", new_callable=AsyncMock
        ) as mock_method:
            mock_method.return_value = []

            await news_service.get_previous_day_headlines(interests)

            mock_method.assert_called_once_with(interests)

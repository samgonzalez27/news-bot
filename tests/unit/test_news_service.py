"""
Unit tests for the news service.
"""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import httpx

from src.services.news_service import NewsService, get_news_service, close_news_service
from src.exceptions import NewsAPIError


class TestNewsService:
    """Tests for NewsService functionality."""

    @pytest.fixture
    def news_service(self):
        """Create a news service instance for testing."""
        service = NewsService()
        yield service
        # Cleanup not needed in sync tests

    @pytest.fixture
    def mock_headlines_response(self, mock_newsapi_response):
        """Create mock response for headlines endpoint."""
        return mock_newsapi_response

    @pytest.mark.asyncio
    async def test_fetch_top_headlines_success(
        self,
        news_service,
        mock_headlines_response,
    ):
        """Should successfully fetch and parse headlines."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_headlines_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            articles = await news_service._fetch_top_headlines(
                category="technology"
            )

            assert len(articles) == 2
            assert articles[0]["title"] == "Test Article Title 1"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_top_headlines_api_error(self, news_service):
        """Should raise NewsAPIError on API failure."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "error",
                "message": "API key invalid",
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with pytest.raises(NewsAPIError):
                await news_service._fetch_top_headlines()

    @pytest.mark.asyncio
    async def test_fetch_top_headlines_http_error(self, news_service):
        """Should raise NewsAPIError on HTTP error."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

            with pytest.raises(NewsAPIError):
                await news_service._fetch_top_headlines()

    @pytest.mark.asyncio
    async def test_fetch_top_headlines_connection_error(self, news_service):
        """Should raise NewsAPIError on connection error."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(NewsAPIError):
                await news_service._fetch_top_headlines()

    @pytest.mark.asyncio
    async def test_get_headlines_for_category_caching(
        self,
        news_service,
        mock_headlines_response,
    ):
        """Should cache headlines and avoid repeated API calls."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_headlines_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # First call - should hit API
            await news_service.get_headlines_for_category("technology")

            # Second call - should use cache
            await news_service.get_headlines_for_category(
                "technology",
                use_cache=True,
            )

            # Should only be called once due to caching
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_headlines_for_category_no_cache(
        self,
        news_service,
        mock_headlines_response,
    ):
        """Should bypass cache when requested."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_headlines_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # Two calls without caching
            await news_service.get_headlines_for_category(
                "technology",
                use_cache=False,
            )
            await news_service.get_headlines_for_category(
                "technology",
                use_cache=False,
            )

            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_headlines_normalizes_format(
        self,
        news_service,
        mock_headlines_response,
    ):
        """Should normalize article format."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_headlines_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            articles = await news_service.get_headlines_for_category(
                "technology",
                use_cache=False,
            )

            assert len(articles) == 2
            article = articles[0]
            assert "title" in article
            assert "description" in article
            assert "source" in article
            assert "url" in article
            assert "published_at" in article
            assert "category" in article
            assert article["category"] == "technology"

    @pytest.mark.asyncio
    async def test_get_headlines_for_interests(
        self,
        news_service,
        mock_headlines_response,
    ):
        """Should fetch headlines for multiple interests."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_headlines_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            interests = [
                {"slug": "technology", "newsapi_category": "technology"},
                {"slug": "economics", "newsapi_category": "business"},
            ]

            articles = await news_service.get_headlines_for_interests(interests)

            # Should have articles from both categories (deduplicated)
            assert len(articles) > 0
            # Each article should have interest_slug
            assert all("interest_slug" in a for a in articles)

    @pytest.mark.asyncio
    async def test_get_headlines_deduplicates(
        self,
        news_service,
        mock_headlines_response,
    ):
        """Should deduplicate articles with same URL."""
        with patch.object(
            news_service.client,
            "get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_headlines_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # Same category twice should deduplicate
            interests = [
                {"slug": "tech1", "newsapi_category": "technology"},
                {"slug": "tech2", "newsapi_category": "technology"},
            ]

            articles = await news_service.get_headlines_for_interests(interests)

            # Should only have 2 articles (deduplicated)
            urls = [a["url"] for a in articles]
            assert len(urls) == len(set(urls))


class TestNewsServiceSingleton:
    """Tests for news service singleton management."""

    @pytest.mark.asyncio
    async def test_get_news_service_creates_singleton(self):
        """Should create singleton instance."""
        service1 = await get_news_service()
        service2 = await get_news_service()

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_close_news_service(self):
        """Should close and clear singleton."""
        service = await get_news_service()
        assert service is not None

        await close_news_service()

        # Get again should create new instance
        new_service = await get_news_service()
        assert new_service is not service

        # Cleanup
        await close_news_service()

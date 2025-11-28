"""
Unit tests for the OpenAI service.
"""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import httpx

from src.services.openai_service import (
    OpenAIService,
    get_openai_service,
    close_openai_service,
)
from src.exceptions import OpenAIError


class TestOpenAIService:
    """Tests for OpenAIService functionality."""

    @pytest.fixture
    def openai_service(self):
        """Create an OpenAI service instance for testing."""
        return OpenAIService()

    @pytest.fixture
    def sample_headlines(self):
        """Sample headlines for testing."""
        return [
            {
                "title": "Tech Company Announces New Product",
                "description": "Major tech announcement today.",
                "source": "Tech News",
                "url": "https://example.com/tech",
                "published_at": "2024-01-15T10:00:00Z",
                "interest_slug": "technology",
            },
            {
                "title": "Stock Market Reaches New High",
                "description": "Markets rally on positive news.",
                "source": "Finance Daily",
                "url": "https://example.com/finance",
                "published_at": "2024-01-15T11:00:00Z",
                "interest_slug": "economics",
            },
        ]

    @pytest.mark.asyncio
    async def test_generate_digest_success(
        self,
        openai_service,
        sample_headlines,
        mock_openai_response,
    ):
        """Should successfully generate digest."""
        with patch.object(
            openai_service.client,
            "post",
            new_callable=AsyncMock,
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_openai_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await openai_service.generate_digest(
                headlines=sample_headlines,
                digest_date="2024-01-14",
                interests=["technology", "economics"],
            )

            assert "content" in result
            assert "summary" in result
            assert "word_count" in result
            assert result["word_count"] > 0
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_digest_empty_headlines(self, openai_service):
        """Should handle empty headlines gracefully."""
        result = await openai_service.generate_digest(
            headlines=[],
            digest_date="2024-01-14",
            interests=["technology"],
        )

        assert "content" in result
        assert "No news articles available" in result["content"]

    @pytest.mark.asyncio
    async def test_generate_digest_http_error(
        self,
        openai_service,
        sample_headlines,
    ):
        """Should raise OpenAIError on HTTP error."""
        with patch.object(
            openai_service.client,
            "post",
            new_callable=AsyncMock,
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                "error": {"message": "Internal server error"}
            }
            mock_response.content = b'{"error": {"message": "Internal server error"}}'
            mock_post.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=mock_response,
            )

            with pytest.raises(OpenAIError):
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-14",
                    interests=["technology"],
                )

    @pytest.mark.asyncio
    async def test_generate_digest_connection_error(
        self,
        openai_service,
        sample_headlines,
    ):
        """Should raise OpenAIError on connection error."""
        with patch.object(
            openai_service.client,
            "post",
            new_callable=AsyncMock,
        ) as mock_post:
            mock_post.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(OpenAIError):
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-14",
                    interests=["technology"],
                )

    def test_format_headlines_for_prompt(
        self,
        openai_service,
        sample_headlines,
    ):
        """Should format headlines into structured prompt."""
        formatted = openai_service._format_headlines_for_prompt(sample_headlines)

        assert "Technology" in formatted
        assert "Economics" in formatted
        assert "Tech Company Announces" in formatted
        assert "Stock Market" in formatted

    def test_format_headlines_groups_by_category(
        self,
        openai_service,
        sample_headlines,
    ):
        """Should group headlines by interest category."""
        formatted = openai_service._format_headlines_for_prompt(sample_headlines)

        # Should have section headers
        assert "### Technology" in formatted
        assert "### Economics" in formatted

    def test_extract_summary(self, openai_service):
        """Should extract summary from content."""
        content = """# Daily News Digest

**Executive Summary:** Today's top stories include technology and economics news.

## Technology
Some tech news here.
"""
        summary = openai_service._extract_summary(content)

        assert summary is not None
        assert len(summary) > 0
        assert len(summary) <= 200

    def test_extract_summary_truncates_long_text(self, openai_service):
        """Should truncate long summaries."""
        content = """# Daily News Digest

**Executive Summary:** """ + "A" * 300 + """

## Content
More content here.
"""
        summary = openai_service._extract_summary(content, max_length=200)

        assert len(summary) <= 200 + 3  # +3 for "..."

    def test_extract_summary_fallback(self, openai_service):
        """Should fallback when no executive summary found."""
        content = """# Daily News Digest

This is a paragraph that serves as the main content of the digest with more than fifty characters.

## Section
More content.
"""
        summary = openai_service._extract_summary(content)

        assert summary is not None
        assert len(summary) > 0


class TestOpenAIServiceSingleton:
    """Tests for OpenAI service singleton management."""

    @pytest.mark.asyncio
    async def test_get_openai_service_creates_singleton(self):
        """Should create singleton instance."""
        service1 = await get_openai_service()
        service2 = await get_openai_service()

        assert service1 is service2

        # Cleanup
        await close_openai_service()

    @pytest.mark.asyncio
    async def test_close_openai_service(self):
        """Should close and clear singleton."""
        service = await get_openai_service()
        assert service is not None

        await close_openai_service()

        # Get again should create new instance
        new_service = await get_openai_service()
        assert new_service is not service

        # Cleanup
        await close_openai_service()

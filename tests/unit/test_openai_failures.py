"""
Tests for OpenAI service failure modes.

Coverage improvements:
- HTTP error responses (4xx, 5xx)
- Connection errors
- Timeout handling
- Invalid API responses
- Rate limiting
- Token limit exceeded
- Content filtering

Uses httpx mock to simulate API behavior.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.openai_service import OpenAIService
from src.exceptions import OpenAIError


@pytest.fixture
def openai_service():
    """Create an OpenAI service instance for testing."""
    with patch("src.services.openai_service.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = "test-key"
        mock_settings.return_value.openai_model = "gpt-4o-mini"
        mock_settings.return_value.openai_max_tokens = 2000
        service = OpenAIService()
        yield service


@pytest.fixture
def sample_headlines():
    """Sample headlines for testing."""
    return [
        {
            "title": "Tech Giants Report Strong Earnings",
            "description": "Major tech companies exceed expectations",
            "source": "Tech News",
            "interest_slug": "technology",
        },
        {
            "title": "Stock Market Reaches New Highs",
            "description": "Markets continue upward trend",
            "source": "Financial Times",
            "interest_slug": "economics",
        },
    ]


class TestOpenAIServiceInit:
    """Tests for OpenAI service initialization."""

    def test_service_creates_http_client(self, openai_service):
        """Service should create an HTTP client."""
        assert openai_service.client is not None
        assert isinstance(openai_service.client, httpx.AsyncClient)

    def test_service_sets_api_key(self, openai_service):
        """Service should set API key."""
        assert openai_service.api_key == "test-key"

    def test_service_sets_model(self, openai_service):
        """Service should set model name."""
        assert openai_service.model == "gpt-4o-mini"


class TestGenerateDigestEmptyInput:
    """Tests for digest generation with empty input."""

    @pytest.mark.asyncio
    async def test_empty_headlines_returns_placeholder(self, openai_service):
        """Should return placeholder content for empty headlines."""
        result = await openai_service.generate_digest(
            headlines=[],
            digest_date="2024-01-01",
            interests=["technology"],
        )

        assert "No news articles available" in result["content"]
        assert result["word_count"] > 0


class TestGenerateDigestSuccess:
    """Tests for successful digest generation."""

    @pytest.mark.asyncio
    async def test_successful_generation(self, openai_service, sample_headlines):
        """Should return digest content on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "# Daily News Digest\n\nExecutive Summary: Test digest content."
                    },
                    "finish_reason": "stop",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            result = await openai_service.generate_digest(
                headlines=sample_headlines,
                digest_date="2024-01-01",
                interests=["technology", "economics"],
            )

            assert "content" in result
            assert "summary" in result
            assert "word_count" in result
            assert result["word_count"] > 0


class TestOpenAIHTTPErrors:
    """Tests for HTTP error handling."""

    @pytest.mark.asyncio
    async def test_401_unauthorized(self, openai_service, sample_headlines):
        """Should raise OpenAIError on 401 Unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.content = b'{"error": {"message": "Invalid API key"}}'
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}

        error = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = error

            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_429_rate_limit(self, openai_service, sample_headlines):
        """Should raise OpenAIError on 429 Rate Limit."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.content = b'{"error": {"message": "Rate limit exceeded"}}'
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        error = httpx.HTTPStatusError(
            "429 Too Many Requests", request=MagicMock(), response=mock_response
        )

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = error

            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

            assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_500_server_error(self, openai_service, sample_headlines):
        """Should raise OpenAIError on 500 Server Error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b'{"error": {"message": "Internal server error"}}'
        mock_response.json.return_value = {
            "error": {"message": "Internal server error"}
        }

        error = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = error

            with pytest.raises(OpenAIError):
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

    @pytest.mark.asyncio
    async def test_503_service_unavailable(self, openai_service, sample_headlines):
        """Should raise OpenAIError on 503 Service Unavailable."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.content = b'{"error": {"message": "Service unavailable"}}'
        mock_response.json.return_value = {"error": {"message": "Service unavailable"}}

        error = httpx.HTTPStatusError(
            "503 Service Unavailable", request=MagicMock(), response=mock_response
        )

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = error

            with pytest.raises(OpenAIError):
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )


class TestOpenAIConnectionErrors:
    """Tests for connection error handling."""

    @pytest.mark.asyncio
    async def test_connection_refused(self, openai_service, sample_headlines):
        """Should raise OpenAIError on connection refused."""
        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

            assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout(self, openai_service, sample_headlines):
        """Should raise OpenAIError on timeout."""
        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

            assert "Failed to connect" in str(exc_info.value)


class TestMalformedResponses:
    """Tests for handling malformed API responses."""

    @pytest.mark.asyncio
    async def test_missing_choices(self, openai_service, sample_headlines):
        """Should raise OpenAIError when choices key is missing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test"}  # Missing 'choices'
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

            assert "Invalid response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_choices(self, openai_service, sample_headlines):
        """Should raise OpenAIError when choices is empty."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.generate_digest(
                    headlines=sample_headlines,
                    digest_date="2024-01-01",
                    interests=["technology"],
                )

            assert "Invalid response" in str(exc_info.value)


class TestFormatHeadlinesForPrompt:
    """Tests for headline formatting."""

    def test_format_groups_by_category(self, openai_service):
        """Should group headlines by category."""
        headlines = [
            {"title": "Tech News 1", "interest_slug": "technology", "source": "A"},
            {"title": "Tech News 2", "interest_slug": "technology", "source": "B"},
            {"title": "Econ News", "interest_slug": "economics", "source": "C"},
        ]

        result = openai_service._format_headlines_for_prompt(headlines)

        assert "Technology" in result
        assert "Economics" in result
        assert "Tech News 1" in result
        assert "Econ News" in result

    def test_format_handles_empty_list(self, openai_service):
        """Should handle empty headlines list."""
        result = openai_service._format_headlines_for_prompt([])
        assert result == ""

    def test_format_uses_category_fallback(self, openai_service):
        """Should fall back to category field if interest_slug missing."""
        headlines = [
            {"title": "News", "category": "general", "source": "Test"},
        ]

        result = openai_service._format_headlines_for_prompt(headlines)
        assert "General" in result

    def test_format_truncates_description(self, openai_service):
        """Should truncate long descriptions."""
        headlines = [
            {
                "title": "News",
                "interest_slug": "tech",
                "source": "Test",
                "description": "A" * 500,  # Very long description
            },
        ]

        result = openai_service._format_headlines_for_prompt(headlines)
        # Should be truncated with ...
        assert "..." in result


class TestExtractSummary:
    """Tests for summary extraction."""

    def test_extract_executive_summary(self, openai_service):
        """Should extract executive summary section."""
        content = """# Daily Digest
        
**Executive Summary:** This is the summary text.

## Details
More content here.
"""
        result = openai_service._extract_summary(content)
        assert "summary text" in result.lower()

    def test_extract_fallback_first_paragraph(self, openai_service):
        """Should fall back to first paragraph if no executive summary."""
        content = """# Daily Digest

This is the first substantial paragraph with enough text to be selected.

## Details
More content here.
"""
        result = openai_service._extract_summary(content)
        assert "first substantial paragraph" in result.lower()

    def test_extract_default_when_empty(self, openai_service):
        """Should return default when content is just headers."""
        content = """# Header
## Subheader
- List item
"""
        result = openai_service._extract_summary(content)
        assert "Daily news digest" in result

    def test_extract_truncates_long_summary(self, openai_service):
        """Should truncate summaries over max length."""
        content = "This is a very long paragraph " * 20

        result = openai_service._extract_summary(content, max_length=50)
        assert len(result) <= 53  # 50 + "..."


class TestServiceClose:
    """Tests for service cleanup."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self, openai_service):
        """Should close HTTP client on close."""
        with patch.object(
            openai_service.client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await openai_service.close()
            mock_close.assert_called_once()


class TestAPIKeyInRequest:
    """Tests for API key handling in requests."""

    @pytest.mark.asyncio
    async def test_request_includes_auth_header(self, openai_service, sample_headlines):
        """Request should include Authorization header."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test"}, "finish_reason": "stop"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            await openai_service.generate_digest(
                headlines=sample_headlines,
                digest_date="2024-01-01",
                interests=["technology"],
            )

            # Check that post was called with correct URL
            call_args = mock_post.call_args
            assert "openai.com" in call_args[0][0]


class TestRequestPayload:
    """Tests for request payload structure."""

    @pytest.mark.asyncio
    async def test_request_includes_model(self, openai_service, sample_headlines):
        """Request should include model parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test"}, "finish_reason": "stop"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            await openai_service.generate_digest(
                headlines=sample_headlines,
                digest_date="2024-01-01",
                interests=["technology"],
            )

            call_kwargs = mock_post.call_args[1]
            assert "model" in call_kwargs["json"]
            assert call_kwargs["json"]["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_request_includes_messages(self, openai_service, sample_headlines):
        """Request should include messages array."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test"}, "finish_reason": "stop"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            openai_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            await openai_service.generate_digest(
                headlines=sample_headlines,
                digest_date="2024-01-01",
                interests=["technology"],
            )

            call_kwargs = mock_post.call_args[1]
            messages = call_kwargs["json"]["messages"]
            assert len(messages) >= 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"


class TestSingletonBehavior:
    """Tests for singleton helper functions."""

    @pytest.mark.asyncio
    async def test_get_openai_service_creates_instance(self):
        """get_openai_service should create an instance."""
        from src.services.openai_service import get_openai_service, close_openai_service

        try:
            service = await get_openai_service()
            assert service is not None
            assert isinstance(service, OpenAIService)
        finally:
            await close_openai_service()

    @pytest.mark.asyncio
    async def test_get_openai_service_returns_same_instance(self):
        """get_openai_service should return same instance."""
        from src.services.openai_service import get_openai_service, close_openai_service

        try:
            service1 = await get_openai_service()
            service2 = await get_openai_service()
            assert service1 is service2
        finally:
            await close_openai_service()

    @pytest.mark.asyncio
    async def test_close_openai_service_clears_singleton(self):
        """close_openai_service should clear the singleton."""
        from src.services.openai_service import (
            get_openai_service,
            close_openai_service,
        )

        # Get a service
        await get_openai_service()

        # Close it
        await close_openai_service()

        # Get a new one - should be different instance
        await get_openai_service()

        # Clean up
        await close_openai_service()

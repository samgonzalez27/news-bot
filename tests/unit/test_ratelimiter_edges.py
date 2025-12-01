"""
Rate limiter edge case tests.

Tests boundary conditions, concurrent access, bucket cleanup, and reset functionality.
Uses the actual RateLimiter API.
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.middleware.rate_limiter import (
    RateLimiter,
    RateLimitBucket,
    RateLimitMiddleware,
)


class TestRateLimiterBasics:
    """Test basic rate limiter functionality."""

    def test_default_initialization(self):
        """Test rate limiter initializes with default values."""
        limiter = RateLimiter()
        # rate = requests_per_minute / 60.0
        assert limiter.rate == 60 / 60.0  # 1.0 tokens per second
        assert limiter.burst == 10

    def test_custom_initialization(self):
        """Test rate limiter initializes with custom values."""
        limiter = RateLimiter(requests_per_minute=120, burst=20)
        assert limiter.rate == 120 / 60.0  # 2.0 tokens per second
        assert limiter.burst == 20

    def test_first_request_allowed(self):
        """Test first request is always allowed."""
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        allowed, retry_after = limiter.is_allowed("test_client")
        assert allowed is True
        assert retry_after == 0

    def test_requests_within_burst_allowed(self):
        """Test requests within burst limit are allowed."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        for i in range(5):
            allowed, _ = limiter.is_allowed("test_client")
            assert allowed is True, f"Request {i+1} should be allowed"

    def test_requests_exceeding_burst_blocked(self):
        """Test requests exceeding burst are blocked."""
        limiter = RateLimiter(requests_per_minute=60, burst=3)
        
        # Exhaust burst
        for _ in range(3):
            limiter.is_allowed("test_client")
        
        # Next request should be blocked
        allowed, retry_after = limiter.is_allowed("test_client")
        assert allowed is False
        assert retry_after > 0


class TestRateLimiterTokenRefill:
    """Test token refill behavior."""

    def test_tokens_refill_over_time(self):
        """Test that tokens refill after time passes."""
        limiter = RateLimiter(requests_per_minute=60, burst=2)
        
        # Exhaust tokens
        limiter.is_allowed("client")
        limiter.is_allowed("client")
        
        # Verify blocked
        allowed, _ = limiter.is_allowed("client")
        assert allowed is False
        
        # Manually advance the bucket's last_refill time
        bucket = limiter.buckets["client"]
        bucket.last_refill = time.time() - 2  # 2 seconds ago
        
        # Now should be allowed (2 seconds = 2 tokens at 1/sec)
        allowed, _ = limiter.is_allowed("client")
        assert allowed is True

    def test_get_remaining_returns_correct_count(self):
        """Test get_remaining returns available tokens."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        initial = limiter.get_remaining("client")
        assert initial == 5  # burst limit
        
        limiter.is_allowed("client")
        after_one = limiter.get_remaining("client")
        assert after_one == 4


class TestRateLimiterMultipleClients:
    """Test rate limiting across multiple clients."""

    def test_separate_buckets_per_client(self):
        """Test each client gets their own bucket."""
        limiter = RateLimiter(requests_per_minute=60, burst=3)
        
        # Exhaust client1
        for _ in range(3):
            limiter.is_allowed("client1")
        
        # client2 should still have tokens
        allowed, _ = limiter.is_allowed("client2")
        assert allowed is True

    def test_client_isolation(self):
        """Test one client's rate limit doesn't affect another."""
        limiter = RateLimiter(requests_per_minute=60, burst=2)
        
        # Block client1
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        allowed1, _ = limiter.is_allowed("client1")
        
        # client2 unaffected
        allowed2, _ = limiter.is_allowed("client2")
        
        assert allowed1 is False
        assert allowed2 is True


class TestRateLimiterReset:
    """Test reset functionality."""

    def test_reset_clears_all_buckets(self):
        """Test reset() clears all client buckets."""
        limiter = RateLimiter(requests_per_minute=60, burst=2)
        
        # Create some buckets
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        
        assert len(limiter.buckets) == 2
        
        # Reset
        limiter.reset()
        
        assert len(limiter.buckets) == 0

    def test_reset_allows_blocked_client(self):
        """Test reset allows previously blocked client."""
        limiter = RateLimiter(requests_per_minute=60, burst=1)
        
        # Block client
        limiter.is_allowed("client")
        allowed, _ = limiter.is_allowed("client")
        assert allowed is False
        
        # Reset
        limiter.reset()
        
        # Should be allowed now (new bucket with full tokens)
        allowed, _ = limiter.is_allowed("client")
        assert allowed is True


class TestRateLimiterCleanup:
    """Test bucket cleanup functionality."""

    def test_cleanup_removes_old_buckets(self):
        """Test cleanup_old_buckets removes stale entries."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        # Create a bucket
        limiter.is_allowed("old_client")
        
        # Make it old by manipulating last_refill
        limiter.buckets["old_client"] = RateLimitBucket(
            tokens=5.0,
            last_refill=time.time() - 7200  # 2 hours ago
        )
        
        # Cleanup with 1 hour max age
        removed = limiter.cleanup_old_buckets(max_age_seconds=3600)
        assert removed == 1
        assert "old_client" not in limiter.buckets

    def test_cleanup_preserves_recent_buckets(self):
        """Test cleanup preserves recently used buckets."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        # Create a recent bucket
        limiter.is_allowed("recent_client")
        
        # Cleanup
        removed = limiter.cleanup_old_buckets(max_age_seconds=3600)
        
        # Recent bucket should still exist
        assert removed == 0
        assert "recent_client" in limiter.buckets

    def test_cleanup_returns_count(self):
        """Test cleanup returns number of removed buckets."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        # No old buckets
        removed = limiter.cleanup_old_buckets()
        assert removed == 0

    def test_cleanup_multiple_old_buckets(self):
        """Test cleanup removes multiple old buckets."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        old_time = time.time() - 7200
        
        # Create multiple old buckets
        for i in range(5):
            limiter.buckets[f"old_client_{i}"] = RateLimitBucket(
                tokens=5.0,
                last_refill=old_time
            )
        
        removed = limiter.cleanup_old_buckets(max_age_seconds=3600)
        assert removed == 5
        assert len(limiter.buckets) == 0


class TestRateLimitBucket:
    """Test RateLimitBucket dataclass."""

    def test_bucket_creation(self):
        """Test bucket can be created with required fields."""
        now = time.time()
        bucket = RateLimitBucket(tokens=10.0, last_refill=now)
        assert bucket.tokens == 10.0
        assert bucket.last_refill == now

    def test_bucket_tokens_can_be_float(self):
        """Test bucket tokens can be fractional."""
        bucket = RateLimitBucket(tokens=5.5, last_refill=time.time())
        assert bucket.tokens == 5.5

    def test_bucket_is_mutable(self):
        """Test bucket attributes can be modified."""
        bucket = RateLimitBucket(tokens=5.0, last_refill=time.time())
        bucket.tokens = 3.0
        assert bucket.tokens == 3.0


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_middleware_allows_request(self):
        """Test middleware allows requests within limit."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        # Create a proper mock request with headers that return empty string for auth
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        
        def mock_get_header(name, default=""):
            if name == "authorization":
                return ""
            return None
        
        request.headers = MagicMock()
        request.headers.get = mock_get_header
        
        call_next = AsyncMock()
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next.return_value = mock_response
        
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_skips_exempt_paths(self):
        """Test middleware skips exempt paths."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/health"
        
        call_next = AsyncMock()
        mock_response = MagicMock()
        call_next.return_value = mock_response
        
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_handles_missing_client(self):
        """Test middleware handles request without client info."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        request = MagicMock()
        request.client = None
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        
        def mock_get_header(name, default=""):
            if name == "authorization":
                return ""
            return None
        
        request.headers = MagicMock()
        request.headers.get = mock_get_header
        
        call_next = AsyncMock()
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next.return_value = mock_response
        
        await middleware.dispatch(request, call_next)
        # Should still work (uses "unknown" as IP)
        call_next.assert_called_once()

    def test_reset_all_limiters_class_method(self):
        """Test reset_all_limiters class method."""
        # Create middleware instance to populate class-level limiters
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        # Use up some tokens
        middleware.default_limiter.is_allowed("client1")
        middleware.auth_limiter.is_allowed("client2")
        
        assert len(middleware.default_limiter.buckets) > 0
        assert len(middleware.auth_limiter.buckets) > 0
        
        # Reset all
        RateLimitMiddleware.reset_all_limiters()
        
        # Both should be reset
        assert len(middleware.default_limiter.buckets) == 0
        assert len(middleware.auth_limiter.buckets) == 0

    @pytest.mark.asyncio
    async def test_middleware_uses_auth_limiter_for_auth_paths(self):
        """Test middleware uses auth limiter for auth paths."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.url = MagicMock()
        request.url.path = "/api/v1/auth/login"
        
        def mock_get_header(name, default=""):
            if name == "authorization":
                return ""
            return None
        
        request.headers = MagicMock()
        request.headers.get = mock_get_header
        
        call_next = AsyncMock()
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next.return_value = mock_response
        
        await middleware.dispatch(request, call_next)
        
        # Auth limiter should have been used
        assert "ip:127.0.0.1" in middleware.auth_limiter.buckets


class TestRetryAfterCalculation:
    """Test retry-after header calculation."""

    def test_retry_after_is_positive_when_blocked(self):
        """Test retry_after is positive when rate limited."""
        limiter = RateLimiter(requests_per_minute=60, burst=1)
        
        # Exhaust
        limiter.is_allowed("client")
        
        # Get retry_after
        allowed, retry_after = limiter.is_allowed("client")
        assert allowed is False
        assert retry_after > 0

    def test_retry_after_zero_when_allowed(self):
        """Test retry_after is 0 when request is allowed."""
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        
        allowed, retry_after = limiter.is_allowed("client")
        assert allowed is True
        assert retry_after == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_client_key(self):
        """Test handling of empty client key."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        # Should handle empty string
        allowed, _ = limiter.is_allowed("")
        assert allowed is True

    def test_very_high_burst(self):
        """Test with very high burst value."""
        limiter = RateLimiter(requests_per_minute=1000, burst=1000)
        
        # Should handle large bursts
        for _ in range(100):
            allowed, _ = limiter.is_allowed("client")
            assert allowed is True

    def test_very_low_rate(self):
        """Test with very low rate."""
        limiter = RateLimiter(requests_per_minute=1, burst=1)
        
        # First allowed
        allowed, _ = limiter.is_allowed("client")
        assert allowed is True
        
        # Second blocked
        allowed, _ = limiter.is_allowed("client")
        assert allowed is False

    def test_concurrent_access_same_client(self):
        """Test concurrent access from same client."""
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        
        # Simulate rapid concurrent requests
        results = []
        for _ in range(15):
            allowed, _ = limiter.is_allowed("concurrent_client")
            results.append(allowed)
        
        # Should have some allowed and some blocked
        assert any(results)  # Some allowed
        assert not all(results)  # Some blocked

    def test_special_characters_in_key(self):
        """Test handling of special characters in client key."""
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        
        # Keys with special characters
        keys = [
            "user:abc-123",
            "ip:192.168.1.1",
            "key with spaces",
            "key/with/slashes",
            "unicode:日本語",
        ]
        
        for key in keys:
            allowed, _ = limiter.is_allowed(key)
            assert allowed is True


class TestRateLimitMiddlewareClientIP:
    """Test client IP extraction in middleware."""

    @pytest.mark.asyncio
    async def test_extracts_forwarded_for_header(self):
        """Test extracts IP from X-Forwarded-For header."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "127.0.0.1"
        
        # Simulate X-Forwarded-For header
        def get_header(name):
            headers = {
                "x-forwarded-for": "203.0.113.50, 70.41.3.18, 150.172.238.178",
                "authorization": None,
            }
            return headers.get(name.lower())
        
        request.headers.get = get_header
        
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.50"  # First IP in chain

    @pytest.mark.asyncio
    async def test_extracts_real_ip_header(self):
        """Test extracts IP from X-Real-IP header."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "127.0.0.1"
        
        def get_header(name):
            headers = {
                "x-forwarded-for": None,
                "x-real-ip": "203.0.113.50",
                "authorization": None,
            }
            return headers.get(name.lower())
        
        request.headers.get = get_header
        
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.50"

    @pytest.mark.asyncio
    async def test_falls_back_to_client_host(self):
        """Test falls back to request.client.host."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.client.host = "192.168.1.100"
        
        def get_header(name):
            return None
        
        request.headers.get = get_header
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"

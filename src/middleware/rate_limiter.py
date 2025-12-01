"""
Rate limiting middleware for the News Digest API.

Implements in-memory rate limiting suitable for single-instance deployment.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger("rate_limiter")


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""

    tokens: float
    last_refill: float


class RateLimiter:
    """
    Token bucket rate limiter.

    Implements a simple token bucket algorithm for rate limiting.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst: int = 10,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Sustained request rate.
            burst: Maximum burst size.
        """
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst = burst
        self.buckets: Dict[str, RateLimitBucket] = defaultdict(
            lambda: RateLimitBucket(tokens=burst, last_refill=time.time())
        )

    def _refill(self, bucket: RateLimitBucket) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket.last_refill
        bucket.tokens = min(self.burst, bucket.tokens + elapsed * self.rate)
        bucket.last_refill = now

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if a request is allowed.

        Args:
            key: Rate limit key (e.g., IP address or user ID).

        Returns:
            Tuple of (is_allowed, retry_after_seconds).
        """
        bucket = self.buckets[key]
        self._refill(bucket)

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return True, 0
        else:
            # Calculate retry-after
            tokens_needed = 1 - bucket.tokens
            retry_after = int(tokens_needed / self.rate) + 1
            return False, retry_after

    def get_remaining(self, key: str) -> int:
        """Get remaining tokens for a key."""
        bucket = self.buckets[key]
        self._refill(bucket)
        return int(bucket.tokens)

    def reset(self) -> None:
        """Reset all rate limit buckets. Useful for testing."""
        self.buckets.clear()

    def cleanup_old_buckets(self, max_age_seconds: int = 3600) -> int:
        """
        Remove old buckets to prevent memory growth.

        Args:
            max_age_seconds: Maximum age of inactive buckets.

        Returns:
            Number of buckets removed.
        """
        now = time.time()
        old_keys = [
            key
            for key, bucket in self.buckets.items()
            if now - bucket.last_refill > max_age_seconds
        ]
        for key in old_keys:
            del self.buckets[key]
        return len(old_keys)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting requests.

    Uses IP address for unauthenticated requests and user ID for
    authenticated requests.
    """

    # Paths that should be exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    # Paths with stricter rate limits (auth endpoints)
    AUTH_PATHS = {"/api/v1/auth/register", "/api/v1/auth/login"}
    AUTH_RATE_LIMIT = 5  # requests per minute
    
    # Class-level limiters for testing access
    _default_limiter = None
    _auth_limiter = None

    def __init__(self, app):
        """Initialize middleware with rate limiters."""
        super().__init__(app)
        settings = get_settings()
        self.default_limiter = RateLimiter(
            requests_per_minute=settings.rate_limit_per_minute,
            burst=settings.rate_limit_burst,
        )
        self.auth_limiter = RateLimiter(
            requests_per_minute=self.AUTH_RATE_LIMIT,
            burst=3,
        )
        self._last_cleanup = time.time()
        # Store references at class level for testing
        RateLimitMiddleware._default_limiter = self.default_limiter
        RateLimitMiddleware._auth_limiter = self.auth_limiter
    
    @classmethod
    def reset_all_limiters(cls):
        """Reset all rate limiters. Useful for testing."""
        if cls._default_limiter:
            cls._default_limiter.reset()
        if cls._auth_limiter:
            cls._auth_limiter.reset()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxy headers."""
        # Check for forwarded headers (from Nginx)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    def _get_rate_limit_key(self, request: Request) -> str:
        """
        Get the rate limit key for a request.

        Uses user ID if authenticated, otherwise IP address.
        """
        # Check for authenticated user
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from src.services.auth_service import AuthService

                token = auth_header.split()[1]
                user_id = AuthService.get_user_id_from_token(token)
                return f"user:{user_id}"
            except Exception:
                pass  # Fall through to IP-based limiting

        return f"ip:{self._get_client_ip(request)}"

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request with rate limiting."""
        path = request.url.path

        # Skip rate limiting for exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Periodic cleanup
        if time.time() - self._last_cleanup > 3600:
            removed = self.default_limiter.cleanup_old_buckets()
            removed += self.auth_limiter.cleanup_old_buckets()
            if removed > 0:
                logger.debug(f"Cleaned up {removed} rate limit buckets")
            self._last_cleanup = time.time()

        # Get rate limit key
        key = self._get_rate_limit_key(request)

        # Select limiter based on path
        if path in self.AUTH_PATHS:
            limiter = self.auth_limiter
        else:
            limiter = self.default_limiter

        # Check rate limit
        allowed, retry_after = limiter.is_allowed(key)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {key} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Add rate limit headers to response
        response = await call_next(request)

        remaining = limiter.get_remaining(key)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(limiter.burst)

        return response

"""
Centralized mocking utilities for the News Digest API test suite.

Provides reusable mocks, factories, and helpers for:
- OpenAI client behavior (success, timeout, rate-limit)
- NewsAPI client behavior (success, 401, malformed JSON)
- Database session mocks
- User service behaviors and failures
- Auth token factories (create valid/expired/tampered tokens)
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import httpx
from jose import jwt

from src.config import get_settings


# =============================================================================
# AUTH TOKEN FACTORIES
# =============================================================================

def create_valid_token(
    user_id: Optional[UUID] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a valid JWT access token for testing.
    
    Args:
        user_id: User ID to encode. Defaults to a new UUID.
        expires_delta: Token expiration time. Defaults to 24 hours.
    
    Returns:
        Valid JWT token string.
    """
    settings = get_settings()
    if user_id is None:
        user_id = uuid4()
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
    
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_expired_token(user_id: Optional[UUID] = None) -> str:
    """
    Create an expired JWT token for testing.
    
    Args:
        user_id: User ID to encode. Defaults to a new UUID.
    
    Returns:
        Expired JWT token string.
    """
    settings = get_settings()
    if user_id is None:
        user_id = uuid4()
    
    # Token expired 1 hour ago
    now = datetime.now(timezone.utc)
    expire = now - timedelta(hours=1)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now - timedelta(hours=2),
        "type": "access",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_wrong_signature(user_id: Optional[UUID] = None) -> str:
    """
    Create a token signed with the wrong secret key.
    
    Args:
        user_id: User ID to encode. Defaults to a new UUID.
    
    Returns:
        JWT token with invalid signature.
    """
    if user_id is None:
        user_id = uuid4()
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    
    # Sign with a different secret
    return jwt.encode(
        payload,
        "completely-wrong-secret-key-not-the-real-one",
        algorithm="HS256",
    )


def create_token_wrong_type(user_id: Optional[UUID] = None) -> str:
    """
    Create a token with wrong type (e.g., 'refresh' instead of 'access').
    
    Args:
        user_id: User ID to encode. Defaults to a new UUID.
    
    Returns:
        JWT token with wrong type claim.
    """
    settings = get_settings()
    if user_id is None:
        user_id = uuid4()
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",  # Wrong type
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_missing_sub(user_id: Optional[UUID] = None) -> str:
    """
    Create a token missing the 'sub' (subject/user ID) claim.
    
    Returns:
        JWT token without user ID.
    """
    settings = get_settings()
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    
    payload = {
        # Missing "sub" claim
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_invalid_uuid() -> str:
    """
    Create a token with invalid UUID in sub claim.
    
    Returns:
        JWT token with invalid user ID format.
    """
    settings = get_settings()
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    
    payload = {
        "sub": "not-a-valid-uuid",
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_tampered_token(user_id: Optional[UUID] = None) -> str:
    """
    Create a tampered token (modified payload after signing).
    
    This creates a valid-looking token but with a payload that doesn't match the signature.
    
    Returns:
        Tampered JWT token.
    """
    settings = get_settings()
    if user_id is None:
        user_id = uuid4()
    
    # Create a valid token first
    token = create_valid_token(user_id)
    
    # Tamper with it by modifying the payload part
    parts = token.split(".")
    if len(parts) == 3:
        # Modify the middle part (payload) slightly
        import base64
        payload_b64 = parts[1]
        # Add extra padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        # Decode, modify, re-encode
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            # Simple tampering: flip a byte
            tampered = bytearray(payload_bytes)
            if len(tampered) > 5:
                tampered[5] = (tampered[5] + 1) % 256
            parts[1] = base64.urlsafe_b64encode(bytes(tampered)).rstrip(b"=").decode()
            return ".".join(parts)
        except Exception:
            pass
    
    # Fallback: just corrupt a character
    return token[:-5] + "XXXXX"


# =============================================================================
# NEWSAPI MOCK RESPONSES
# =============================================================================

def create_newsapi_success_response(
    articles: Optional[List[Dict[str, Any]]] = None,
    total_results: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a successful NewsAPI response.
    
    Args:
        articles: List of article dictionaries. Defaults to sample articles.
        total_results: Total result count. Defaults to len(articles).
    
    Returns:
        NewsAPI-formatted success response.
    """
    if articles is None:
        articles = [
            {
                "source": {"id": "test-source", "name": "Test Source"},
                "author": "Test Author",
                "title": "Test Article Title 1",
                "description": "Test article description for testing purposes.",
                "url": "https://example.com/article1",
                "urlToImage": "https://example.com/image1.jpg",
                "publishedAt": "2024-01-15T10:00:00Z",
                "content": "Full test article content goes here.",
            },
            {
                "source": {"id": "test-source-2", "name": "Test Source 2"},
                "author": "Another Author",
                "title": "Test Article Title 2",
                "description": "Another test article description.",
                "url": "https://example.com/article2",
                "urlToImage": "https://example.com/image2.jpg",
                "publishedAt": "2024-01-15T11:00:00Z",
                "content": "Another full test article content.",
            },
        ]
    
    return {
        "status": "ok",
        "totalResults": total_results if total_results is not None else len(articles),
        "articles": articles,
    }


def create_newsapi_error_response(
    code: str = "apiKeyInvalid",
    message: str = "Your API key is invalid.",
) -> Dict[str, Any]:
    """
    Create a NewsAPI error response.
    
    Args:
        code: Error code (e.g., 'apiKeyInvalid', 'rateLimited').
        message: Error message.
    
    Returns:
        NewsAPI-formatted error response.
    """
    return {
        "status": "error",
        "code": code,
        "message": message,
    }


def create_newsapi_empty_response() -> Dict[str, Any]:
    """Create a NewsAPI response with no articles."""
    return {
        "status": "ok",
        "totalResults": 0,
        "articles": [],
    }


def create_newsapi_malformed_response() -> Dict[str, Any]:
    """Create a malformed NewsAPI response (missing expected fields)."""
    return {
        "unexpected": "data",
        "no_status": True,
    }


# =============================================================================
# OPENAI MOCK RESPONSES
# =============================================================================

def create_openai_success_response(
    content: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Create a successful OpenAI chat completion response.
    
    Args:
        content: Response content. Defaults to a sample digest.
        model: Model name.
    
    Returns:
        OpenAI-formatted success response.
    """
    if content is None:
        content = """# Daily News Digest - 2024-01-14

**Executive Summary:** Today's top stories cover major developments in technology and economics, with significant market movements and breakthrough announcements.

## Technology

Major tech companies announced new AI initiatives today. The developments signal a continued push toward artificial intelligence integration across consumer products.

## Economics

Economic indicators released today showed mixed signals. While employment figures remained strong, inflation concerns persist among analysts.

## Key Takeaways
- Technology sector sees continued AI investment
- Economic indicators show mixed signals
- Markets respond cautiously to new data
- Consumer confidence remains stable
"""
    
    return {
        "id": f"chatcmpl-{uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 500,
            "completion_tokens": len(content.split()),
            "total_tokens": 500 + len(content.split()),
        },
    }


def create_openai_error_response(
    error_type: str = "invalid_api_key",
    message: str = "Incorrect API key provided.",
    code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an OpenAI error response.
    
    Args:
        error_type: Type of error.
        message: Error message.
        code: Optional error code.
    
    Returns:
        OpenAI-formatted error response.
    """
    error = {
        "message": message,
        "type": error_type,
    }
    if code:
        error["code"] = code
    
    return {"error": error}


def create_openai_rate_limit_response() -> Dict[str, Any]:
    """Create an OpenAI rate limit error response."""
    return create_openai_error_response(
        error_type="rate_limit_exceeded",
        message="Rate limit exceeded. Please retry after 60 seconds.",
        code="rate_limit_exceeded",
    )


def create_openai_malformed_response() -> Dict[str, Any]:
    """Create a malformed OpenAI response (missing expected fields)."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        # Missing 'choices' key
        "created": int(time.time()),
    }


# =============================================================================
# HTTPX MOCK HELPERS
# =============================================================================

class MockHTTPResponse:
    """Mock httpx.Response for testing."""
    
    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text: str = "",
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text or (str(json_data) if json_data else "")
        self.headers = headers or {}
        self.content = text.encode() if text else b""
        
        # For httpx compatibility
        self.is_error = status_code >= 400
        self.is_success = 200 <= status_code < 300
    
    def json(self) -> Dict[str, Any]:
        if self._json_data is None:
            raise ValueError("No JSON data")
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=MagicMock(),
                response=self,
            )


def create_mock_httpx_client(responses: List[MockHTTPResponse]) -> AsyncMock:
    """
    Create a mock httpx.AsyncClient that returns predefined responses.
    
    Args:
        responses: List of MockHTTPResponse objects to return in sequence.
    
    Returns:
        Mock AsyncClient.
    """
    client = AsyncMock()
    
    # Track response index
    response_index = [0]
    
    async def mock_get(*args, **kwargs):
        idx = response_index[0]
        response_index[0] = min(idx + 1, len(responses) - 1)
        return responses[idx]
    
    async def mock_post(*args, **kwargs):
        idx = response_index[0]
        response_index[0] = min(idx + 1, len(responses) - 1)
        return responses[idx]
    
    client.get = mock_get
    client.post = mock_post
    client.aclose = AsyncMock()
    
    return client


# =============================================================================
# DATABASE MOCK HELPERS
# =============================================================================

def create_mock_user(
    user_id: Optional[UUID] = None,
    email: str = "test@example.com",
    is_active: bool = True,
    full_name: str = "Test User",
) -> MagicMock:
    """
    Create a mock User object for testing.
    
    Args:
        user_id: User ID. Defaults to a new UUID.
        email: User email.
        is_active: Whether user is active.
        full_name: User's full name.
    
    Returns:
        Mock User object.
    """
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = email
    user.is_active = is_active
    user.full_name = full_name
    user.hashed_password = "hashed_password_placeholder"
    user.timezone = "UTC"
    user.preferred_time = datetime.now().time()
    user.interests = []
    return user


def create_mock_db_session() -> AsyncMock:
    """
    Create a mock async database session.
    
    Returns:
        Mock AsyncSession.
    """
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


# =============================================================================
# RATE LIMITER HELPERS
# =============================================================================

class MockTimeProvider:
    """
    Mock time provider for rate limiter testing.
    
    Allows controlling the passage of time in tests.
    """
    
    def __init__(self, start_time: Optional[float] = None):
        self._current_time = start_time or time.time()
    
    def time(self) -> float:
        return self._current_time
    
    def advance(self, seconds: float):
        """Advance the mock time by the specified seconds."""
        self._current_time += seconds
    
    def set(self, timestamp: float):
        """Set the mock time to a specific timestamp."""
        self._current_time = timestamp


# =============================================================================
# COVERAGE EXPLANATION
# =============================================================================
"""
Coverage Improvements from tests/mocks.py:

1. Token Factories:
   - create_valid_token: Used to test authenticated endpoints
   - create_expired_token: Tests TokenExpiredError handling
   - create_token_wrong_signature: Tests InvalidTokenError (signature mismatch)
   - create_token_wrong_type: Tests type validation in decode_token
   - create_token_missing_sub: Tests user ID extraction error paths
   - create_token_invalid_uuid: Tests UUID parsing error paths
   - create_tampered_token: Tests signature verification

2. NewsAPI Mocks:
   - Success/error/empty/malformed responses enable testing all NewsService paths
   - HTTP status error simulation tests exception handling
   - Network error simulation tests connection failure paths

3. OpenAI Mocks:
   - Success/error/rate-limit/malformed responses enable full OpenAIService coverage
   - Tests digest generation success and failure modes

4. Database Mocks:
   - Mock sessions enable unit testing without real database
   - Mock users enable service layer testing in isolation

5. Rate Limiter Helpers:
   - MockTimeProvider enables deterministic rate limit testing
   - Can test window boundaries, burst limits, and cleanup

Each mock reduces risk by:
- Enabling deterministic, repeatable tests
- Isolating components from external dependencies
- Testing error handling paths that are hard to trigger with real services
"""

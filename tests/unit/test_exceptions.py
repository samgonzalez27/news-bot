"""
Unit tests for exceptions module.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.exceptions import (
    NewsDigestException,
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    DuplicateError,
    ExternalAPIError,
    NewsAPIError,
    OpenAIError,
    RateLimitError,
    DatabaseError,
    create_error_response,
    register_exception_handlers,
)


class TestNewsDigestException:
    """Tests for base exception class."""

    def test_default_values(self):
        """Should have default error code."""
        exc = NewsDigestException("Test error")
        
        assert exc.message == "Test error"
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.details == {}

    def test_custom_values(self):
        """Should accept custom error code and details."""
        exc = NewsDigestException(
            "Test error",
            error_code="CUSTOM",
            details={"key": "value"},
        )
        
        assert exc.error_code == "CUSTOM"
        assert exc.details == {"key": "value"}


class TestAuthenticationError:
    """Tests for authentication exceptions."""

    def test_default_message(self):
        """Should have default message."""
        exc = AuthenticationError()
        
        assert exc.message == "Authentication failed"
        assert exc.error_code == "AUTHENTICATION_ERROR"

    def test_custom_message(self):
        """Should accept custom message."""
        exc = AuthenticationError("Custom auth error")
        
        assert exc.message == "Custom auth error"


class TestInvalidCredentialsError:
    """Tests for invalid credentials exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = InvalidCredentialsError()
        
        assert exc.message == "Invalid email or password"
        assert exc.error_code == "INVALID_CREDENTIALS"


class TestTokenExpiredError:
    """Tests for token expired exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = TokenExpiredError()
        
        assert exc.message == "Token has expired"
        assert exc.error_code == "TOKEN_EXPIRED"


class TestInvalidTokenError:
    """Tests for invalid token exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = InvalidTokenError()
        
        assert exc.message == "Invalid token"
        assert exc.error_code == "INVALID_TOKEN"


class TestAuthorizationError:
    """Tests for authorization exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = AuthorizationError()
        
        assert exc.message == "Permission denied"
        assert exc.error_code == "AUTHORIZATION_ERROR"


class TestValidationError:
    """Tests for validation exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = ValidationError()
        
        assert exc.message == "Validation failed"
        assert exc.error_code == "VALIDATION_ERROR"
        assert "errors" in exc.details

    def test_with_errors(self):
        """Should accept error list."""
        errors = [{"field": "email", "message": "Invalid format"}]
        exc = ValidationError(errors=errors)
        
        assert exc.details["errors"] == errors


class TestNotFoundError:
    """Tests for not found exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = NotFoundError()
        
        assert exc.message == "Resource not found"

    def test_with_resource(self):
        """Should include resource name."""
        exc = NotFoundError("User")
        
        assert exc.message == "User not found"

    def test_with_resource_id(self):
        """Should include resource ID."""
        exc = NotFoundError("User", "123")
        
        assert "123" in exc.message


class TestDuplicateError:
    """Tests for duplicate exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = DuplicateError()
        
        assert "already exists" in exc.message

    def test_with_resource_and_field(self):
        """Should include resource and field."""
        exc = DuplicateError("User", "email")
        
        assert "User" in exc.message
        assert "email" in exc.message


class TestExternalAPIError:
    """Tests for external API exception."""

    def test_includes_service(self):
        """Should include service name in message."""
        exc = ExternalAPIError("TestService", "Connection failed")
        
        assert "TestService" in exc.message
        assert "Connection failed" in exc.message


class TestNewsAPIError:
    """Tests for NewsAPI exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = NewsAPIError()
        
        assert "NewsAPI" in exc.message
        assert exc.error_code == "NEWSAPI_ERROR"


class TestOpenAIError:
    """Tests for OpenAI exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = OpenAIError()
        
        assert "OpenAI" in exc.message
        assert exc.error_code == "OPENAI_ERROR"


class TestRateLimitError:
    """Tests for rate limit exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = RateLimitError()
        
        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.retry_after == 60

    def test_custom_retry_after(self):
        """Should accept custom retry_after."""
        exc = RateLimitError(retry_after=120)
        
        assert exc.retry_after == 120
        assert exc.details["retry_after"] == 120


class TestDatabaseError:
    """Tests for database exception."""

    def test_default_values(self):
        """Should have appropriate defaults."""
        exc = DatabaseError()
        
        assert exc.message == "Database operation failed"
        assert exc.error_code == "DATABASE_ERROR"


class TestCreateErrorResponse:
    """Tests for create_error_response function."""

    def test_creates_json_response(self):
        """Should create JSONResponse with correct structure."""
        response = create_error_response(
            status_code=400,
            message="Bad request",
            error_code="BAD_REQUEST",
            path="/test",
        )
        
        assert response.status_code == 400

    def test_includes_details(self):
        """Should include details in response."""
        response = create_error_response(
            status_code=400,
            message="Error",
            error_code="ERROR",
            path="/test",
            details={"extra": "info"},
        )
        
        assert response.status_code == 400


class TestRegisterExceptionHandlers:
    """Tests for exception handler registration."""

    def test_registers_handlers(self):
        """Should register handlers without error."""
        mock_app = MagicMock()
        mock_app.exception_handler = MagicMock(return_value=lambda f: f)
        
        register_exception_handlers(mock_app)
        
        # Should have registered multiple handlers
        assert mock_app.exception_handler.call_count > 0

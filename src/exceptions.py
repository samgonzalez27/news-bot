"""
Custom exceptions for the News Digest API.

Provides a hierarchy of exceptions for different error types,
along with FastAPI exception handlers.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class NewsDigestException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(NewsDigestException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(
        self,
        message: str = "Invalid email or password",
        error_code: str = "INVALID_CREDENTIALS",
    ):
        super().__init__(message, error_code)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        error_code: str = "TOKEN_EXPIRED",
    ):
        super().__init__(message, error_code)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""

    def __init__(
        self,
        message: str = "Invalid token",
        error_code: str = "INVALID_TOKEN",
    ):
        super().__init__(message, error_code)


class AuthorizationError(NewsDigestException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str = "AUTHORIZATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class ValidationError(NewsDigestException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        errors: Optional[List[Dict[str, str]]] = None,
    ):
        super().__init__(message, error_code, {"errors": errors or []})


class NotFoundError(NewsDigestException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
        error_code: str = "NOT_FOUND",
    ):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message, error_code)


class DuplicateError(NewsDigestException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(
        self,
        resource: str = "Resource",
        field: str = "field",
        error_code: str = "DUPLICATE_ERROR",
    ):
        message = f"{resource} with this {field} already exists"
        super().__init__(message, error_code)


class ExternalAPIError(NewsDigestException):
    """Raised when an external API call fails."""

    def __init__(
        self,
        service: str,
        message: str = "External API error",
        error_code: str = "EXTERNAL_API_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        full_message = f"{service}: {message}"
        super().__init__(full_message, error_code, details)


class NewsAPIError(ExternalAPIError):
    """Raised when NewsAPI call fails."""

    def __init__(
        self,
        message: str = "Failed to fetch news",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("NewsAPI", message, "NEWSAPI_ERROR", details)


class OpenAIError(ExternalAPIError):
    """Raised when OpenAI API call fails."""

    def __init__(
        self,
        message: str = "Failed to generate digest",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("OpenAI", message, "OPENAI_ERROR", details)


class RateLimitError(NewsDigestException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
    ):
        super().__init__(
            message,
            "RATE_LIMIT_EXCEEDED",
            {"retry_after": retry_after},
        )
        self.retry_after = retry_after


class DatabaseError(NewsDigestException):
    """Raised when database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        error_code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


def create_error_response(
    status_code: int,
    message: str,
    error_code: str,
    path: str,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response."""
    from datetime import datetime, timezone

    content = {
        "detail": message,
        "error_code": error_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": path,
    }

    if details:
        content.update(details)

    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with the FastAPI application."""

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
            details=exc.details if exc.details else None,
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
            details=exc.details if exc.details else None,
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
            details=exc.details,
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
        )

    @app.exception_handler(DuplicateError)
    async def duplicate_error_handler(
        request: Request, exc: DuplicateError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
        )

    @app.exception_handler(ExternalAPIError)
    async def external_api_error_handler(
        request: Request, exc: ExternalAPIError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
            details=exc.details if exc.details else None,
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        response = create_error_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
            details=exc.details,
        )
        response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @app.exception_handler(DatabaseError)
    async def database_error_handler(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An internal error occurred",
            error_code=exc.error_code,
            path=str(request.url.path),
        )

    @app.exception_handler(NewsDigestException)
    async def news_digest_exception_handler(
        request: Request, exc: NewsDigestException
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=exc.message,
            error_code=exc.error_code,
            path=str(request.url.path),
            details=exc.details if exc.details else None,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        from src.logging_config import get_logger

        logger = get_logger("exceptions")
        logger.exception(f"Unhandled exception: {exc}")

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An internal server error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            path=str(request.url.path),
        )

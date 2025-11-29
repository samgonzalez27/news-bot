"""
News Digest API - Main Application Entry Point

A FastAPI application that generates personalized daily news digests
for users based on their selected interests.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings
from src.database import close_db, init_db
from src.exceptions import register_exception_handlers
from src.logging_config import get_logger, set_request_id, setup_logging
from src.middleware.rate_limiter import RateLimitMiddleware
from src.routers import (
    auth_router,
    digests_router,
    health_router,
    interests_router,
    users_router,
)
from src.scheduler import start_scheduler, stop_scheduler
from src.scheduler.jobs import seed_interests_on_startup
from src.services.news_service import close_news_service
from src.services.openai_service import close_openai_service

# Initialize logging (lazy - doesn't load settings at import time)
logger = None


def _get_logger():
    """Get or create the application logger."""
    global logger
    if logger is None:
        logger = setup_logging()
    return logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)
        
        # Add request ID to response headers
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        # Log request completion
        log = _get_logger()
        log.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
            extra={
                "request_path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Get settings and logger at runtime (not import time)
    settings = get_settings()
    log = _get_logger()
    
    # Startup
    log.info(f"Starting {settings.app_name} ({settings.app_env})")

    # Initialize database (development only - use migrations in production)
    if settings.is_development:
        await init_db()
        log.info("Database tables initialized")

    # Seed interests
    await seed_interests_on_startup()

    # Start scheduler
    start_scheduler()

    log.info(f"{settings.app_name} started successfully")

    yield

    # Shutdown
    log.info(f"Shutting down {settings.app_name}")

    # Stop scheduler
    stop_scheduler()

    # Close external service clients
    await close_news_service()
    await close_openai_service()

    # Close database connections
    await close_db()

    log.info(f"{settings.app_name} shutdown complete")


def _create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Uses a factory function to defer settings access until runtime.
    """
    settings = get_settings()
    
    application = FastAPI(
        title=settings.app_name,
        description="""
    ## News Digest API

    A personalized daily news digest service that aggregates news from
    various sources and generates cohesive summaries based on user interests.

    ### Features

    - **User Authentication**: Secure JWT-based authentication
    - **Interest Management**: Subscribe to news categories
    - **Daily Digests**: Automated personalized news summaries
    - **On-Demand Generation**: Manually trigger digest creation

    ### Authentication

    Most endpoints require authentication. Include the JWT token in the
    Authorization header:

    ```
    Authorization: Bearer <your_token>
    ```

    Obtain a token via the `/api/v1/auth/login` endpoint.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add request ID middleware (first, so it wraps everything)
    application.add_middleware(RequestIDMiddleware)

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting middleware
    application.add_middleware(RateLimitMiddleware)

    # Register exception handlers
    register_exception_handlers(application)

    # Include routers
    application.include_router(health_router)  # Health checks at /health/*
    application.include_router(auth_router, prefix=settings.api_v1_prefix)
    application.include_router(users_router, prefix=settings.api_v1_prefix)
    application.include_router(interests_router, prefix=settings.api_v1_prefix)
    application.include_router(digests_router, prefix=settings.api_v1_prefix)
    
    # Add root endpoint
    @application.get(
        "/",
        tags=["Root"],
        summary="Root endpoint",
        description="Returns basic API information.",
    )
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    return application


# Create app instance - deferred to first access for test compatibility
_app_instance = None


def get_app() -> FastAPI:
    """Get or create the FastAPI application instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = _create_app()
    return _app_instance


def reset_app() -> None:
    """
    Reset the application instance.
    
    Useful for testing to ensure a fresh app is created with new middleware.
    """
    global _app_instance
    _app_instance = None


# For compatibility with uvicorn and existing imports
# This creates the app lazily on first attribute access
class _LazyApp:
    """
    ASGI-compatible lazy proxy that creates the app on first access.
    
    This ensures:
    1. Settings are not loaded at import time (important for testing)
    2. Full ASGI compatibility with uvicorn and other servers
    3. The app instance is only created once
    """
    _real_app = None
    
    def _get_app(self):
        if self._real_app is None:
            self._real_app = _create_app()
        return self._real_app
    
    def _reset_app(self):
        """Reset the app instance for testing."""
        self._real_app = None
    
    def __getattr__(self, name):
        return getattr(self._get_app(), name)
    
    async def __call__(self, scope, receive, send):
        """ASGI interface - delegate to the real FastAPI app."""
        app = self._get_app()
        await app(scope, receive, send)


app = _LazyApp()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )

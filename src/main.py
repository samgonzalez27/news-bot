"""
News Digest API - Main Application Entry Point

A FastAPI application that generates personalized daily news digests
for users based on their selected interests.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.database import close_db, init_db
from src.exceptions import register_exception_handlers
from src.logging_config import setup_logging
from src.middleware.rate_limiter import RateLimitMiddleware
from src.routers import auth_router, digests_router, interests_router, users_router
from src.scheduler import start_scheduler, stop_scheduler
from src.scheduler.jobs import seed_interests_on_startup
from src.services.news_service import close_news_service
from src.services.openai_service import close_openai_service

# Initialize logging
logger = setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")

    # Initialize database (development only - use migrations in production)
    if settings.is_development:
        await init_db()
        logger.info("Database tables initialized")

    # Seed interests
    await seed_interests_on_startup()

    # Start scheduler
    start_scheduler()

    logger.info(f"{settings.app_name} started successfully")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

    # Stop scheduler
    stop_scheduler()

    # Close external service clients
    await close_news_service()
    await close_openai_service()

    # Close database connections
    await close_db()

    logger.info(f"{settings.app_name} shutdown complete")


# Create FastAPI application
app = FastAPI(
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(interests_router, prefix=settings.api_v1_prefix)
app.include_router(digests_router, prefix=settings.api_v1_prefix)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the health status of the API.",
)
async def health_check() -> dict:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get(
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )

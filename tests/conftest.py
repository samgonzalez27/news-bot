"""
Pytest fixtures and configuration for the News Digest API tests.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import Settings, get_settings
from src.database import Base, get_db
from src.main import app
from src.models.interest import Interest, PREDEFINED_INTERESTS
from src.models.user import User
from src.services.auth_service import AuthService


# Test database URL (SQLite for simplicity)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


def get_test_settings() -> Settings:
    """Get settings configured for testing."""
    return Settings(
        app_env="testing",
        debug=True,
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key-for-jwt-tokens-minimum-32-chars",
        newsapi_key="test-newsapi-key",
        openai_api_key="test-openai-api-key",
        scheduler_enabled=False,
        log_level="DEBUG",
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def seeded_db(db_session: AsyncSession) -> AsyncSession:
    """Database session with seeded interests."""
    for interest_data in PREDEFINED_INTERESTS:
        interest = Interest(**interest_data)
        db_session.add(interest)
    await db_session.commit()
    return db_session


@pytest.fixture
def test_settings() -> Settings:
    """Get test settings."""
    return get_test_settings()


@pytest.fixture
def override_settings(test_settings: Settings):
    """Override app settings for testing."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def override_db(db_session: AsyncSession):
    """Override database dependency for testing."""
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def override_seeded_db(seeded_db: AsyncSession):
    """Override database dependency for testing with seeded interests."""
    async def _get_test_db():
        yield seeded_db

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(override_settings, override_seeded_db) -> TestClient:
    """Create synchronous test client with seeded database."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_no_seed(override_settings, override_db) -> TestClient:
    """Create synchronous test client without seeded interests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(override_settings, override_seeded_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with seeded database."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(seeded_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=AuthService.hash_password("TestPassword123"),
        full_name="Test User",
        timezone="UTC",
        is_active=True,
    )
    seeded_db.add(user)
    await seeded_db.commit()
    await seeded_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_with_interests(seeded_db: AsyncSession) -> User:
    """Create a test user with interests."""
    from sqlalchemy import select
    from src.models.user import UserInterest

    user = User(
        id=uuid4(),
        email="test.interests@example.com",
        hashed_password=AuthService.hash_password("TestPassword123"),
        full_name="Test User With Interests",
        timezone="America/New_York",
        is_active=True,
    )
    seeded_db.add(user)
    await seeded_db.flush()

    # Add some interests
    stmt = select(Interest).where(Interest.slug.in_(["technology", "economics"]))
    result = await seeded_db.execute(stmt)
    interests = result.scalars().all()

    for interest in interests:
        user_interest = UserInterest(
            user_id=user.id,
            interest_id=interest.id,
        )
        seeded_db.add(user_interest)

    await seeded_db.commit()
    await seeded_db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create auth token for test user."""
    return AuthService.create_access_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


# Mock data fixtures
@pytest.fixture
def mock_newsapi_response() -> dict:
    """Mock NewsAPI response data."""
    return {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "source": {"id": "test-source", "name": "Test Source"},
                "author": "Test Author",
                "title": "Test Article Title 1",
                "description": "Test article description 1",
                "url": "https://example.com/article1",
                "urlToImage": "https://example.com/image1.jpg",
                "publishedAt": "2024-01-15T10:00:00Z",
                "content": "Test article content 1",
            },
            {
                "source": {"id": "test-source-2", "name": "Test Source 2"},
                "author": "Test Author 2",
                "title": "Test Article Title 2",
                "description": "Test article description 2",
                "url": "https://example.com/article2",
                "urlToImage": "https://example.com/image2.jpg",
                "publishedAt": "2024-01-15T11:00:00Z",
                "content": "Test article content 2",
            },
        ],
    }


@pytest.fixture
def mock_openai_response() -> dict:
    """Mock OpenAI response data."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1705320000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": """# Daily News Digest - 2024-01-14

**Executive Summary:** Today's top stories cover major developments in technology and economics.

## Technology

Major announcements in the tech sector today...

## Economics

Economic indicators show positive trends...

## Key Takeaways
- Technology sector sees growth
- Economic indicators positive
- Market sentiment improving
""",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 500,
            "completion_tokens": 200,
            "total_tokens": 700,
        },
    }

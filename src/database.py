"""
Database configuration and session management.

Provides async SQLAlchemy engine, session factory, and base model.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Lazy-initialized module-level objects
_engine = None
_async_session_maker = None


def get_engine():
    """
    Get or create the async database engine.
    
    Uses lazy initialization to avoid loading settings at import time,
    which is critical for test compatibility.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        
        # Build engine kwargs - pool settings only apply to PostgreSQL
        engine_kwargs = {
            "echo": settings.debug,
        }
        
        # SQLite doesn't support pool_size and max_overflow
        if settings.database_url.startswith("postgresql"):
            engine_kwargs["pool_size"] = settings.db_pool_size
            engine_kwargs["max_overflow"] = settings.db_max_overflow
            engine_kwargs["pool_pre_ping"] = True  # Enable connection health checks
        elif settings.database_url.startswith("sqlite"):
            # SQLite needs special connect args for async
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        
        _engine = create_async_engine(settings.database_url, **engine_kwargs)
    return _engine


def get_async_session_maker():
    """
    Get or create the async session maker.
    
    Uses lazy initialization to avoid loading settings at import time.
    """
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker


# Backwards compatibility aliases (lazy property access)
class _LazyEngine:
    """Proxy object for backwards compatibility with `engine` access."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)

class _LazySessionMaker:
    """Proxy object for backwards compatibility with `async_session_maker` access."""
    def __call__(self):
        return get_async_session_maker()()
    def __getattr__(self, name):
        return getattr(get_async_session_maker(), name)

engine = _LazyEngine()
async_session_maker = _LazySessionMaker()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: Database session that is automatically closed after use.
    """
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Should be called on application startup in development.
    Use Alembic migrations for production.
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Should be called on application shutdown.
    """
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None


def reset_engine() -> None:
    """
    Reset the database engine and session maker.
    
    Useful for testing to ensure a fresh engine is created.
    This is a synchronous reset - just clears the references.
    """
    global _engine, _async_session_maker
    _engine = None
    _async_session_maker = None

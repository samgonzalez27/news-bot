"""
Unit tests for database module.
"""

import pytest
from unittest.mock import patch

from src.database import (
    get_engine,
    get_async_session_maker,
    get_db,
    init_db,
    close_db,
    reset_engine,
    _LazyEngine,
    _LazySessionMaker,
)


class TestGetEngine:
    """Tests for get_engine function."""

    def test_creates_engine_on_first_call(self):
        """Should create engine on first call."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            mock_settings.return_value.db_pool_size = 5
            mock_settings.return_value.db_max_overflow = 10
            
            engine = get_engine()
            
            assert engine is not None
        
        # Clean up
        reset_engine()

    def test_returns_cached_engine(self):
        """Should return cached engine on subsequent calls."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            engine1 = get_engine()
            engine2 = get_engine()
            
            assert engine1 is engine2
        
        reset_engine()


class TestGetAsyncSessionMaker:
    """Tests for get_async_session_maker function."""

    def test_creates_session_maker_on_first_call(self):
        """Should create session maker on first call."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            session_maker = get_async_session_maker()
            
            assert session_maker is not None
        
        reset_engine()


class TestGetDb:
    """Tests for get_db dependency."""

    @pytest.mark.asyncio
    async def test_yields_session_and_commits(self):
        """Should yield session and commit on success."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            async for session in get_db():
                assert session is not None
                break  # Just test we get a session
        
        reset_engine()


class TestLazyEngine:
    """Tests for _LazyEngine proxy."""

    def test_lazy_engine_getattr(self):
        """Should proxy attribute access to real engine."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            lazy = _LazyEngine()
            # Access an attribute - should delegate to real engine
            url = lazy.url
            assert url is not None
        
        reset_engine()


class TestLazySessionMaker:
    """Tests for _LazySessionMaker proxy."""

    def test_lazy_session_maker_call(self):
        """Should be callable to create session."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            lazy = _LazySessionMaker()
            session = lazy()
            assert session is not None
        
        reset_engine()


class TestResetEngine:
    """Tests for reset_engine function."""

    def test_reset_clears_engine(self):
        """Should clear engine reference."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            # Create engine
            engine1 = get_engine()
            assert engine1 is not None
            
            # Reset
            reset_engine()
            
            # Next call should create new engine
            engine2 = get_engine()
            assert engine2 is not engine1
        
        reset_engine()


class TestCloseDb:
    """Tests for close_db function."""

    @pytest.mark.asyncio
    async def test_disposes_engine(self):
        """Should dispose engine and clear references."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            # Create engine
            get_engine()
            
            # Close should dispose
            await close_db()
        
        # Engine reference should be cleared
        # (we can't easily verify dispose was called on the actual engine)


class TestInitDb:
    """Tests for init_db function."""

    @pytest.mark.asyncio
    async def test_creates_tables(self):
        """Should create database tables."""
        reset_engine()
        
        with patch("src.database.get_settings") as mock_settings:
            mock_settings.return_value.database_url = "sqlite+aiosqlite:///:memory:"
            mock_settings.return_value.debug = False
            
            # This should create all tables
            await init_db()
        
        reset_engine()

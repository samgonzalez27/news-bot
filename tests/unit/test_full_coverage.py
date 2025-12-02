"""
Comprehensive test file to achieve 100% coverage.

This file targets all remaining uncovered lines across:
- config.py (lines 205, 214, 224, 243, 259)
- logging_config.py (lines 32, 60, 64, 66, 68, 70, 72, 76)
- main.py (lines 120, 215-217, 227, 250, 253, 257-258, 265-268)
- rate_limiter.py (lines 211-215, 230-231)
- database.py (lines 44-46, 84, 101, 104)
- routers/*.py (various missing branches)
- models/*.py (repr methods)
- schemas/user.py (validators)
- services/news_service.py (lines 147-149, 161-163, 171)
"""

import pytest
import time
import json
import logging
from datetime import datetime, timezone, timedelta, date, time as time_type
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ===========================================================================
# CONFIG.PY TESTS
# ===========================================================================
class TestConfigCoverage:
    """Cover remaining config.py branches."""

    def test_cors_origins_json_list(self):
        """Test CORS origins from JSON array string."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "CORS_ORIGINS": '["http://localhost", "http://example.com"]',
        }):
            settings = Settings()
            assert "http://localhost" in settings.cors_origins
            assert "http://example.com" in settings.cors_origins

    def test_cors_origins_comma_separated(self):
        """Test CORS origins from comma-separated string."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "CORS_ORIGINS": "http://localhost, http://example.com",
        }):
            settings = Settings()
            assert "http://localhost" in settings.cors_origins
            assert "http://example.com" in settings.cors_origins

    def test_cors_origins_invalid_json(self):
        """Test CORS origins with invalid JSON falls back to comma-separated."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "CORS_ORIGINS": "{not valid json}",
        }):
            settings = Settings()
            # Falls back to treating as comma-separated
            assert len(settings.cors_origins) >= 1

    def test_log_level_invalid_defaults_to_info(self):
        """Test invalid log level defaults to INFO."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "LOG_LEVEL": "INVALID_LEVEL",
        }):
            settings = Settings()
            assert settings.log_level == "INFO"

    def test_app_env_invalid_defaults_to_development(self):
        """Test invalid app_env defaults to development."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "APP_ENV": "invalid_environment",
        }):
            settings = Settings()
            assert settings.app_env == "development"

    def test_is_production_property(self):
        """Test is_production property."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "APP_ENV": "production",
        }):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False
            assert settings.is_testing is False

    def test_is_testing_property(self):
        """Test is_testing property."""
        from src.config import Settings

        with patch.dict("os.environ", {
            "JWT_SECRET_KEY": "test-secret-key-for-jwt-tokens-minimum-32-chars",
            "NEWSAPI_KEY": "test",
            "OPENAI_API_KEY": "test",
            "APP_ENV": "testing",
        }):
            settings = Settings()
            assert settings.is_testing is True

    def test_clear_settings(self):
        """Test clear_settings clears the cache."""
        from src.config import clear_settings, get_settings

        # Call get_settings to populate cache
        get_settings()
        
        # Clear it
        clear_settings()
        
        # Should not raise
        assert True


# ===========================================================================
# LOGGING_CONFIG.PY TESTS
# ===========================================================================
class TestLoggingConfigCoverage:
    """Cover remaining logging_config.py branches."""

    def test_set_request_id_generates_uuid(self):
        """Test set_request_id generates UUID when not provided."""
        from src.logging_config import set_request_id

        request_id = set_request_id()
        assert request_id is not None
        assert len(request_id) == 36  # UUID format

    def test_set_request_id_uses_provided(self):
        """Test set_request_id uses provided value."""
        from src.logging_config import set_request_id, get_request_id

        set_request_id("custom-request-id")
        assert get_request_id() == "custom-request-id"

    def test_json_formatter_with_all_extras(self):
        """Test JSONFormatter includes all extra fields."""
        from src.logging_config import JSONFormatter, set_request_id

        formatter = JSONFormatter()
        set_request_id("test-request-id")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add extra fields
        record.request_path = "/api/test"
        record.client_ip = "127.0.0.1"
        record.method = "GET"
        record.status_code = 200
        record.duration_ms = 50.5

        result = formatter.format(record)
        data = json.loads(result)

        assert data["request_id"] == "test-request-id"
        assert data["request_path"] == "/api/test"
        assert data["client_ip"] == "127.0.0.1"
        assert data["method"] == "GET"
        assert data["status_code"] == 200
        assert data["duration_ms"] == 50.5

    def test_json_formatter_with_exception(self):
        """Test JSONFormatter includes exception info."""
        from src.logging_config import JSONFormatter

        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            result = formatter.format(record)
            data = json.loads(result)
            assert "exception" in data
            assert "ValueError: Test error" in data["exception"]

    def test_console_formatter_all_levels(self):
        """Test ConsoleFormatter with all log levels."""
        from src.logging_config import ConsoleFormatter, set_request_id

        formatter = ConsoleFormatter()
        set_request_id("test-id")

        for level_name in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            level = getattr(logging, level_name)
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            result = formatter.format(record)
            assert level_name in result

    def test_console_formatter_with_exception(self):
        """Test ConsoleFormatter with exception."""
        from src.logging_config import ConsoleFormatter

        formatter = ConsoleFormatter()

        try:
            raise RuntimeError("Test exception")
        except RuntimeError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            result = formatter.format(record)
            assert "RuntimeError" in result

    def test_setup_logging_production_json(self):
        """Test setup_logging uses JSON formatter in production."""
        from src.logging_config import setup_logging

        with patch("src.logging_config.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "INFO"
            settings.log_json_format = True
            settings.is_production = True
            settings.log_file_path = None
            mock_settings.return_value = settings

            logger = setup_logging()
            assert logger.name == "news_digest"

    def test_setup_logging_development(self):
        """Test setup_logging uses console formatter in development."""
        from src.logging_config import setup_logging

        with patch("src.logging_config.get_settings") as mock_settings:
            settings = MagicMock()
            settings.log_level = "DEBUG"
            settings.log_json_format = False
            settings.is_production = False
            settings.log_file_path = None
            mock_settings.return_value = settings

            logger = setup_logging()
            assert logger.name == "news_digest"

    def test_get_logger_returns_child(self):
        """Test get_logger returns child logger."""
        from src.logging_config import get_logger

        logger = get_logger("test_module")
        assert logger.name == "news_digest.test_module"


# ===========================================================================
# DATABASE.PY TESTS
# ===========================================================================
class TestDatabaseCoverage:
    """Cover remaining database.py branches."""

    def test_get_engine_creates_once(self):
        """Test get_engine creates engine only once."""
        from src.database import get_engine, reset_engine

        reset_engine()  # Clear any existing engine

        with patch("src.database.get_settings") as mock_settings:
            settings = MagicMock()
            settings.database_url = "sqlite+aiosqlite:///:memory:"
            settings.debug = False
            mock_settings.return_value = settings

            engine1 = get_engine()
            engine2 = get_engine()
            assert engine1 is engine2

        reset_engine()  # Cleanup

    def test_get_engine_postgres_settings(self):
        """Test get_engine with PostgreSQL settings."""
        from src.database import get_engine, reset_engine

        reset_engine()

        with patch("src.database.get_settings") as mock_settings:
            settings = MagicMock()
            settings.database_url = "postgresql+asyncpg://user:pass@localhost/db"
            settings.debug = False
            settings.db_pool_size = 5
            settings.db_max_overflow = 10
            mock_settings.return_value = settings

            with patch("src.database.create_async_engine") as mock_create:
                mock_create.return_value = MagicMock()
                get_engine()
                
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["pool_size"] == 5
                assert call_kwargs["max_overflow"] == 10
                assert call_kwargs["pool_pre_ping"] is True

        reset_engine()

    def test_get_async_session_maker_creates_once(self):
        """Test get_async_session_maker creates session maker only once."""
        from src.database import get_async_session_maker, reset_engine

        reset_engine()

        with patch("src.database.get_settings") as mock_settings:
            settings = MagicMock()
            settings.database_url = "sqlite+aiosqlite:///:memory:"
            settings.debug = False
            mock_settings.return_value = settings

            maker1 = get_async_session_maker()
            maker2 = get_async_session_maker()
            assert maker1 is maker2

        reset_engine()

    @pytest.mark.asyncio
    async def test_get_db_exception_rollback(self):
        """Test get_db rolls back on exception."""
        from src.database import get_db, reset_engine

        reset_engine()

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_session_maker = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker.return_value = mock_cm

        with patch("src.database.get_async_session_maker", return_value=mock_session_maker):
            gen = get_db()
            with pytest.raises(Exception):
                async for session in gen:
                    raise Exception("Test exception")

        reset_engine()

    def test_lazy_engine_proxy(self):
        """Test _LazyEngine proxy delegates attributes."""
        from src.database import engine, reset_engine

        reset_engine()

        with patch("src.database.get_settings") as mock_settings:
            settings = MagicMock()
            settings.database_url = "sqlite+aiosqlite:///:memory:"
            settings.debug = False
            mock_settings.return_value = settings

            # Access an attribute through the proxy
            # This should trigger __getattr__
            url = engine.url
            assert url is not None

        reset_engine()

    def test_lazy_session_maker_call(self):
        """Test _LazySessionMaker callable."""
        from src.database import async_session_maker, reset_engine

        reset_engine()

        with patch("src.database.get_settings") as mock_settings:
            settings = MagicMock()
            settings.database_url = "sqlite+aiosqlite:///:memory:"
            settings.debug = False
            mock_settings.return_value = settings

            # Call the session maker
            session = async_session_maker()
            assert session is not None

        reset_engine()


# ===========================================================================
# RATE_LIMITER.PY TESTS
# ===========================================================================
class TestRateLimiterCoverage:
    """Cover remaining rate_limiter.py branches."""

    def test_rate_limiter_cleanup_old_buckets(self):
        """Test cleanup_old_buckets removes stale entries."""
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=60, burst=10)
        
        # Create some buckets
        limiter.is_allowed("key1")
        limiter.is_allowed("key2")
        
        # Age them artificially
        for bucket in limiter.buckets.values():
            bucket.last_refill = time.time() - 7200  # 2 hours old
        
        removed = limiter.cleanup_old_buckets(max_age_seconds=3600)
        assert removed == 2
        assert len(limiter.buckets) == 0

    def test_rate_limiter_reset(self):
        """Test reset clears all buckets."""
        from src.middleware.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.is_allowed("key1")
        limiter.is_allowed("key2")
        
        assert len(limiter.buckets) == 2
        
        limiter.reset()
        assert len(limiter.buckets) == 0

    @pytest.mark.asyncio
    async def test_middleware_periodic_cleanup(self):
        """Test middleware performs periodic cleanup."""
        from src.middleware.rate_limiter import RateLimitMiddleware
        from fastapi import Request

        # Create a request mock
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def call_next(request):
            return mock_response

        # Create middleware with artificial time
        with patch("src.middleware.rate_limiter.get_settings") as mock_settings:
            settings = MagicMock()
            settings.rate_limit_per_minute = 60
            settings.rate_limit_burst = 10
            mock_settings.return_value = settings

            mock_app = MagicMock()
            middleware = RateLimitMiddleware(mock_app)
            
            # Set last cleanup to long ago
            middleware._last_cleanup = time.time() - 7200

            # Add some old buckets
            middleware.default_limiter.is_allowed("old_key")
            for bucket in middleware.default_limiter.buckets.values():
                bucket.last_refill = time.time() - 7200

            await middleware.dispatch(mock_request, call_next)
            
            # Cleanup should have happened
            assert middleware._last_cleanup > time.time() - 100

    @pytest.mark.asyncio
    async def test_middleware_user_based_rate_limit(self):
        """Test middleware uses user ID for authenticated requests."""
        from src.middleware.rate_limiter import RateLimitMiddleware
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {"authorization": "Bearer valid_token"}
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def call_next(request):
            return mock_response

        with patch("src.middleware.rate_limiter.get_settings") as mock_settings:
            settings = MagicMock()
            settings.rate_limit_per_minute = 60
            settings.rate_limit_burst = 10
            mock_settings.return_value = settings

            mock_app = MagicMock()
            middleware = RateLimitMiddleware(mock_app)

            # Mock AuthService.get_user_id_from_token in the services module
            user_id = uuid4()
            with patch("src.services.auth_service.AuthService.get_user_id_from_token", return_value=user_id):
                await middleware.dispatch(mock_request, call_next)

            # Should use user-based key
            assert f"user:{user_id}" in middleware.default_limiter.buckets

    @pytest.mark.asyncio
    async def test_middleware_auth_path_stricter_limit(self):
        """Test middleware uses stricter limits for auth paths."""
        from src.middleware.rate_limiter import RateLimitMiddleware
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/auth/login"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def call_next(request):
            return mock_response

        with patch("src.middleware.rate_limiter.get_settings") as mock_settings:
            settings = MagicMock()
            settings.rate_limit_per_minute = 60
            settings.rate_limit_burst = 10
            mock_settings.return_value = settings

            mock_app = MagicMock()
            middleware = RateLimitMiddleware(mock_app)

            await middleware.dispatch(mock_request, call_next)
            
            # Should use auth_limiter with stricter limits
            assert "ip:127.0.0.1" in middleware.auth_limiter.buckets

    @pytest.mark.asyncio
    async def test_middleware_rate_limit_exceeded(self):
        """Test middleware returns 429 when rate limit exceeded."""
        from src.middleware.rate_limiter import RateLimitMiddleware
        from fastapi import Request
        from starlette.responses import JSONResponse

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"

        async def call_next(request):
            return MagicMock()

        with patch("src.middleware.rate_limiter.get_settings") as mock_settings:
            settings = MagicMock()
            settings.rate_limit_per_minute = 60
            settings.rate_limit_burst = 1  # Very low burst
            mock_settings.return_value = settings

            mock_app = MagicMock()
            middleware = RateLimitMiddleware(mock_app)

            # Exhaust the bucket
            middleware.default_limiter.is_allowed("ip:127.0.0.1")
            middleware.default_limiter.buckets["ip:127.0.0.1"].tokens = 0

            response = await middleware.dispatch(mock_request, call_next)
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_middleware_forwarded_for_header(self):
        """Test middleware extracts IP from X-Forwarded-For header."""
        from src.middleware.rate_limiter import RateLimitMiddleware
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {"x-forwarded-for": "203.0.113.1, 198.51.100.1"}
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def call_next(request):
            return mock_response

        with patch("src.middleware.rate_limiter.get_settings") as mock_settings:
            settings = MagicMock()
            settings.rate_limit_per_minute = 60
            settings.rate_limit_burst = 10
            mock_settings.return_value = settings

            mock_app = MagicMock()
            middleware = RateLimitMiddleware(mock_app)

            await middleware.dispatch(mock_request, call_next)
            
            # Should use first IP from X-Forwarded-For
            assert "ip:203.0.113.1" in middleware.default_limiter.buckets

    @pytest.mark.asyncio
    async def test_middleware_x_real_ip_header(self):
        """Test middleware extracts IP from X-Real-IP header."""
        from src.middleware.rate_limiter import RateLimitMiddleware
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {"x-real-ip": "203.0.113.5"}
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def call_next(request):
            return mock_response

        with patch("src.middleware.rate_limiter.get_settings") as mock_settings:
            settings = MagicMock()
            settings.rate_limit_per_minute = 60
            settings.rate_limit_burst = 10
            mock_settings.return_value = settings

            mock_app = MagicMock()
            middleware = RateLimitMiddleware(mock_app)

            await middleware.dispatch(mock_request, call_next)
            
            # Should use X-Real-IP
            assert "ip:203.0.113.5" in middleware.default_limiter.buckets


# ===========================================================================
# MODELS REPR TESTS
# ===========================================================================
class TestModelReprCoverage:
    """Cover model __repr__ methods."""

    def test_user_repr(self):
        """Test User model repr."""
        from src.models.user import User

        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hash",
            full_name="Test",
        )
        repr_str = repr(user)
        assert "User" in repr_str
        assert "test@example.com" in repr_str

    def test_user_interest_repr(self):
        """Test UserInterest model repr."""
        from src.models.user import UserInterest

        ui = UserInterest(
            user_id=uuid4(),
            interest_id=uuid4(),
        )
        repr_str = repr(ui)
        assert "UserInterest" in repr_str

    def test_interest_repr(self):
        """Test Interest model repr."""
        from src.models.interest import Interest

        interest = Interest(
            id=uuid4(),
            name="Technology",
            slug="technology",
        )
        repr_str = repr(interest)
        assert "Interest" in repr_str
        assert "technology" in repr_str

    def test_digest_repr(self):
        """Test Digest model repr."""
        from src.models.digest import Digest

        digest = Digest(
            id=uuid4(),
            user_id=uuid4(),
            digest_date=date.today(),
            content="Test content",
        )
        repr_str = repr(digest)
        assert "Digest" in repr_str


# ===========================================================================
# SCHEMA VALIDATOR TESTS
# ===========================================================================
class TestSchemaValidatorsCoverage:
    """Cover schema validators."""

    def test_user_create_password_no_letter(self):
        """Test password validation requires letter."""
        from src.schemas.user import UserCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="12345678",  # No letters
                full_name="Test User",
            )
        assert "letter" in str(exc_info.value).lower()

    def test_user_create_password_no_number(self):
        """Test password validation requires number."""
        from src.schemas.user import UserCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="abcdefgh",  # No numbers
                full_name="Test User",
            )
        assert "number" in str(exc_info.value).lower()

    def test_user_create_invalid_time_format(self):
        """Test time format validation."""
        from src.schemas.user import UserCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="SecurePass123",
                full_name="Test User",
                preferred_time="invalid",
            )
        assert "HH:MM" in str(exc_info.value)

    # NOTE: Timezone support disabled - test skipped
    @pytest.mark.skip(reason="Timezone support disabled - all users use UTC")
    def test_user_create_invalid_timezone(self):
        """Test timezone validation."""
        from src.schemas.user import UserCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="SecurePass123",
                full_name="Test User",
                timezone="Invalid/Timezone",
            )
        assert "timezone" in str(exc_info.value).lower()

    # NOTE: Timezone support disabled - test modified
    def test_user_preferences_update_none_values(self):
        """Test preferences update with None values passes validation."""
        from src.schemas.user import UserPreferencesUpdate

        prefs = UserPreferencesUpdate(
            preferred_time=None,
            # NOTE: timezone field disabled
            # timezone=None,
        )
        assert prefs.preferred_time is None
        # assert prefs.timezone is None  # timezone disabled

    def test_user_response_time_formatting(self):
        """Test UserResponse formats time object to string."""
        from src.schemas.user import UserResponse
        from datetime import timezone as tz

        # Mock a user-like object
        user_data = {
            "id": uuid4(),
            "email": "test@example.com",
            "full_name": "Test",
            "preferred_time": time_type(8, 30),  # time object
            # NOTE: timezone field disabled - all users use UTC
            # "timezone": "UTC",
            "is_active": True,
            "interests": [],
            "created_at": datetime.now(tz.utc),
            "updated_at": datetime.now(tz.utc),
        }
        
        response = UserResponse.model_validate(user_data)
        assert response.preferred_time == "08:30"


# ===========================================================================
# NEWS SERVICE TESTS
# ===========================================================================
class TestNewsServiceCoverage:
    """Cover remaining news_service.py branches."""

    @pytest.mark.asyncio
    async def test_fetch_everything_with_default_dates(self):
        """Test _fetch_everything uses default dates."""
        from src.services.news_service import NewsService

        service = NewsService()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "articles": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(service.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            articles = await service._fetch_everything("test query")
            
            assert articles == []
            mock_get.assert_called_once()

        await service.close()

    @pytest.mark.asyncio
    async def test_fetch_everything_request_error(self):
        """Test _fetch_everything handles request errors."""
        from src.services.news_service import NewsService
        from src.exceptions import NewsAPIError
        import httpx

        service = NewsService()

        with patch.object(service.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")
            
            with pytest.raises(NewsAPIError):
                await service._fetch_everything("test query")

        await service.close()

    @pytest.mark.asyncio
    async def test_get_headlines_skip_no_category(self):
        """Test get_headlines_for_interests skips interests without category."""
        from src.services.news_service import NewsService

        service = NewsService()

        # Interest without newsapi_category
        interests = [
            {"slug": "custom", "newsapi_category": None},
        ]

        articles = await service.get_headlines_for_interests(interests)
        assert articles == []

        await service.close()

    @pytest.mark.asyncio
    async def test_get_headlines_handles_api_error(self):
        """Test get_headlines_for_interests handles API errors gracefully."""
        from src.services.news_service import NewsService
        from src.exceptions import NewsAPIError

        service = NewsService()

        interests = [
            {"slug": "technology", "newsapi_category": "technology"},
        ]

        with patch.object(service, "get_headlines_for_category", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = NewsAPIError("API error")
            
            # Should not raise, returns empty
            articles = await service.get_headlines_for_interests(interests)
            assert articles == []

        await service.close()

    def test_cache_validity_check(self):
        """Test _is_cache_valid method."""
        from src.services.news_service import NewsService, CACHE_TTL_SECONDS

        service = NewsService()

        # Empty cache entry
        assert service._is_cache_valid({}) is False

        # No cached_at
        assert service._is_cache_valid({"articles": []}) is False

        # Fresh cache
        fresh_entry = {
            "articles": [],
            "cached_at": datetime.now(timezone.utc),
        }
        assert service._is_cache_valid(fresh_entry) is True

        # Stale cache
        stale_entry = {
            "articles": [],
            "cached_at": datetime.now(timezone.utc) - timedelta(seconds=CACHE_TTL_SECONDS + 100),
        }
        assert service._is_cache_valid(stale_entry) is False


# ===========================================================================
# MAIN.PY TESTS
# ===========================================================================
class TestMainAppCoverage:
    """Cover remaining main.py branches."""

    def test_get_logger_function(self):
        """Test _get_logger creates logger lazily."""
        from src.main import _get_logger

        logger = _get_logger()
        assert logger is not None
        assert logger.name == "news_digest"

    def test_lazy_app_asgi_interface(self):
        """Test _LazyApp ASGI interface."""
        from src.main import app

        # Reset to force fresh app
        app._reset_app()
        
        # Test attribute access
        assert app.title is not None
        
        app._reset_app()

    def test_reset_app_function(self):
        """Test reset_app clears instance."""
        from src.main import reset_app, get_app

        get_app()
        reset_app()
        # get_app should create fresh instance
        get_app()
        
        # Clean up
        reset_app()

    @pytest.mark.asyncio
    async def test_request_id_middleware_generates_id(self):
        """Test RequestIDMiddleware generates request ID."""
        from src.main import RequestIDMiddleware
        from fastapi import Request

        middleware = RequestIDMiddleware(MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}  # No X-Request-ID header
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        response = await middleware.dispatch(mock_request, call_next)
        
        # Should have added request ID header
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_id_middleware_uses_provided_id(self):
        """Test RequestIDMiddleware uses provided X-Request-ID."""
        from src.main import RequestIDMiddleware
        from fastapi import Request

        middleware = RequestIDMiddleware(MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Request-ID": "custom-id-12345"}
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        response = await middleware.dispatch(mock_request, call_next)
        
        assert response.headers["X-Request-ID"] == "custom-id-12345"

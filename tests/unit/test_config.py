"""
Unit tests for config module.
"""

from unittest.mock import patch
import os


# Valid test secret key (must be at least 32 characters)
TEST_SECRET_KEY = "test-secret-key-that-is-at-least-32-chars-long"


class TestSettings:
    """Tests for Settings class."""

    def test_cors_origins_json_string(self):
        """Should parse JSON array string."""
        from src.config import Settings
        
        with patch.dict(os.environ, {
            "JWT_SECRET_KEY": TEST_SECRET_KEY,
            "NEWSAPI_KEY": "test-news-key",
            "OPENAI_API_KEY": "test-openai-key",
            "CORS_ORIGINS": '["http://localhost:3000", "http://localhost:8080"]',
        }):
            # Clear cache
            from src.config import get_settings
            get_settings.cache_clear()
            
            settings = Settings()
            assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_cors_origins_comma_separated(self):
        """Should parse comma-separated string."""
        from src.config import Settings
        
        with patch.dict(os.environ, {
            "JWT_SECRET_KEY": TEST_SECRET_KEY,
            "NEWSAPI_KEY": "test-news-key",
            "OPENAI_API_KEY": "test-openai-key",
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
        }):
            from src.config import get_settings
            get_settings.cache_clear()
            
            settings = Settings()
            assert "http://localhost:3000" in settings.cors_origins
            assert "http://localhost:8080" in settings.cors_origins

    def test_is_production(self):
        """Should detect production environment."""
        from src.config import Settings
        
        with patch.dict(os.environ, {
            "JWT_SECRET_KEY": TEST_SECRET_KEY,
            "NEWSAPI_KEY": "test-news-key",
            "OPENAI_API_KEY": "test-openai-key",
            "APP_ENV": "production",
        }):
            from src.config import get_settings
            get_settings.cache_clear()
            
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False

    def test_is_development(self):
        """Should detect development environment."""
        from src.config import Settings
        
        with patch.dict(os.environ, {
            "JWT_SECRET_KEY": TEST_SECRET_KEY,
            "NEWSAPI_KEY": "test-news-key",
            "OPENAI_API_KEY": "test-openai-key",
            "APP_ENV": "development",
        }):
            from src.config import get_settings
            get_settings.cache_clear()
            
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

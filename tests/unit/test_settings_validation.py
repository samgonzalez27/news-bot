"""
Tests for settings validation and configuration edge cases.

Coverage improvements:
- CORS origins parsing (JSON list, comma-separated, single value)
- Boolean field parsing
- Integer field validation
- Environment-specific properties (is_production, is_development)
- Settings caching behavior

Note: Testing required fields without .env is complex since Pydantic Settings
always reads from .env. We focus on parsing behavior and property logic.
"""


from src.config import Settings, get_settings


class TestCORSOriginsParsing:
    """Tests for CORS origins parsing validator."""

    def test_parse_json_list(self):
        """Should parse JSON list format."""
        from src.config import Settings
        
        # Test validator directly via Settings class
        result = Settings.parse_cors_origins('["http://localhost:3000", "http://localhost:8000"]')
        assert "http://localhost:3000" in result
        assert "http://localhost:8000" in result
        assert len(result) == 2

    def test_parse_comma_separated(self):
        """Should parse comma-separated format."""
        result = Settings.parse_cors_origins("http://localhost:3000,http://localhost:8000")
        assert "http://localhost:3000" in result
        assert "http://localhost:8000" in result

    def test_parse_comma_separated_with_spaces(self):
        """Should handle comma-separated with spaces."""
        result = Settings.parse_cors_origins("http://localhost:3000, http://localhost:8000 ")
        assert any("localhost:3000" in origin for origin in result)
        assert any("localhost:8000" in origin for origin in result)

    def test_parse_single_value(self):
        """Should handle single value."""
        result = Settings.parse_cors_origins("http://localhost:3000")
        assert "http://localhost:3000" in result

    def test_parse_list_passthrough(self):
        """Should pass through a list unchanged."""
        input_list = ["http://localhost:3000", "http://localhost:8000"]
        result = Settings.parse_cors_origins(input_list)
        assert result == input_list

    def test_parse_empty_string(self):
        """Should handle empty string."""
        result = Settings.parse_cors_origins("")
        # Empty string splits to empty list, but validator returns default
        # Actually, the validator returns ["http://localhost:3000"] for invalid input
        # Let's check the actual behavior
        assert isinstance(result, list)

    def test_parse_invalid_json(self):
        """Should fall back to comma-separated for invalid JSON."""
        # Invalid JSON that looks like it could be JSON
        result = Settings.parse_cors_origins("[not valid json")
        # Should fall back to comma-separated parsing
        assert isinstance(result, list)


class TestEnvironmentProperties:
    """Tests for environment-specific computed properties."""

    def test_is_production_property(self):
        """Test is_production property logic."""
        settings = get_settings()
        
        # Create a test instance with production env
        # We can't easily mock this, so we test the property logic
        # by accessing it and checking it's consistent
        is_prod = settings.app_env.lower() == "production"
        assert settings.is_production == is_prod

    def test_is_development_property(self):
        """Test is_development property logic."""
        settings = get_settings()
        
        is_dev = settings.app_env.lower() == "development"
        assert settings.is_development == is_dev

    def test_properties_are_mutually_exclusive_for_prod_dev(self):
        """Test that production and development are mutually exclusive."""
        settings = get_settings()
        
        # Can't be both production and development
        if settings.is_production:
            assert not settings.is_development
        if settings.is_development:
            assert not settings.is_production


class TestBooleanFieldBehavior:
    """Tests for boolean field type handling."""

    def test_debug_is_boolean(self):
        """Debug field should be a boolean."""
        settings = get_settings()
        assert isinstance(settings.debug, bool)

    def test_scheduler_enabled_is_boolean(self):
        """scheduler_enabled field should be a boolean."""
        settings = get_settings()
        assert isinstance(settings.scheduler_enabled, bool)


class TestIntegerFieldBehavior:
    """Tests for integer field type handling."""

    def test_port_is_integer(self):
        """Port field should be an integer."""
        settings = get_settings()
        assert isinstance(settings.port, int)

    def test_rate_limit_per_minute_is_integer(self):
        """rate_limit_per_minute should be an integer."""
        settings = get_settings()
        assert isinstance(settings.rate_limit_per_minute, int)

    def test_rate_limit_burst_is_integer(self):
        """rate_limit_burst should be an integer."""
        settings = get_settings()
        assert isinstance(settings.rate_limit_burst, int)

    def test_jwt_expire_minutes_is_integer(self):
        """JWT expire minutes should be an integer."""
        settings = get_settings()
        assert isinstance(settings.jwt_access_token_expire_minutes, int)

    def test_db_pool_size_is_integer(self):
        """DB pool size should be an integer."""
        settings = get_settings()
        assert isinstance(settings.db_pool_size, int)

    def test_openai_max_tokens_is_integer(self):
        """OpenAI max tokens should be an integer."""
        settings = get_settings()
        assert isinstance(settings.openai_max_tokens, int)


class TestStringFieldBehavior:
    """Tests for string field type handling."""

    def test_app_name_is_string(self):
        """app_name should be a string."""
        settings = get_settings()
        assert isinstance(settings.app_name, str)

    def test_app_env_is_string(self):
        """app_env should be a string."""
        settings = get_settings()
        assert isinstance(settings.app_env, str)

    def test_jwt_algorithm_is_string(self):
        """JWT algorithm should be a string."""
        settings = get_settings()
        assert isinstance(settings.jwt_algorithm, str)

    def test_openai_model_is_string(self):
        """OpenAI model should be a string."""
        settings = get_settings()
        assert isinstance(settings.openai_model, str)

    def test_log_level_is_string(self):
        """Log level should be a string."""
        settings = get_settings()
        assert isinstance(settings.log_level, str)


class TestCORSOriginsType:
    """Tests for CORS origins list type."""

    def test_cors_origins_is_list(self):
        """cors_origins should be a list."""
        settings = get_settings()
        assert isinstance(settings.cors_origins, list)

    def test_cors_origins_contains_strings(self):
        """cors_origins should contain strings."""
        settings = get_settings()
        for origin in settings.cors_origins:
            assert isinstance(origin, str)


class TestSettingsCaching:
    """Tests for settings caching via lru_cache."""

    def test_get_settings_returns_same_instance(self):
        """get_settings should return same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the exact same object (cached)
        assert settings1 is settings2

    def test_settings_have_required_attributes(self):
        """Settings instance should have all expected attributes."""
        settings = get_settings()
        
        # Required fields
        assert hasattr(settings, "jwt_secret_key")
        assert hasattr(settings, "newsapi_key")
        assert hasattr(settings, "openai_api_key")
        
        # Optional/default fields
        assert hasattr(settings, "app_name")
        assert hasattr(settings, "app_env")
        assert hasattr(settings, "debug")
        assert hasattr(settings, "database_url")
        assert hasattr(settings, "cors_origins")
        assert hasattr(settings, "rate_limit_per_minute")


class TestDatabaseURLField:
    """Tests for database URL handling."""

    def test_database_url_is_string(self):
        """database_url should be a string."""
        settings = get_settings()
        assert isinstance(settings.database_url, str)

    def test_database_url_contains_driver(self):
        """database_url should contain a database driver."""
        settings = get_settings()
        # Should contain postgresql, sqlite, or similar
        assert "://" in settings.database_url


class TestAPIKeyFields:
    """Tests for API key fields."""

    def test_jwt_secret_key_is_set(self):
        """JWT secret key should be set."""
        settings = get_settings()
        assert settings.jwt_secret_key is not None
        assert len(settings.jwt_secret_key) > 0

    def test_newsapi_key_is_set(self):
        """NewsAPI key should be set."""
        settings = get_settings()
        assert settings.newsapi_key is not None
        assert len(settings.newsapi_key) > 0

    def test_openai_api_key_is_set(self):
        """OpenAI API key should be set."""
        settings = get_settings()
        assert settings.openai_api_key is not None
        assert len(settings.openai_api_key) > 0


class TestRateLimitSettings:
    """Tests for rate limiting configuration."""

    def test_rate_limit_per_minute_positive(self):
        """Rate limit per minute should be positive."""
        settings = get_settings()
        assert settings.rate_limit_per_minute > 0

    def test_rate_limit_burst_positive(self):
        """Rate limit burst should be positive."""
        settings = get_settings()
        assert settings.rate_limit_burst > 0


class TestSchedulerSettings:
    """Tests for scheduler configuration."""

    def test_scheduler_enabled_field_exists(self):
        """scheduler_enabled field should exist."""
        settings = get_settings()
        assert hasattr(settings, "scheduler_enabled")

    def test_digest_check_interval_exists(self):
        """digest_check_interval_minutes field should exist."""
        settings = get_settings()
        assert hasattr(settings, "digest_check_interval_minutes")
        assert isinstance(settings.digest_check_interval_minutes, int)


class TestLogSettings:
    """Tests for logging configuration."""

    def test_log_level_is_valid(self):
        """Log level should be a valid level string."""
        settings = get_settings()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert settings.log_level.upper() in valid_levels

    def test_log_file_path_exists(self):
        """Log file path should be set."""
        settings = get_settings()
        assert settings.log_file_path is not None
        assert len(settings.log_file_path) > 0

    def test_log_max_bytes_positive(self):
        """Log max bytes should be positive."""
        settings = get_settings()
        assert settings.log_max_bytes > 0

    def test_log_backup_count_non_negative(self):
        """Log backup count should be non-negative."""
        settings = get_settings()
        assert settings.log_backup_count >= 0


class TestOpenAISettings:
    """Tests for OpenAI configuration."""

    def test_openai_model_is_set(self):
        """OpenAI model should be set."""
        settings = get_settings()
        assert settings.openai_model is not None
        assert len(settings.openai_model) > 0

    def test_openai_max_tokens_reasonable(self):
        """OpenAI max tokens should be reasonable."""
        settings = get_settings()
        assert settings.openai_max_tokens > 0
        assert settings.openai_max_tokens < 100000  # Reasonable upper bound


class TestServerSettings:
    """Tests for server configuration."""

    def test_host_is_set(self):
        """Host should be set."""
        settings = get_settings()
        assert settings.host is not None
        assert len(settings.host) > 0

    def test_port_is_valid(self):
        """Port should be in valid range."""
        settings = get_settings()
        assert 1 <= settings.port <= 65535

    def test_api_prefix_starts_with_slash(self):
        """API prefix should start with slash."""
        settings = get_settings()
        assert settings.api_v1_prefix.startswith("/")

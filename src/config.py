"""
Configuration management for the News Digest API.

Uses Pydantic Settings for environment variable parsing and validation.
All settings can be configured via environment variables or .env file.
"""

from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Required environment variables:
        - JWT_SECRET_KEY: Secret key for JWT token signing (min 32 chars)
        - NEWSAPI_KEY: API key for NewsAPI.org
        - OPENAI_API_KEY: API key for OpenAI
        - DATABASE_URL: PostgreSQL connection string
        
    All other settings have sensible defaults for production use.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="None",
    )

    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    app_name: str = Field(
        default="NewsDigestAPI",
        description="Application name displayed in docs and logs",
    )
    app_env: str = Field(
        default="development",
        description="Environment: development, staging, production, testing",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (additional logging, stack traces)",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API version prefix for all routes",
    )

    # -------------------------------------------------------------------------
    # Server Settings
    # -------------------------------------------------------------------------
    host: str = Field(
        default="0.0.0.0",
        description="Server bind address",
    )
    port: int = Field(
        default=8000,
        description="Server port",
    )

    # -------------------------------------------------------------------------
    # Database Settings
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://newsdigest:password@localhost:5432/newsdigest_db",
        description="PostgreSQL async connection URL",
    )
    db_pool_size: int = Field(
        default=5,
        description="Database connection pool size",
        ge=1,
        le=50,
    )
    db_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections beyond pool size",
        ge=0,
        le=50,
    )

    # -------------------------------------------------------------------------
    # JWT Authentication Settings
    # -------------------------------------------------------------------------
    jwt_secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT token signing (min 32 characters)",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=1440,
        description="JWT token expiration time in minutes (default: 24 hours)",
        ge=1,
    )

    # -------------------------------------------------------------------------
    # External API Settings
    # -------------------------------------------------------------------------
    newsapi_key: str = Field(
        ...,
        description="NewsAPI.org API key",
    )
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for digest generation",
    )
    openai_max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for OpenAI responses",
        ge=100,
        le=16000,
    )

    # -------------------------------------------------------------------------
    # Rate Limiting Settings
    # -------------------------------------------------------------------------
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per client",
        ge=1,
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Burst allowance for rate limiting",
        ge=1,
    )

    # -------------------------------------------------------------------------
    # Logging Settings
    # -------------------------------------------------------------------------
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    log_file_path: Optional[str] = Field(
        default="/var/log/news-digest/app.log",
        description="Path for log file (set to None to disable file logging)",
    )
    log_max_bytes: int = Field(
        default=10485760,
        description="Maximum log file size in bytes (default: 10MB)",
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
    )
    log_json_format: bool = Field(
        default=True,
        description="Use JSON format for logs (recommended for production)",
    )

    # -------------------------------------------------------------------------
    # CORS Settings
    # -------------------------------------------------------------------------
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins (comma-separated string or JSON array)",
    )

    # -------------------------------------------------------------------------
    # Scheduler Settings
    # -------------------------------------------------------------------------
    scheduler_enabled: bool = Field(
        default=True,
        description="Enable the background scheduler for digest generation",
    )
    digest_check_interval_minutes: int = Field(
        default=15,
        description="Interval in minutes for checking digest generation",
        ge=1,
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v) -> str:
        """Validate and normalize log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = str(v).upper()
        if normalized not in valid_levels:
            return "INFO"
        return normalized

    @field_validator("app_env", mode="before")
    @classmethod
    def validate_app_env(cls, v) -> str:
        """Validate and normalize application environment."""
        valid_envs = {"development", "staging", "production", "testing"}
        normalized = str(v).lower()
        if normalized not in valid_envs:
            return "development"
        return normalized

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app_env.lower() == "testing"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.
    Call clear_settings() to reload settings if needed.
    """
    return Settings()


def clear_settings() -> None:
    """Clear cached settings to force reload on next access."""
    get_settings.cache_clear()

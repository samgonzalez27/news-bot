"""
Configuration management for the News Digest API.

Uses Pydantic Settings for environment variable parsing and validation.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="NewsDigestAPI")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api/v1")

    # Server
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://newsdigest:password@localhost:5432/newsdigest_db"
    )
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)

    # JWT Authentication
    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=1440)  # 24 hours

    # External APIs
    newsapi_key: str = Field(...)
    openai_api_key: str = Field(...)
    openai_model: str = Field(default="gpt-4o-mini")
    openai_max_tokens: int = Field(default=2000)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_burst: int = Field(default=10)

    # Logging
    log_level: str = Field(default="INFO")
    log_file_path: str = Field(default="/var/log/news-digest/app.log")
    log_max_bytes: int = Field(default=10485760)  # 10 MB
    log_backup_count: int = Field(default=5)

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # Scheduler
    scheduler_enabled: bool = Field(default=True)
    digest_check_interval_minutes: int = Field(default=15)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()

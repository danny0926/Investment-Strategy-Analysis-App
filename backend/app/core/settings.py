"""Application settings module."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, List

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseModel):
    """Security related settings."""

    secret_key: str = Field(default="change-me")
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    jwt_audience: str = "trade-journal"
    jwt_issuer: str = "trade-journal-api"


class DatabaseSettings(BaseModel):
    """Database settings."""

    url: str = Field(default="postgresql+psycopg2://postgres:postgres@db:5432/tradejournal")
    echo: bool = False


class BrokerFeatureFlags(BaseModel):
    """Feature flags for broker integrations."""

    enable_shioaji: bool = True
    enable_ibkr: bool = True
    enable_email_csv: bool = True


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", case_sensitive=False)

    environment: str = Field(default="development")
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[AnyHttpUrl] | List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    broker_flags: BrokerFeatureFlags = Field(default_factory=BrokerFeatureFlags)

    encryption_key: str = Field(default="0123456789abcdef0123456789abcdef")
    timezone: str = Field(default="Asia/Taipei")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()

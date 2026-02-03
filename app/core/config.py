"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "SecAPI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", min_length=32)

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://secapi:secapi@localhost:5432/secapi"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 3600

    # API Keys
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "secapi_"

    # API Key Reset
    RESET_TOKEN_EXPIRY_MINUTES: int = 15
    RESET_METHOD: Literal["console", "email"] = "console"

    # SMTP Configuration (for production email sending)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@secapi.io"
    SMTP_USE_TLS: bool = True


settings = Settings()

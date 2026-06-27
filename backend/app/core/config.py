"""Application configuration loaded from environment variables.

Single source of truth for every setting. Nothing in the codebase should read
``os.environ`` directly — always go through ``settings``.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- AI Provider ---
    AI_PROVIDER: Literal["ollama", "openai", "anthropic", "gemini", "openai_compatible"] = "ollama"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_API_KEY: str = ""
    OLLAMA_MODEL: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""

    OPENAI_COMPAT_BASE_URL: str = ""
    OPENAI_COMPAT_API_KEY: str = ""
    OPENAI_COMPAT_MODEL: str = ""

    # --- App ---
    APP_NAME: str = "Personal AI Learning Coach"
    APP_ENV: Literal["dev", "prod"] = "dev"
    DATABASE_URL: str = "postgresql+psycopg://coach:coach@postgres:5432/coach"
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Auth ---
    JWT_SECRET: str = "change-me-in-prod"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60 * 24 * 7  # 7 days

    # --- YouTube ---
    YOUTUBE_API_KEY: str = ""

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""
    INTERNAL_BOT_TOKEN: str = ""

    # --- Storage ---
    DATA_DIR: str = "/app/data"

    # --- Adaptive ---
    ADAPTIVE_REDUCE_THRESHOLD: float = 0.5
    ADAPTIVE_INCREASE_THRESHOLD: float = 0.85
    ADAPTIVE_COMPLETION_THRESHOLD: float = 0.8
    ADAPTIVE_MIN_DAILY_MINUTES: int = 15
    ADAPTIVE_MAX_DAILY_MINUTES: int = 240

    # --- CORS ---
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
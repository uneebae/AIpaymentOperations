"""Typed application settings, sourced from environment variables / .env.

Single source of truth for configuration — see backend/.env.example for the
full list of supported variables. Replaces scattered `os.getenv` calls so
every setting has one declared type, one default, and one place to look.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./apoe.db"
    anthropic_api_key: str | None = None
    cors_allow_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

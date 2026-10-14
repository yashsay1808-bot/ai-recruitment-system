"""
Application configuration management using pydantic-settings.
Supports environment-based configuration overrides, secure defaults, and provider configs.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for the AI Recruitment Platform."""

    # Project metadata
    PROJECT_NAME: str = "AI Recruitment Platform"
    VERSION: str = "4.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", description="Environment mode: development, testing, production")
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/recruitment_db",
        description="Database connection URL"
    )
    SQLITE_FALLBACK_URL: str = "sqlite:///./recruitment_system_v4.db"

    # MongoDB Atlas (accounts, sessions, candidate pools). Optional: the Mongo-backed routes answer
    # 503 until MONGODB_URI is set.
    MONGODB_URI: Optional[str] = Field(default=None, description="mongodb+srv://... connection string")
    MONGODB_DB: str = "recruitment"

    # LLM & Embedding Provider configuration (Configurable via env, never hardcoded)
    LLM_PROVIDER: str = Field(
        default="mock",
        description="LLM provider name: 'mock' for offline/testing, 'gemini' for Google GenAI"
    )
    LLM_MODEL: str = Field(
        default="gemini-1.5-flash",
        description="Configurable LLM model identifier"
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-004",
        description="Embedding model identifier"
    )
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API Key; optional when running with mock provider"
    )

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    SECRET_KEY: str = Field(
        default="super-secret-default-key-change-in-production",
        description="Secret key for signing sessions"
    )

    # Storage paths
    DATA_DIR: str = "data"
    CACHE_DIR: str = "data/cache"
    UPLOAD_DIR: str = "data/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()

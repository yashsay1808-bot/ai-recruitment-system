"""
Database engine and session management.
Supports PostgreSQL with psycopg driver and graceful fallback to SQLite for local development and test runners.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import get_settings
from db.base import Base

settings = get_settings()

# Use SQLite fallback if configured or during test execution when Postgres is unreachable
database_url = settings.DATABASE_URL
# Hosted providers (Render, Heroku, ...) hand out plain postgres:// or postgresql:// URLs;
# route them to the psycopg v3 driver this project ships.
if database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]
if os.environ.get("USE_SQLITE", "").lower() in ("true", "1") or settings.ENVIRONMENT == "testing":
    database_url = settings.SQLITE_FALLBACK_URL

# Connect arguments
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )
except Exception:
    # Fallback to local SQLite if Postgres driver/connection setup encounters issues
    database_url = settings.SQLITE_FALLBACK_URL
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session.
    Ensures rollback on uncaught exceptions and session closing upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Helper to initialize tables synchronously (useful for test fixtures & bootstrap)."""
    Base.metadata.create_all(bind=engine)

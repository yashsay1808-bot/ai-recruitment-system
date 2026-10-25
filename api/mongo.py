"""
MongoDB Atlas access for accounts, sessions and candidate pools.

The client is created lazily so the API still boots (and /health answers) when MONGODB_URI is unset;
Mongo-backed routes then respond 503. Routers take the database through `get_mongo_db`, which tests
override with an in-memory fake.
"""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, status
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

from src.config import get_settings

SEED_DIR = Path(__file__).parent / "seed"
POOLS = ("core12", "benchmark50", "benchmark100")


@lru_cache()
def _client(uri: str) -> MongoClient:
    return MongoClient(uri, serverSelectionTimeoutMS=8000, tz_aware=True)


def get_mongo_db() -> Database:
    settings = get_settings()
    if not settings.MONGODB_URI:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database is not configured.")
    return _client(settings.MONGODB_URI)[settings.MONGODB_DB]


def init_mongo(db: Database) -> None:
    """Create indexes and load the bundled candidate pools into any pool that is still empty."""
    db.users.create_index("email", unique=True)
    db.sessions.create_index("tokenHash", unique=True)
    db.sessions.create_index("expiresAt", expireAfterSeconds=0)
    db.password_resets.create_index("email", unique=True)
    db.password_resets.create_index("purgeAt", expireAfterSeconds=0)
    db.candidates.create_index([("pool", ASCENDING), ("id", ASCENDING)], unique=True)

    for pool in POOLS:
        if db.candidates.count_documents({"pool": pool}, limit=1):
            continue
        rows = json.loads((SEED_DIR / f"{pool}.json").read_text(encoding="utf-8"))
        db.candidates.insert_many(
            [{**row, "pool": pool, "_order": i} for i, row in enumerate(rows)]
        )

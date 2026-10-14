"""
Candidate pools served from MongoDB. Contract (matches frontend/src/utils/candidatesService.js):

    GET /candidates?pool=<core12|benchmark50|benchmark100> -> Candidate[]

The pools are the bundled synthetic benchmark candidates (api/seed), so the endpoint is public and
read-only.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.database import Database

from api.mongo import POOLS, get_mongo_db

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("")
def list_candidates(
    pool: str = Query(default="core12"), db: Database = Depends(get_mongo_db)
) -> List[dict]:
    if pool not in POOLS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unknown candidate pool. Choose one of: {', '.join(POOLS)}."
        )
    return list(
        db.candidates.find({"pool": pool}, {"_id": 0, "pool": 0, "_order": 0}).sort("_order", 1)
    )

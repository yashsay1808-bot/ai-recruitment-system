"""
Account routes backed by MongoDB. Contract (matches frontend/src/utils/authService.js):

    POST /auth/signup  {name,email,company,role,password} -> 201 {user}
    POST /auth/signin  {email,password}                   -> {token,user}
    GET  /auth/me      (Bearer token)                     -> {user}
    POST /auth/signout (Bearer token)                     -> 204

Passwords are PBKDF2-SHA256 hashed with a per-user salt. Session tokens are random, only their SHA-256
is stored, and they expire after SESSION_DAYS. Five wrong passwords lock the account for 15 minutes.
"""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from api.mongo import get_mongo_db

router = APIRouter(prefix="/auth", tags=["Auth"])

ROLES = [
    "Lead Technical Recruiter",
    "Talent Acquisition Partner",
    "Engineering Hiring Manager",
    "HR Business Partner",
    "Technical Interviewer",
]
MIN_PASSWORD_LENGTH = 8
PBKDF2_ITERATIONS = 210_000
SESSION_DAYS = 7
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BAD_CREDENTIALS = "Incorrect email or password."


class SignUpBody(BaseModel):
    name: str = Field(max_length=120)
    email: str = Field(max_length=254)
    company: str = Field(max_length=120)
    role: str
    password: str = Field(max_length=256)


class SignInBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _norm_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_user(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "company": doc["company"],
        "role": doc["role"],
    }


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _bearer(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


def current_session(
    authorization: Optional[str] = Header(default=None), db: Database = Depends(get_mongo_db)
) -> dict:
    token = _bearer(authorization)
    session = db.sessions.find_one({"tokenHash": _token_hash(token)}) if token else None
    if not session or _aware(session["expiresAt"]) <= _now():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in.")
    return session


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignUpBody, db: Database = Depends(get_mongo_db)) -> dict:
    email = _norm_email(body.email)
    if not body.name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter your full name.")
    if not EMAIL_RE.match(email):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter a valid email address.")
    if not email.endswith("@gmail.com"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Only Gmail addresses (name@gmail.com) can sign up."
        )
    if not body.company.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter your company.")
    if body.role not in ROLES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Choose your role.")
    if len(body.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )

    salt = secrets.token_bytes(16)
    doc = {
        "name": body.name.strip(),
        "email": email,
        "company": body.company.strip(),
        "role": body.role,
        "salt": salt.hex(),
        "hash": _hash_password(body.password, salt),
        "iterations": PBKDF2_ITERATIONS,
        "failedLogins": 0,
        "lockedUntil": None,
        "createdAt": _now(),
    }
    try:
        doc["_id"] = db.users.insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    return {"user": _public_user(doc)}


@router.post("/signin")
def signin(body: SignInBody, db: Database = Depends(get_mongo_db)) -> dict:
    email = _norm_email(body.email)
    user = db.users.find_one({"email": email})

    if user is None:
        # Spend the same time as a real check so unknown emails can't be told apart by latency.
        _hash_password(body.password, b"\x00" * 16)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, BAD_CREDENTIALS)

    locked_until = _aware(user.get("lockedUntil"))
    if locked_until and locked_until > _now():
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts. Try again in a few minutes."
        )

    expected = user["hash"]
    actual = _hash_password(body.password, bytes.fromhex(user["salt"]), user["iterations"])
    if not hmac.compare_digest(expected, actual):
        failed = user.get("failedLogins", 0) + 1
        update = {"failedLogins": failed}
        if failed >= MAX_FAILED_LOGINS:
            update = {"failedLogins": 0, "lockedUntil": _now() + timedelta(minutes=LOCK_MINUTES)}
        db.users.update_one({"_id": user["_id"]}, {"$set": update})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, BAD_CREDENTIALS)

    db.users.update_one({"_id": user["_id"]}, {"$set": {"failedLogins": 0, "lockedUntil": None}})
    token = secrets.token_urlsafe(32)
    db.sessions.insert_one(
        {
            "tokenHash": _token_hash(token),
            "userId": user["_id"],
            "createdAt": _now(),
            "expiresAt": _now() + timedelta(days=SESSION_DAYS),
        }
    )
    return {"token": token, "user": _public_user(user)}


@router.get("/me")
def me(session: dict = Depends(current_session), db: Database = Depends(get_mongo_db)) -> dict:
    user = db.users.find_one({"_id": session["userId"]})
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in.")
    return {"user": _public_user(user)}


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
def signout(session: dict = Depends(current_session), db: Database = Depends(get_mongo_db)) -> Response:
    db.sessions.delete_one({"_id": session["_id"]})
    return Response(status_code=status.HTTP_204_NO_CONTENT)

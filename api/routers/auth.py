"""
Account routes backed by MongoDB. Contract (matches frontend/src/utils/authService.js):

    POST /auth/signup  {name,email,company,role,password} -> 201 {user}
    POST /auth/signin  {email,password}                   -> {token,user}
    POST /auth/google  {credential}  (Google ID token)    -> {token,user}
    GET  /auth/me      (Bearer token)                     -> {user}
    POST /auth/signout (Bearer token)                     -> 204

Passwords are PBKDF2-SHA256 hashed with a per-user salt. Session tokens are random, only their SHA-256
is stored, and they expire after SESSION_DAYS. Five wrong passwords lock the account for 15 minutes.
"""

import hashlib
import hmac
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from api import mailer
from api.mongo import get_mongo_db
from src.config import get_settings

router = APIRouter(prefix="/auth", tags=["Auth"])

ROLES = [
    "Lead Technical Recruiter",
    "Talent Acquisition Partner",
    "Engineering Hiring Manager",
    "HR Business Partner",
    "Technical Interviewer",
]
MIN_PASSWORD_LENGTH = 8
PASSWORD_RULE = (
    f"Password must have at least {MIN_PASSWORD_LENGTH} characters with an uppercase letter, "
    "a lowercase letter, a number and a special character."
)


def _strong_password(p: str) -> bool:
    return (
        len(p) >= MIN_PASSWORD_LENGTH
        and any(c.islower() for c in p)
        and any(c.isupper() for c in p)
        and any(c.isdigit() for c in p)
        and any(not c.isalnum() for c in p)
    )
PBKDF2_ITERATIONS = 210_000
SESSION_DAYS = 7
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RESET_MINUTES = 10  # how long an e-mailed code stays valid
RESET_MAX_ATTEMPTS = 5  # wrong guesses allowed per code
RESET_MAX_PER_HOUR = 3  # codes that can be requested per e-mail per hour
BAD_CREDENTIALS = "Incorrect email or password."


class SignUpBody(BaseModel):
    name: str = Field(max_length=120)
    email: str = Field(max_length=254)
    company: str = Field(max_length=120)
    role: str
    password: str = Field(max_length=256)
    phone: str = Field(default="", max_length=24)  # optional; a reset code is also sent here when SMS is set up


class SignInBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class ForgotBody(BaseModel):
    email: str = Field(max_length=254)


class ResetCodeBody(BaseModel):
    email: str = Field(max_length=254)
    code: str = Field(max_length=12)
    password: str = Field(max_length=256)


class GoogleBody(BaseModel):
    credential: str = Field(max_length=4096)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _norm_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()


def _norm_phone(phone: str) -> Optional[str]:
    """'' for no number, '+91...' for a valid one, None when it is not a plausible mobile number."""
    p = re.sub(r"[\s().-]", "", phone or "")
    if not p:
        return ""
    if re.fullmatch(r"\d{10}", p):
        return "+91" + p  # a bare 10-digit number is read as an Indian mobile number
    return p if re.fullmatch(r"\+\d{10,14}", p) else None


def _code_hash(email: str, code: str) -> str:
    return hmac.new(get_settings().SECRET_KEY.encode(), f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_user(doc: dict) -> dict:
    user = {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "company": doc["company"],
        "role": doc["role"],
    }
    if doc.get("picture"):
        user["picture"] = doc["picture"]
    return user


def _issue_session(db: Database, user: dict) -> dict:
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


def verify_google_credential(credential: str) -> dict:
    """Validate a Google ID token with Google and return its claims.

    Raises HTTPException when the token is invalid, for another client, expired, or the email is
    unverified or not a Gmail address. Tests replace this function with a stub.
    """
    client_id = get_settings().GOOGLE_CLIENT_ID
    if not client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google sign-in is not configured.")

    bad = HTTPException(status.HTTP_401_UNAUTHORIZED, "Google sign-in could not be verified.")
    url = f"{GOOGLE_TOKENINFO_URL}?{urllib.parse.urlencode({'id_token': credential})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            claims = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError:
        raise bad  # Google rejects malformed, expired or tampered tokens with a 400
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not reach Google to verify sign-in.")

    if claims.get("aud") != client_id or claims.get("iss") not in GOOGLE_ISSUERS:
        raise bad
    try:
        if int(claims.get("exp", 0)) <= _now().timestamp():
            raise bad
    except (TypeError, ValueError):
        raise bad
    if str(claims.get("email_verified")).lower() != "true" or not claims.get("email"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your Google account email is not verified.")
    if not _norm_email(claims["email"]).endswith("@gmail.com"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only @gmail.com Google accounts are accepted.")
    return claims


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
    if not _strong_password(body.password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_RULE)
    phone = _norm_phone(body.phone)
    if phone is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Enter a valid mobile number, or leave it empty.")

    salt = secrets.token_bytes(16)
    doc = {
        "phone": phone,
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

    if user is None or not user.get("hash"):
        # Unknown email, or a Google-only account with no password. Spend the same time as a real check so unknown emails can't be told apart by latency.
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
    return _issue_session(db, user)


@router.post("/google")
def google_signin(body: GoogleBody, db: Database = Depends(get_mongo_db)) -> dict:
    claims = verify_google_credential(body.credential)
    email = _norm_email(claims["email"])
    picture = claims.get("picture")

    user = db.users.find_one({"email": email})
    if user is None:
        user = {
            "name": claims.get("name") or email,
            "email": email,
            "company": claims.get("hd") or "Google account",
            "role": ROLES[0],
            "hash": None,  # Google-only account: no password to sign in with
            "salt": None,
            "iterations": 0,
            "failedLogins": 0,
            "lockedUntil": None,
            "googleId": claims.get("sub"),
            "picture": picture,
            "createdAt": _now(),
        }
        try:
            user["_id"] = db.users.insert_one(user).inserted_id
        except DuplicateKeyError:  # two first sign-ins racing: use the winner's record
            user = db.users.find_one({"email": email})
    else:
        # Same Gmail already registered (email + password): link Google to that account.
        update = {"googleId": claims.get("sub")}
        if picture:
            update["picture"] = picture
        db.users.update_one({"_id": user["_id"]}, {"$set": update})
        user = {**user, **update}
    return _issue_session(db, user)


class ResetBody(BaseModel):
    credential: str = Field(max_length=4096)
    password: str = Field(max_length=256)


@router.post("/reset-password")
def reset_password(body: ResetBody, db: Database = Depends(get_mongo_db)) -> dict:
    """Forgot password: Google proves that the caller owns the Gmail address, then a new password is stored.

    Every account is a Gmail address, so no reset e-mail (and no mail server) is needed.
    """
    claims = verify_google_credential(body.credential)
    if not _strong_password(body.password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_RULE)
    user = db.users.find_one({"email": _norm_email(claims["email"])})
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No account was found for this Gmail address. Create an account first.")
    salt = secrets.token_bytes(16)
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"salt": salt.hex(), "hash": _hash_password(body.password, salt), "iterations": PBKDF2_ITERATIONS,
                  "failedLogins": 0, "lockedUntil": None}},
    )
    db.sessions.delete_many({"userId": user["_id"]})  # a changed password ends the old sessions
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(body: ForgotBody, db: Database = Depends(get_mongo_db)) -> dict:
    """Send a 6-digit code by e-mail (and by SMS when the account has a number and SMS is set up).

    The answer is the same whether or not the e-mail has an account, so nobody can use this to find out who is registered.
    """
    if not mailer.email_configured():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Password reset by e-mail is not set up on this server yet.")
    generic = {"ok": True, "message": f"If an account exists for this e-mail, a 6-digit code has been sent. It is valid for {RESET_MINUTES} minutes."}
    email = _norm_email(body.email)
    user = db.users.find_one({"email": email})
    if user is None:
        return generic

    now = _now()
    previous = db.password_resets.find_one({"email": email}) or {}
    recent = [t for t in (_aware(x) for x in previous.get("requests", [])) if t and now - t < timedelta(hours=1)]
    if len(recent) >= RESET_MAX_PER_HOUR:
        return generic

    code = f"{secrets.randbelow(10**6):06d}"
    db.password_resets.replace_one(
        {"email": email},
        {
            "email": email,
            "codeHash": _code_hash(email, code),
            "expiresAt": now + timedelta(minutes=RESET_MINUTES),
            "purgeAt": now + timedelta(hours=1),  # the document outlives the code so the hourly limit is remembered
            "attempts": 0,
            "requests": recent + [now],
        },
        upsert=True,
    )
    text = f"Your Nexus ATS password reset code is {code}. It is valid for {RESET_MINUTES} minutes. If you did not ask for it, ignore this message."
    mailer.send_email(email, "Your Nexus ATS password reset code", text)
    if user.get("phone"):
        mailer.send_sms(user["phone"], text)
    return generic


@router.post("/reset-with-code")
def reset_with_code(body: ResetCodeBody, db: Database = Depends(get_mongo_db)) -> dict:
    """Set a new password with the code that was sent by e-mail or SMS."""
    email = _norm_email(body.email)
    bad = HTTPException(status.HTTP_400_BAD_REQUEST, "That code is incorrect or has expired. Ask for a new one.")
    doc = db.password_resets.find_one({"email": email})
    if not doc or _aware(doc["expiresAt"]) <= _now() or doc.get("attempts", 0) >= RESET_MAX_ATTEMPTS:
        raise bad
    if not _strong_password(body.password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_RULE)
    if not hmac.compare_digest(doc["codeHash"], _code_hash(email, body.code.strip())):
        db.password_resets.update_one({"_id": doc["_id"]}, {"$inc": {"attempts": 1}})
        raise bad
    user = db.users.find_one({"email": email})
    if user is None:
        raise bad

    salt = secrets.token_bytes(16)
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"salt": salt.hex(), "hash": _hash_password(body.password, salt), "iterations": PBKDF2_ITERATIONS,
                  "failedLogins": 0, "lockedUntil": None}},
    )
    db.password_resets.delete_one({"_id": doc["_id"]})
    db.sessions.delete_many({"userId": user["_id"]})
    return {"ok": True}


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

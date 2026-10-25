"""Auth and candidate routes against an in-memory MongoDB (mongomock)."""

import pytest

mongomock = pytest.importorskip("mongomock")

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402
from api.mongo import get_mongo_db, init_mongo  # noqa: E402

SIGNUP = {
    "name": "Test Recruiter",
    "email": "Tester@Gmail.com",
    "company": "Acme",
    "role": "Lead Technical Recruiter",
    "password": "Correct-Horse9!",
}


@pytest.fixture()
def client():
    db = mongomock.MongoClient().recruitment
    init_mongo(db)
    app.dependency_overrides[get_mongo_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def signin(client, password="Correct-Horse9!"):
    return client.post("/auth/signin", json={"email": "tester@gmail.com", "password": password})


def test_signup_then_signin_me_signout(client):
    res = client.post("/auth/signup", json=SIGNUP)
    assert res.status_code == 201
    assert res.json()["user"]["email"] == "tester@gmail.com"
    assert "hash" not in res.json()["user"]

    res = signin(client)
    assert res.status_code == 200
    token = res.json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    assert client.get("/auth/me", headers=auth).json()["user"]["name"] == "Test Recruiter"
    assert client.post("/auth/signout", headers=auth).status_code == 204
    assert client.get("/auth/me", headers=auth).status_code == 401


def test_signup_rules(client):
    assert client.post("/auth/signup", json={**SIGNUP, "email": "x@yahoo.com"}).status_code == 422
    assert client.post("/auth/signup", json={**SIGNUP, "password": "short"}).status_code == 422
    assert client.post("/auth/signup", json={**SIGNUP, "role": "CEO"}).status_code == 422
    assert client.post("/auth/signup", json=SIGNUP).status_code == 201
    dup = client.post("/auth/signup", json={**SIGNUP, "email": "TESTER@gmail.com"})
    assert dup.status_code == 409


def test_wrong_password_is_generic_and_locks_after_five(client):
    client.post("/auth/signup", json=SIGNUP)
    unknown = client.post("/auth/signin", json={"email": "nobody@gmail.com", "password": "whatever1"})
    wrong = signin(client, "wrong-password")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"]

    for _ in range(4):
        assert signin(client, "wrong-password").status_code == 401
    assert signin(client).status_code == 429  # locked, even with the right password


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_candidate_pools(client):
    counts = {"core12": 12, "benchmark50": 50, "benchmark100": 100}
    for pool, n in counts.items():
        rows = client.get(f"/candidates?pool={pool}").json()
        assert len(rows) == n
        assert "_id" not in rows[0] and "pool" not in rows[0] and "id" in rows[0]
    assert client.get("/candidates").json()[0]["id"] == "CAN-001"
    assert client.get("/candidates?pool=nope").status_code == 400


def test_init_mongo_is_idempotent(client):
    db = app.dependency_overrides[get_mongo_db]()
    init_mongo(db)
    assert db.candidates.count_documents({}) == 162


def test_503_when_mongo_not_configured():
    app.dependency_overrides.clear()
    assert TestClient(app).get("/candidates").status_code == 503


# ---------------------------------------------------------------------------------------------
# Google sign-in
# ---------------------------------------------------------------------------------------------
import io  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
import urllib.error  # noqa: E402

from fastapi import HTTPException  # noqa: E402

from api.routers import auth as auth_module  # noqa: E402
from src.config import get_settings  # noqa: E402

CLIENT_ID = "client-123.apps.googleusercontent.com"


def claims(**over):
    base = {
        "aud": CLIENT_ID,
        "iss": "https://accounts.google.com",
        "exp": str(int(time.time()) + 3600),
        "email": "Googler@Gmail.com",
        "email_verified": "true",
        "name": "Go Ogler",
        "sub": "1234567890",
        "picture": "https://example.com/p.png",
    }
    return {**base, **over}


@pytest.fixture()
def google_ok(monkeypatch):
    monkeypatch.setattr(auth_module, "verify_google_credential", lambda cred: claims())


def test_google_creates_user_and_session(client, google_ok):
    res = client.post("/auth/google", json={"credential": "tok"})
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["email"] == "googler@gmail.com"
    assert body["user"]["name"] == "Go Ogler"
    assert body["user"]["picture"] == "https://example.com/p.png"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200

    db = app.dependency_overrides[get_mongo_db]()
    stored = db.users.find_one({"email": "googler@gmail.com"})
    assert stored["hash"] is None and stored["googleId"] == "1234567890"
    assert db.sessions.count_documents({}) == 1


def test_google_is_idempotent_and_links_existing_password_account(client, google_ok):
    client.post("/auth/signup", json={**SIGNUP, "email": "googler@gmail.com"})
    first = client.post("/auth/google", json={"credential": "tok"}).json()
    second = client.post("/auth/google", json={"credential": "tok"}).json()
    assert first["user"]["id"] == second["user"]["id"]
    assert first["user"]["company"] == "Acme"  # kept the email/password profile

    db = app.dependency_overrides[get_mongo_db]()
    assert db.users.count_documents({"email": "googler@gmail.com"}) == 1
    # The password still works for the linked account
    ok = client.post("/auth/signin", json={"email": "googler@gmail.com", "password": "Correct-Horse9!"})
    assert ok.status_code == 200


def test_google_only_account_cannot_password_sign_in(client, google_ok):
    client.post("/auth/google", json={"credential": "tok"})
    res = client.post("/auth/signin", json={"email": "googler@gmail.com", "password": "anything-at-all"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect email or password."


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture()
def tokeninfo(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", CLIENT_ID)
    get_settings.cache_clear()

    def install(payload=None, error=None):
        def fake_urlopen(url, timeout=0):
            if error:
                raise error
            return FakeResponse(json.dumps(payload).encode())

        monkeypatch.setattr(auth_module.urllib.request, "urlopen", fake_urlopen)

    yield install
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "payload,status_code",
    [
        (claims(), 200),
        (claims(aud="someone-else"), 401),
        (claims(iss="https://evil.example"), 401),
        (claims(exp=str(int(time.time()) - 5)), 401),
        (claims(email_verified="false"), 401),
        (claims(email="x@yahoo.com"), 403),
    ],
)
def test_verify_google_credential_rules(tokeninfo, payload, status_code):
    tokeninfo(payload)
    if status_code == 200:
        assert auth_module.verify_google_credential("tok")["sub"] == "1234567890"
    else:
        with pytest.raises(HTTPException) as err:
            auth_module.verify_google_credential("tok")
        assert err.value.status_code == status_code


def test_verify_google_credential_rejects_bad_token_and_handles_outage(tokeninfo):
    tokeninfo(error=urllib.error.HTTPError("u", 400, "bad", {}, io.BytesIO(b"{}")))
    with pytest.raises(HTTPException) as err:
        auth_module.verify_google_credential("garbage")
    assert err.value.status_code == 401

    tokeninfo(error=urllib.error.URLError("down"))
    with pytest.raises(HTTPException) as err:
        auth_module.verify_google_credential("tok")
    assert err.value.status_code == 502


def test_google_not_configured_returns_503(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    get_settings.cache_clear()
    assert client.post("/auth/google", json={"credential": "tok"}).status_code == 503
    get_settings.cache_clear()


def test_signup_requires_upper_lower_digit_and_special_character(client):
    weak = ["Sh0rt!", "alllowercase1!", "ALLUPPERCASE1!", "NoDigitsHere!", "NoSpecial123Abc"]
    for pw in weak:
        assert client.post("/auth/signup", json={**SIGNUP, "password": pw}).status_code == 422, pw
    assert client.post("/auth/signup", json={**SIGNUP, "password": "Str0ng-Pass!"}).status_code == 201


def test_forgot_password_resets_through_google_and_ends_old_sessions(client, google_ok):
    client.post("/auth/signup", json={**SIGNUP, "email": "googler@gmail.com"})
    old = client.post("/auth/signin", json={"email": "googler@gmail.com", "password": SIGNUP["password"]}).json()["token"]
    # a weak new password is refused, the old one still works
    assert client.post("/auth/reset-password", json={"credential": "tok", "password": "weakpass"}).status_code == 422
    assert client.post("/auth/signin", json={"email": "googler@gmail.com", "password": SIGNUP["password"]}).status_code == 200
    # a strong one replaces it
    assert client.post("/auth/reset-password", json={"credential": "tok", "password": "N3w-Passw0rd!"}).status_code == 200
    assert client.post("/auth/signin", json={"email": "googler@gmail.com", "password": SIGNUP["password"]}).status_code == 401
    assert client.post("/auth/signin", json={"email": "googler@gmail.com", "password": "N3w-Passw0rd!"}).status_code == 200
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old}"}).status_code == 401


def test_forgot_password_needs_an_existing_account(client, google_ok):
    res = client.post("/auth/reset-password", json={"credential": "tok", "password": "N3w-Passw0rd!"})
    assert res.status_code == 404


# ---- forgot password by e-mail code
# --------------------------------------------------------------------------
EMAIL = SIGNUP["email"].lower()


@pytest.fixture()
def outbox(monkeypatch):
    """Turns e-mail on and records what would have been sent."""
    monkeypatch.setenv("BREVO_API_KEY", "test-key")
    monkeypatch.setenv("MAIL_FROM", "noreply@example.com")
    sent = []
    monkeypatch.setattr(auth_module.mailer, "send_email", lambda to, subject, text: sent.append((to, text)) or True)
    monkeypatch.setattr(auth_module.mailer, "send_sms", lambda to, text: sent.append((to, text)) or True)
    return sent


def _code(outbox):
    import re as _re
    return _re.search(r"code is (\d{6})", outbox[-1][1]).group(1)


def test_forgot_password_emails_a_code_that_resets_the_password(client, outbox):
    client.post("/auth/signup", json=SIGNUP)
    old = signin(client).json()["token"]
    res = client.post("/auth/forgot-password", json={"email": EMAIL})
    assert res.status_code == 200 and "6-digit code" in res.json()["message"]
    assert outbox[-1][0] == EMAIL
    code = _code(outbox)
    # a weak password is refused and does not use up the code
    assert client.post("/auth/reset-with-code", json={"email": EMAIL, "code": code, "password": "weak"}).status_code == 422
    assert client.post("/auth/reset-with-code", json={"email": EMAIL, "code": code, "password": "N3w-Passw0rd!"}).status_code == 200
    assert signin(client).status_code == 401
    assert signin(client, "N3w-Passw0rd!").status_code == 200
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old}"}).status_code == 401
    # the code works once
    assert client.post("/auth/reset-with-code", json={"email": EMAIL, "code": code, "password": "An0ther-Pass!"}).status_code == 400


def test_forgot_password_does_not_reveal_which_emails_have_accounts(client, outbox):
    known = client.post("/auth/signup", json=SIGNUP) and client.post("/auth/forgot-password", json={"email": EMAIL})
    unknown = client.post("/auth/forgot-password", json={"email": "nobody@gmail.com"})
    assert known.status_code == unknown.status_code == 200 and known.json() == unknown.json()
    assert [to for to, _ in outbox] == [EMAIL]


def test_wrong_codes_are_limited_to_five_tries(client, outbox):
    client.post("/auth/signup", json=SIGNUP)
    client.post("/auth/forgot-password", json={"email": EMAIL})
    good = _code(outbox)
    wrong = "000000" if good != "000000" else "111111"
    for _ in range(5):
        assert client.post("/auth/reset-with-code", json={"email": EMAIL, "code": wrong, "password": "N3w-Passw0rd!"}).status_code == 400
    # the right code no longer works after five wrong guesses
    assert client.post("/auth/reset-with-code", json={"email": EMAIL, "code": good, "password": "N3w-Passw0rd!"}).status_code == 400


def test_an_expired_code_is_refused(client, outbox):
    client.post("/auth/signup", json=SIGNUP)
    client.post("/auth/forgot-password", json={"email": EMAIL})
    code = _code(outbox)
    db = app.dependency_overrides[get_mongo_db]()
    db.password_resets.update_one({"email": EMAIL}, {"$set": {"expiresAt": auth_module._now() - auth_module.timedelta(minutes=1)}})
    assert client.post("/auth/reset-with-code", json={"email": EMAIL, "code": code, "password": "N3w-Passw0rd!"}).status_code == 400


def test_at_most_three_codes_per_hour_and_an_sms_when_the_account_has_a_number(client, outbox):
    client.post("/auth/signup", json={**SIGNUP, "phone": "98765 43210"})
    db = app.dependency_overrides[get_mongo_db]()
    assert db.users.find_one({"email": EMAIL})["phone"] == "+919876543210"
    for _ in range(5):
        client.post("/auth/forgot-password", json={"email": EMAIL})
    assert len([m for m in outbox if m[0] == EMAIL]) == 3
    assert len([m for m in outbox if m[0] == "+919876543210"]) == 3


def test_forgot_password_says_so_when_e_mail_is_not_set_up(client, monkeypatch):
    monkeypatch.delenv("BREVO_API_KEY", raising=False)
    assert client.post("/auth/forgot-password", json={"email": EMAIL}).status_code == 503


def test_signup_rejects_an_invalid_phone_number(client):
    assert client.post("/auth/signup", json={**SIGNUP, "phone": "12345"}).status_code == 422

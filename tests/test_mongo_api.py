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
    "password": "correct-horse",
}


@pytest.fixture()
def client():
    db = mongomock.MongoClient().recruitment
    init_mongo(db)
    app.dependency_overrides[get_mongo_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def signin(client, password="correct-horse"):
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

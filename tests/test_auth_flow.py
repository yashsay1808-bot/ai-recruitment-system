"""Auth: password storage, sign-up -> sign-in loop, and the page gate (runs against a throwaway DB)."""
import os

import pytest

from src.core.database import RecruitmentDatabase

st_testing = pytest.importorskip("streamlit.testing.v1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "auth_test.db")
    monkeypatch.setenv("RECRUITMENT_DB_PATH", path)
    return path


def test_new_accounts_use_pbkdf2_and_verify(db_path):
    db = RecruitmentDatabase(db_path)
    assert db.register_recruiter("Ada", "ada@acme.io", "correct horse", "Acme", "Lead Technical Recruiter")
    with db._get_connection() as conn:
        stored = conn.execute("SELECT password_hash FROM recruiters").fetchone()[0]
    assert stored.startswith("pbkdf2$")
    assert db.authenticate_recruiter("ada@acme.io", "correct horse")["name"] == "Ada"
    assert db.authenticate_recruiter("ada@acme.io", "wrong") is None


def test_legacy_sha256_accounts_still_sign_in(db_path):
    db = RecruitmentDatabase(db_path)
    with db._get_connection() as conn:
        conn.execute(
            "INSERT INTO recruiters (name, email, password_hash, company, role, clearance_level) VALUES (?,?,?,?,?,?)",
            ("Old", "old@acme.io", db._hash_password("legacy-pass"), "Acme", "Talent Acquisition Partner", 2),
        )
    assert db.authenticate_recruiter("old@acme.io", "legacy-pass")["name"] == "Old"


def test_no_seeded_demo_account_and_no_self_service_admin(db_path):
    db = RecruitmentDatabase(db_path)
    assert db.authenticate_recruiter("recruiter@techcorp.com", "password123") is None
    db.register_recruiter("Eve", "eve@acme.io", "pw-12345678", "Acme", "Executive HR / Super Admin")
    assert db.get_recruiter_by_email("eve@acme.io")["clearance_level"] == 2


def _boot():
    return st_testing.AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=180)


def test_signed_out_user_only_sees_sign_in(db_path):
    cwd = os.getcwd(); os.chdir(ROOT)
    try:
        at = _boot().run()
        assert not at.exception
        assert not at.tabs
        assert [t.label for t in at.text_input] == ["Email", "Password"]
        assert at.session_state["authenticated_recruiter"] is None
    finally:
        os.chdir(cwd)


def test_sign_up_returns_to_sign_in_then_signs_in(db_path):
    cwd = os.getcwd(); os.chdir(ROOT)
    try:
        at = _boot().run()
        next(b for b in at.button if b.label == "Sign up").click().run()
        assert [t.label for t in at.text_input] == ["Full name", "Work email", "Company", "Password"]
        for field, value in zip(at.text_input, ["Ada Lovelace", "ada@acme.io", "Acme", "hunter2hunter2"]):
            field.set_value(value)
        next(b for b in at.button if b.label == "Create account").click().run()
        assert not at.exception
        assert at.session_state["authenticated_recruiter"] is None          # not auto-signed-in
        assert [t.label for t in at.text_input] == ["Email", "Password"]    # back on Sign in
        assert any("Account created successfully" in m.value for m in at.markdown)

        at.text_input[0].set_value("ada@acme.io"); at.text_input[1].set_value("hunter2hunter2")
        next(b for b in at.button if b.label == "Sign in").click().run()
        assert not at.exception
        assert at.session_state["authenticated_recruiter"]["name"] == "Ada Lovelace"
        assert "Command Center" in [t.label for t in at.tabs]
        assert [b.label for b in at.sidebar.button][0] == "Sign out"
    finally:
        os.chdir(cwd)

"""
Unit tests for SQLite Recruitment Database, Enterprise Authorization, and Recruiter Authentication.
"""

import os
import pytest
from src.core.database import RecruitmentDatabase


def test_recruitment_database(tmp_path):
    db_file = str(tmp_path / "test_recruitment.db")
    db = RecruitmentDatabase(db_path=db_file)

    # 1. Test Recruiter Registration with Valid Enterprise Key
    recruiter_id = db.register_recruiter(
        name="John Doe",
        email="john.doe@enterprise.com",
        password="securePassword456",
        company="Enterprise Global",
        role="Lead Technical Recruiter",
        auth_key="TECHCORP-AUTH-2026"
    )
    assert recruiter_id is not None

    # Test rejection with invalid enterprise key
    invalid_key_id = db.register_recruiter(
        name="Hacker Recruiter",
        email="hacker@fake.com",
        password="password123",
        company="Fake Corp",
        role="Recruiter",
        auth_key="INVALID-KEY-999"
    )
    assert invalid_key_id is None

    # Test duplicate email rejection
    dup_id = db.register_recruiter(
        name="John Impostor",
        email="john.doe@enterprise.com",
        password="anotherPassword",
        company="Other Corp",
        role="HR",
        auth_key="TECHCORP-AUTH-2026"
    )
    assert dup_id is None

    # Test authentication success & clearance token
    auth_user = db.authenticate_recruiter("john.doe@enterprise.com", "securePassword456")
    assert auth_user is not None
    assert auth_user["name"] == "John Doe"
    assert auth_user["company"] == "Enterprise Global"
    assert auth_user["clearance_level"] == 2
    assert "AUTH-SEC-" in auth_user["session_token"]

    # Test authentication failure (wrong password)
    failed_user = db.authenticate_recruiter("john.doe@enterprise.com", "wrongPassword")
    assert failed_user is None

    # Test audit logs generated
    audit_logs = db.get_auth_audit_logs(limit=10)
    assert len(audit_logs) >= 3

    # 2. Create Job
    job_id = db.create_job(
        title="ML Engineer",
        department="AI",
        min_experience=2.0,
        required_skills=["Python", "ML"],
        preferred_skills=["Docker"],
        description_text="Sample ML Job"
    )
    assert job_id == 1

    jobs = db.get_all_jobs()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "ML Engineer"

    # 3. Save Screening Session
    cands = [{
        "candidate_name": "Test Candidate",
        "overall_score": 88.5,
        "rank": 1,
        "breakdown": {"technical_skills": 90.0},
        "gap_results": {"matched_skills": ["Python"]},
        "candidate_data": {"email": "test@test.com", "phone": "1234567890"}
    }]

    session_id = db.save_screening_session(
        job_id=job_id,
        session_name="Test Batch 1",
        evaluated_candidates=cands,
        recruiter_email="john.doe@enterprise.com"
    )
    assert session_id == 1

    sessions = db.get_all_sessions()
    assert len(sessions) == 1
    assert sessions[0]["session_name"] == "Test Batch 1"

    saved_cands = db.get_session_candidates(session_id)
    assert len(saved_cands) == 1
    assert saved_cands[0]["candidate_name"] == "Test Candidate"
    assert saved_cands[0]["overall_score"] == 88.5

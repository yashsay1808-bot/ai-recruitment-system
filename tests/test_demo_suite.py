"""Asserts the four viva test resumes behave as documented in GUIDEBOOK.md (real pipeline, no mocks)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.verify_test_suite import run  # noqa: E402


@pytest.fixture(scope="module")
def rows():
    return {r["file"]: r for r in run(verbose=False)}


def test_gold_standard_ranks_first_and_is_strong_hire(rows):
    r = rows["Test_Case_1_Gold_Standard_Pass.txt"]
    assert r["rank"] == 1 and r["match"] >= 85
    assert r["verdict"] == "STRONG_HIRE" and r["flags"] == []


def test_buzzword_resume_rejected_and_flagged(rows):
    r = rows["Test_Case_2_Buzzword_Exaggeration_Fail.txt"]
    assert r["match"] < 45 and r["verdict"] == "REJECT"
    assert "UNVERIFIED_SKILL_CLAIMS" in r["flags"] and any("EXPERIENCE" in f for f in r["flags"])


def test_lateral_partial_match_is_lean_hire(rows):
    r = rows["Test_Case_3_Lateral_Partial_Match.txt"]
    assert r["verdict"] == "LEAN_HIRE"
    assert "FastAPI" in r["partial"] and any("pytorch" in m.lower() for m in r["missing"])


def test_corrupt_resume_has_low_ats_and_date_flag(rows):
    r = rows["Test_Case_4_Corrupt_ATS_Format_Error.txt"]
    assert r["ats"] < 35 and "DATE_INCONSISTENCY" in r["flags"]

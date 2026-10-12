"""Boots the Streamlit app headlessly (AppTest) and asserts the Obsidian tabs render without exceptions."""
import os

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")


def test_app_boots_with_new_tabs():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cwd = os.getcwd()
    os.chdir(root)
    try:
        at = st_testing.AppTest.from_file(os.path.join(root, "app.py"), default_timeout=120)
        at.session_state["authenticated_recruiter"] = {"id": 1, "name": "T", "role": "R", "company": "C",
                                                       "clearance_level": 2, "session_token": "AUTH-SEC-TEST-2026"}
        at.run()
        assert not at.exception
        labels = [t.label for t in at.tabs]
        for expected in ("Command Center", "Council & GitHub", "Copilot"):
            assert expected in labels
        assert at.session_state["ranked_candidates"]
    finally:
        os.chdir(cwd)

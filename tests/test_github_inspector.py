"""Tests for the GitHub authenticity inspector using an injected fake transport (no network)."""

import json
import time
from datetime import datetime, timezone

from src.core.github_inspector import (GitHubClient, GitHubInspector, extract_github_username,
                                       extract_github_usernames)

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)


def _repo(name, lang, stars, pushed, fork=False):
    return {"name": name, "language": lang, "stargazers_count": stars, "forks_count": 1, "pushed_at": pushed,
            "size": 500, "fork": fork, "description": "d", "license": {"spdx_id": "MIT"}, "topics": ["x"],
            "html_url": "u", "archived": False}


REPOS = [_repo("a", "Python", 30, "2026-09-20T00:00:00Z"), _repo("b", "Python", 2, "2026-08-01T00:00:00Z"),
         _repo("c", "JavaScript", 0, "2026-05-01T00:00:00Z"), _repo("f", "Go", 900, "2026-09-01T00:00:00Z", fork=True)]


def transport(method, url, headers, body, timeout):
    ok = {"x-ratelimit-remaining": "50", "x-ratelimit-reset": str(int(time.time()) + 3000)}
    if url.endswith("/users/ghost"):
        return 404, ok, "{}"
    if "/users/limited" in url:
        return 403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) + 3000)}, "{}"
    if url.endswith("/users/alice"):
        return 200, ok, json.dumps({"login": "alice", "created_at": "2020-01-01T00:00:00Z", "public_repos": 4})
    if "/users/alice/repos" in url:
        return 200, ok, json.dumps(REPOS)
    if "/events/public" in url:
        return 200, ok, json.dumps([{"type": "PushEvent", "created_at": "2026-09-25T00:00:00Z",
                                     "repo": {"name": "alice/a"}, "payload": {"size": 3}}])
    if "/languages" in url:
        return 200, ok, json.dumps({"Python": 9000} if "/a/" in url else {"JavaScript": 2000})
    return 404, ok, "{}"


def _inspector():
    return GitHubInspector(GitHubClient(token="", transport=transport, sleep=lambda s: None), now=lambda: NOW)


def test_username_extraction():
    assert extract_github_usernames("GitHub: https://github.com/octocat | github.com/features | bob.github.io") == ["octocat", "bob"]
    assert extract_github_username({"github": "github.com/snehakulkarni"}) == "snehakulkarni"
    assert extract_github_username({"raw_text": "no links here"}) is None


def test_verified_claims_score_high():
    r = _inspector().inspect_username("alice", ["Python", "JavaScript"])
    assert r["status"] == "ok" and r["authenticity_score"] >= 80 and r["verdict"] == "VERIFIED"
    assert r["activity"]["active_within_6_months"] and r["activity"]["estimated_commits_90d"] == 3


def test_exaggeration_is_detected_and_forks_do_not_count():
    r = _inspector().inspect_username("alice", ["Python", "JavaScript", "Go", "Rust"])
    status = {v["language"]: v["status"] for v in r["language_verification"]}
    assert status["Go"] == "unverified" and status["Rust"] == "unverified"  # Go only exists in a fork
    assert r["resume_authenticity"]["exaggeration_risk"] == "HIGH" and r["authenticity_score"] <= 50


def test_graceful_failures():
    ins = _inspector()
    assert ins.inspect_username("ghost", ["Python"])["status"] == "user_not_found"
    limited = ins.inspect_username("limited", ["Python"])
    assert limited["status"] == "rate_limited" and limited["authenticity_score"] is None
    assert limited["retry_after_seconds"] > 0
    assert ins.inspect_candidate({"raw_text": "hello"})["status"] == "no_github_found"

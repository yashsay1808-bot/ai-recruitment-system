"""
GitHub & Portfolio Authenticity Inspector
=========================================

Validates the programming-language claims on a resume against the candidate's real, public
GitHub footprint and produces a ``ResumeAuthenticityScore`` (0-100).

What it does
------------
1. **Finds the GitHub handle** in parsed resume data (``candidate_data["github"]``) or raw text
   (``github.com/<user>``, ``<user>.github.io``, ``GitHub: <user>``).
2. **Queries the public REST API** (``/users/{u}``, ``/users/{u}/repos``, per-repo ``/languages``
   and ``/users/{u}/events/public``) using only the standard library. ``GITHUB_TOKEN`` is used
   automatically when set (60 -> 5,000 requests/hour) and enables true *pinned* repositories via GraphQL.
3. **Handles rate limits gracefully**: short ``Retry-After`` waits are honoured, longer ones return a
   structured ``rate_limited`` report (or a ``partial`` report if the limit is hit mid-way) instead of
   raising. Results are cached in-memory (default 15 min) so re-scoring a batch does not burn quota.
4. **Evaluates** language mix (percent by bytes), stars/forks, repository maturity, commit/push activity
   over the last 90 days, recency (active within 6 months or abandoned) and pinned/featured repositories.
5. **Cross-references claims**: each language on the resume is marked ``verified`` / ``weak`` /
   ``unverified`` against what the repositories actually contain, and an exaggeration risk
   (``LOW`` / ``MODERATE`` / ``HIGH``) is derived.

Important interpretation notes (also returned in every report)
--------------------------------------------------------------
* A missing or thin GitHub is **not** proof of dishonesty. Many strong engineers work in private or
  employer repositories. The report therefore carries a ``confidence`` value and uses the verdict
  ``INSUFFICIENT_PUBLIC_DATA`` (with ``authenticity_score = None``) when there is nothing to judge.
* The REST API cannot return pinned repositories. With a token they are fetched via GraphQL; without
  one, ``pinned_repositories_source`` is ``"heuristic_top_repos"`` (most-starred / most-recent originals).
* Commit counts come from the public events feed, which only covers the last ~90 days and is an
  estimate. Forked repositories are excluded from language evidence because forked code is not authored work.

Typical use
-----------
    from src.core.github_inspector import GitHubInspector

    report = GitHubInspector().inspect_candidate(candidate_data)
    report["authenticity_score"]       # 0-100 or None
    report["language_verification"]    # per-language verified / weak / unverified
    candidate_data["github_report"] = report   # picked up by the Tech Lead agent in agentic_council.py

No third-party dependencies are required.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # Optional: project ontology improves skill classification.
    from src.core.skill_ontology import get_skill_category as _get_skill_category
except Exception:  # pragma: no cover
    _get_skill_category = None

logger = logging.getLogger(__name__)

__all__ = [
    "GitHubError",
    "GitHubRateLimitError",
    "GitHubNotFoundError",
    "GitHubUnavailableError",
    "GitHubClient",
    "GitHubInspector",
    "ResumeAuthenticityScore",
    "extract_github_usernames",
    "extract_github_username",
    "extract_claimed_languages",
    "inspect_candidate_github",
]

API_BASE = "https://api.github.com"
USER_AGENT = "ai-recruitment-platform-github-inspector/1.0"

# --------------------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------------------
class GitHubError(Exception):
    """Base class for GitHub client failures."""


class GitHubNotFoundError(GitHubError):
    """HTTP 404: user or repository does not exist (or is private)."""


class GitHubUnavailableError(GitHubError):
    """Network failure, timeout or 5xx response."""


class GitHubRateLimitError(GitHubError):
    """Primary or secondary rate limit reached and the wait is too long to block on."""

    def __init__(self, message: str, retry_after_seconds: Optional[int] = None, reset_at: Optional[str] = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.reset_at = reset_at


# --------------------------------------------------------------------------------------
# Username extraction
# --------------------------------------------------------------------------------------
_RESERVED_PATHS = {
    "features", "orgs", "sponsors", "topics", "marketplace", "settings", "login", "logout", "about", "pricing",
    "enterprise", "collections", "apps", "explore", "readme", "pulls", "issues", "notifications", "new", "join",
    "security", "site", "contact", "trending", "events", "customer-stories", "team", "search", "codespaces",
    "copilot", "premium-support", "resources", "solutions", "partners", "github", "organizations", "gist", "gists",
}
_NOT_A_HANDLE = {"http", "https", "www", "com", "profile", "link", "url", "id", "username", "handle", "link:", "na", "none"}
_NAME = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})"
_URL_RE = re.compile(rf"(?:https?://)?(?:www\.)?github\.com/(?P<u>{_NAME})(?![A-Za-z0-9_-])", re.IGNORECASE)
_PAGES_RE = re.compile(rf"\b(?P<u>{_NAME})\.github\.io\b", re.IGNORECASE)
_LABEL_RE = re.compile(
    rf"\bgit\s?hub\b(?:\s*(?:id|profile|username|handle|link))?\s*[:\-–|]\s*@?(?P<u>{_NAME})(?![A-Za-z0-9_.@/-])",
    re.IGNORECASE,
)


def extract_github_usernames(text: str) -> List[str]:
    """Return candidate GitHub handles found in ``text`` in order of appearance (de-duplicated)."""
    if not text:
        return []
    found: List[Tuple[int, str]] = []
    for rx in (_URL_RE, _PAGES_RE):
        for m in rx.finditer(text):
            found.append((m.start(), m.group("u")))
    scrubbed = _URL_RE.sub(" ", text)
    for m in _LABEL_RE.finditer(scrubbed):
        found.append((len(text) + m.start(), m.group("u")))
    seen, out = set(), []
    for _, user in sorted(found):
        low = user.lower()
        if low in _RESERVED_PATHS or low in _NOT_A_HANDLE or low in seen or low.endswith("-"):
            continue
        seen.add(low)
        out.append(user)
    return out


def extract_github_username(candidate_data: Dict[str, Any]) -> Optional[str]:
    """Best-effort handle lookup in parsed resume data, then in raw text. Returns ``None`` if absent."""
    if not isinstance(candidate_data, dict):
        return None
    probes: List[str] = []
    for key in ("github", "github_url", "github_username", "portfolio", "website"):
        val = candidate_data.get(key)
        if isinstance(val, str) and val.strip():
            probes.append(val.strip())
    links = candidate_data.get("links") or candidate_data.get("social_links")
    if isinstance(links, dict):
        probes.extend(str(v) for v in links.values() if isinstance(v, str))
    for probe in probes:
        users = extract_github_usernames(probe)
        if users:
            return users[0]
        if re.fullmatch(_NAME, probe.lstrip("@")) and probe.lstrip("@").lower() not in _NOT_A_HANDLE:
            return probe.lstrip("@")  # bare handle stored in a dedicated field
    text_sources = [candidate_data.get("raw_text")]
    sections = candidate_data.get("sections")
    if isinstance(sections, dict):
        text_sources.extend(sections.values())
    for text in text_sources:
        if isinstance(text, str):
            users = extract_github_usernames(text)
            if users:
                return users[0]
    return None


# --------------------------------------------------------------------------------------
# Language claim handling
# --------------------------------------------------------------------------------------
_KNOWN_LANGS = {
    "python", "javascript", "typescript", "java", "c++", "c", "c#", "go", "rust", "php", "ruby", "swift", "kotlin",
    "sql", "r", "scala", "bash", "shell", "html", "css", "dart", "matlab", "perl", "lua", "haskell", "elixir",
    "objective-c", "powershell", "verilog", "vhdl", "assembly", "julia", "groovy", "solidity",
}
_CLAIM_ALIASES = {
    "golang": "go", "js": "javascript", "ts": "typescript", "py": "python", "c sharp": "c#", "cpp": "c++",
    "bash/shell": "shell", "bash": "shell", "shell scripting": "shell", "html5": "html", "css3": "css",
    "html/css": "html", "node": "javascript",
}
# claimed language -> GitHub (linguist) language names that count as evidence for it
_EVIDENCE = {
    "python": {"python", "jupyter notebook"},
    "javascript": {"javascript"},
    "typescript": {"typescript"},
    "c++": {"c++"},
    "c": {"c"},
    "c#": {"c#"},
    "go": {"go"},
    "sql": {"sql", "plpgsql", "tsql", "plsql", "pl/sql", "plpgsql"},
    "shell": {"shell", "batchfile"},
    "html": {"html", "vue", "svelte"},
    "css": {"css", "scss", "sass", "less"},
    "verilog": {"verilog", "systemverilog"},
    "assembly": {"assembly"},
}
# Languages GitHub rarely attributes to application work: treated as low-weight claims.
_LOW_WEIGHT = {"sql": 0.3, "shell": 0.3, "html": 0.3, "css": 0.3, "matlab": 0.7}
_DISPLAY = {"c++": "C++", "c#": "C#", "sql": "SQL", "html": "HTML", "css": "CSS", "shell": "Shell", "php": "PHP", "r": "R",
            "javascript": "JavaScript", "typescript": "TypeScript", "objective-c": "Objective-C", "powershell": "PowerShell"}


def _norm_claim(skill: str) -> Optional[str]:
    low = skill.strip().lower()
    low = _CLAIM_ALIASES.get(low, low)
    if low in _KNOWN_LANGS:
        return low
    if _get_skill_category is not None:
        try:
            if _get_skill_category(skill) == "Programming Languages":
                return _CLAIM_ALIASES.get(skill.strip().lower(), skill.strip().lower())
        except Exception:  # pragma: no cover
            pass
    return None


def _display(lang: str) -> str:
    return _DISPLAY.get(lang, lang.title() if lang.islower() else lang)


def _mentions(text_lower: str, lang: str) -> int:
    pattern = r"(?<![a-z0-9+#])" + re.escape(lang) + r"(?![a-z0-9+#])"
    return len(re.findall(pattern, text_lower))


def extract_claimed_languages(candidate_data: Dict[str, Any]) -> List[str]:
    """Programming languages the resume claims, ordered by how often the resume mentions them."""
    skills = [str(s) for s in (candidate_data.get("skills") or []) if str(s).strip()]
    claimed: List[str] = []
    for s in skills:
        norm = _norm_claim(s)
        if norm and norm not in claimed:
            claimed.append(norm)
    text = str(candidate_data.get("raw_text") or "").lower()
    if not claimed and text:
        claimed = [lang for lang in sorted(_KNOWN_LANGS) if len(lang) > 1 and _mentions(text, lang)]
    if text:
        claimed.sort(key=lambda lang: -_mentions(text, lang))
    return claimed


# --------------------------------------------------------------------------------------
# HTTP client
# --------------------------------------------------------------------------------------
Transport = Callable[[str, str, Dict[str, str], Optional[bytes], float], Tuple[int, Dict[str, str], str]]


def _urllib_transport(method: str, url: str, headers: Dict[str, str], body: Optional[bytes], timeout: float
                      ) -> Tuple[int, Dict[str, str], str]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https endpoint
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, {k.lower(): v for k, v in (exc.headers or {}).items()}, text
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GitHubUnavailableError(f"Cannot reach GitHub: {exc}") from exc


class GitHubClient:
    """Minimal, rate-limit-aware GitHub REST/GraphQL client with an in-memory TTL cache.

    Args:
        token: Personal access token; defaults to the ``GITHUB_TOKEN`` environment variable.
        timeout: Per-request timeout in seconds.
        max_retry_wait: Longest rate-limit wait (seconds) the client will sleep through before retrying once.
            Longer waits raise ``GitHubRateLimitError`` immediately so a UI request never hangs.
        cache_ttl: Seconds to cache successful GET responses (0 disables).
        transport: Injectable HTTP function (used by tests); defaults to ``urllib``.
    """

    def __init__(self, token: Optional[str] = None, timeout: float = 10.0, max_retry_wait: float = 5.0,
                 cache_ttl: float = 900.0, transport: Optional[Transport] = None,
                 sleep: Callable[[float], None] = time.sleep):
        self.token = token if token is not None else (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        self.timeout = timeout
        self.max_retry_wait = max_retry_wait
        self.cache_ttl = cache_ttl
        self._transport = transport or _urllib_transport
        self._sleep = sleep
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_reset: Optional[int] = None
        self.requests_made = 0

    @property
    def authenticated(self) -> bool:
        return bool(self.token)

    # -- public ---------------------------------------------------------------------
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = self._url(path, params)
        cached = self._cache_get(url)
        if cached is not None:
            return cached
        data = self._request("GET", url, None)
        self._cache_put(url, data)
        return data

    def get_paginated(self, path: str, params: Optional[Dict[str, Any]] = None, max_pages: int = 3,
                      per_page: int = 100) -> List[Any]:
        items: List[Any] = []
        for page in range(1, max_pages + 1):
            merged = dict(params or {}, per_page=per_page, page=page)
            chunk = self.get(path, merged)
            if not isinstance(chunk, list):
                break
            items.extend(chunk)
            if len(chunk) < per_page:
                break
        return items

    def graphql(self, query: str, variables: Dict[str, Any]) -> Any:
        if not self.token:
            raise GitHubError("GraphQL API requires GITHUB_TOKEN")
        body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        data = self._request("POST", f"{API_BASE}/graphql", body)
        if isinstance(data, dict) and data.get("errors") and not data.get("data"):
            raise GitHubError(str(data["errors"])[:200])
        return data.get("data") if isinstance(data, dict) else None

    # -- internals ------------------------------------------------------------------
    @staticmethod
    def _url(path: str, params: Optional[Dict[str, Any]]) -> str:
        url = path if path.startswith("http") else f"{API_BASE}{path}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        return url

    def _headers(self, with_token: bool = True) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        }
        if with_token and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if with_token:
            headers["Content-Type"] = "application/json"
        return headers

    def _cache_get(self, key: str) -> Any:
        if self.cache_ttl <= 0:
            return None
        with self._lock:
            hit = self._cache.get(key)
            if hit and time.time() - hit[0] < self.cache_ttl:
                return hit[1]
            if hit:
                self._cache.pop(key, None)
        return None

    def _cache_put(self, key: str, value: Any) -> None:
        if self.cache_ttl > 0:
            with self._lock:
                if len(self._cache) > 512:
                    self._cache.clear()
                self._cache[key] = (time.time(), value)

    def _note_rate_headers(self, headers: Dict[str, str]) -> None:
        try:
            if "x-ratelimit-remaining" in headers:
                self.rate_limit_remaining = int(headers["x-ratelimit-remaining"])
            if "x-ratelimit-reset" in headers:
                self.rate_limit_reset = int(headers["x-ratelimit-reset"])
        except ValueError:
            pass

    def _request(self, method: str, url: str, body: Optional[bytes]) -> Any:
        use_token = True
        retried = False
        while True:
            self.requests_made += 1
            status, headers, text = self._transport(method, url, self._headers(use_token), body, self.timeout)
            self._note_rate_headers(headers)

            if 200 <= status < 300:
                try:
                    return json.loads(text) if text else None
                except json.JSONDecodeError as exc:
                    raise GitHubUnavailableError("GitHub returned malformed JSON") from exc
            if status == 401 and use_token and self.token:
                logger.warning("GITHUB_TOKEN rejected (401); continuing unauthenticated")
                use_token = False
                self.token = None
                continue
            if status == 404:
                raise GitHubNotFoundError(f"Not found: {url}")
            if status in (403, 429):
                wait = self._rate_limit_wait(headers, text)
                if wait is not None:
                    if wait <= self.max_retry_wait and not retried:
                        retried = True
                        self._sleep(max(wait, 0.0) + 0.25)
                        continue
                    reset_at = None
                    if self.rate_limit_reset:
                        reset_at = datetime.fromtimestamp(self.rate_limit_reset, tz=timezone.utc).isoformat()
                    raise GitHubRateLimitError(
                        f"GitHub rate limit reached; retry in about {int(wait)}s", int(wait), reset_at)
                raise GitHubError(f"GitHub refused the request (HTTP {status})")
            if status >= 500:
                raise GitHubUnavailableError(f"GitHub server error (HTTP {status})")
            raise GitHubError(f"Unexpected GitHub response (HTTP {status})")

    def _rate_limit_wait(self, headers: Dict[str, str], body: str) -> Optional[float]:
        """Seconds to wait if the response is a rate limit; ``None`` if it is some other 403."""
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                return 60.0
        if headers.get("x-ratelimit-remaining") == "0":
            reset = headers.get("x-ratelimit-reset")
            try:
                return max(0.0, float(reset) - time.time()) if reset else 60.0
            except ValueError:
                return 60.0
        if "rate limit" in (body or "").lower():
            return 60.0  # secondary limit without headers
        return None


# --------------------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------------------
@dataclass
class ResumeAuthenticityScore:
    """Cross-reference outcome between resume claims and public GitHub evidence."""

    score: Optional[float]  # 0-100, None when there is not enough public data to judge
    verdict: str  # VERIFIED | LIKELY_AUTHENTIC | PARTIALLY_VERIFIED | UNVERIFIED_CLAIMS | INSUFFICIENT_PUBLIC_DATA
    confidence: float  # 0-100: how much public evidence the score rests on
    exaggeration_risk: str  # LOW | MODERATE | HIGH | UNKNOWN
    components: Dict[str, Any] = field(default_factory=dict)
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------------------
# Inspector
# --------------------------------------------------------------------------------------
def _parse_dt(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


_PINNED_QUERY = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository {
        name description url stargazerCount forkCount pushedAt isFork
        primaryLanguage { name }
      } }
    }
  }
}
"""


class GitHubInspector:
    """Validates resume language claims against public GitHub activity.

    Args:
        client: Preconfigured ``GitHubClient``; one is created (honouring ``GITHUB_TOKEN``) if omitted.
        language_scan_limit: Max repositories for which exact per-language byte counts are fetched
            (one extra API call each). Automatically reduced when the remaining quota is low.
        max_repo_pages: Pages of 100 repositories to read (default 300 repos).
        active_window_days: Window that counts as "recently active" (default ~6 months).
        apply_exaggeration_cap: Cap the score (50 for HIGH, 70 for MODERATE exaggeration risk) when at
            least three original repositories give the evidence base real weight.
        now: Injectable clock for tests.
    """

    def __init__(self, client: Optional[GitHubClient] = None, language_scan_limit: int = 5, max_repo_pages: int = 3,
                 active_window_days: int = 183, apply_exaggeration_cap: bool = True,
                 now: Optional[Callable[[], datetime]] = None):
        self.client = client or GitHubClient()
        self.language_scan_limit = max(0, language_scan_limit)
        self.max_repo_pages = max(1, max_repo_pages)
        self.active_window_days = active_window_days
        self.apply_exaggeration_cap = apply_exaggeration_cap
        self._now = now or (lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------ entry points
    def inspect_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect the GitHub profile referenced by a parsed resume dict and score claim authenticity."""
        if not isinstance(candidate_data, dict):
            raise TypeError("candidate_data must be a dict (ResumeParser.parse output)")
        username = extract_github_username(candidate_data)
        claimed = extract_claimed_languages(candidate_data)
        exp = candidate_data.get("experience")
        years = float(exp.get("years_of_experience") or 0) if isinstance(exp, dict) else 0.0
        if not username:
            return self._empty_report("no_github_found", None, claimed,
                                      "No GitHub profile or handle was found on the resume.")
        return self.inspect_username(username, claimed_languages=claimed, claimed_years=years)

    def inspect_username(self, username: str, claimed_languages: Optional[List[str]] = None,
                         claimed_years: float = 0.0) -> Dict[str, Any]:
        """Inspect a GitHub handle. ``claimed_languages`` are the resume's languages (any casing)."""
        username = (username or "").strip().lstrip("@")
        if not re.fullmatch(_NAME, username):
            return self._empty_report("error", username or None, claimed_languages or [], "Invalid GitHub username.")
        claimed: List[str] = []
        for c in claimed_languages or []:
            n = _norm_claim(str(c)) or str(c).strip().lower()
            if n and n not in claimed:
                claimed.append(n)

        notes: List[str] = []
        partial = False
        try:
            profile = self.client.get(f"/users/{username}")
        except GitHubNotFoundError:
            return self._empty_report("user_not_found", username, claimed,
                                      f"GitHub user '{username}' does not exist. The resume link may be mistyped or outdated.")
        except GitHubRateLimitError as exc:
            return self._empty_report("rate_limited", username, claimed,
                                      "GitHub rate limit reached; try again later or set GITHUB_TOKEN.",
                                      retry_after_seconds=exc.retry_after_seconds, reset_at=exc.reset_at)
        except GitHubUnavailableError as exc:
            return self._empty_report("unavailable", username, claimed, f"GitHub could not be reached: {exc}")
        except GitHubError as exc:
            return self._empty_report("error", username, claimed, str(exc))

        repos: List[Dict[str, Any]] = []
        try:
            repos = self.client.get_paginated(f"/users/{username}/repos", {"type": "owner", "sort": "pushed"},
                                              max_pages=self.max_repo_pages)
        except GitHubRateLimitError:
            partial = True
            notes.append("Rate limit hit while listing repositories; repository metrics are missing.")
        except GitHubError as exc:
            partial = True
            notes.append(f"Repository list unavailable: {exc}")

        now = self._now()
        original = [r for r in repos if not r.get("fork")]
        forks = [r for r in repos if r.get("fork")]

        language_data, lang_notes, lang_partial = self._language_breakdown(username, original)
        notes.extend(lang_notes)
        partial = partial or lang_partial

        activity = self._activity(username, repos, original, now)
        if activity.pop("_events_failed", False):
            partial = True
            notes.append("Public events feed unavailable; 90-day commit activity is not included.")

        repo_summary = self._repo_summary(repos, original, forks)
        pinned, pinned_source = self._pinned(username, original)
        maturity = self._maturity(original)
        created = _parse_dt(profile.get("created_at"))
        account_age_years = round((now - created).days / 365.25, 1) if created else None

        authenticity = self._score(claimed, language_data, activity, repo_summary, maturity, account_age_years,
                                   original, activity.get("_events_available", False), claimed_years)
        activity.pop("_events_available", None)

        flags, positives = self._flags(claimed, authenticity, activity, repo_summary, account_age_years, claimed_years)

        report = {
            "status": "partial" if partial else "ok",
            "username": profile.get("login") or username,
            "profile_url": profile.get("html_url") or f"https://github.com/{username}",
            "authenticity_score": authenticity.score,
            "verdict": authenticity.verdict,
            "confidence": authenticity.confidence,
            "resume_authenticity": authenticity.to_dict(),
            "summary": self._summary(authenticity, activity, repo_summary, claimed, language_data),
            "claimed_languages": [_display(c) for c in claimed],
            "language_breakdown": language_data["breakdown"],
            "language_data_source": language_data["source"],
            "language_verification": authenticity.components.get("language_verification", []),
            "profile": {
                "name": profile.get("name"), "bio": profile.get("bio"), "company": profile.get("company"),
                "followers": profile.get("followers"), "following": profile.get("following"),
                "public_repos": profile.get("public_repos"), "created_at": profile.get("created_at"),
                "account_age_years": account_age_years,
            },
            "repositories": repo_summary,
            "pinned_repositories": pinned,
            "pinned_repositories_source": pinned_source,
            "repo_maturity_index": maturity,
            "activity": activity,
            "positives": positives,
            "flags": flags,
            "notes": notes,
            "rate_limit": self._rate_state(),
            "caveat": ("Absence of public activity is not proof of exaggeration: private and employer repositories "
                       "are invisible to this check. Use the score as one signal alongside interviews."),
        }
        return report

    # ------------------------------------------------------------------ collection helpers
    def _language_breakdown(self, username: str, original: List[Dict[str, Any]]
                            ) -> Tuple[Dict[str, Any], List[str], bool]:
        """Language percentages by bytes for the top original repos, plus presence data from all original repos."""
        notes: List[str] = []
        partial = False
        primary_repos: Dict[str, int] = Counter()
        primary_size: Dict[str, int] = defaultdict(int)
        for r in original:
            lang = r.get("language")
            if lang:
                primary_repos[lang] += 1
                primary_size[lang] += int(r.get("size") or 0)

        scan_n = self.language_scan_limit
        remaining = self.client.rate_limit_remaining
        if remaining is not None:
            scan_n = max(0, min(scan_n, remaining - 3))
        ranked = sorted([r for r in original if int(r.get("size") or 0) > 0],
                        key=lambda r: (int(r.get("stargazers_count") or 0), r.get("pushed_at") or ""), reverse=True)
        bytes_by_lang: Dict[str, int] = defaultdict(int)
        scanned = 0
        for r in ranked[:scan_n]:
            try:
                langs = self.client.get(f"/repos/{username}/{r['name']}/languages")
            except GitHubRateLimitError:
                partial = True
                notes.append("Rate limit hit during language scan; using repository primary languages for the rest.")
                break
            except GitHubError:
                continue
            if isinstance(langs, dict) and langs:
                scanned += 1
                for lang, b in langs.items():
                    bytes_by_lang[lang] += int(b)

        if scanned:
            source, weights = "linguist_bytes", dict(bytes_by_lang)
        else:
            source, weights = "repo_size_estimate", {k: v for k, v in primary_size.items()}
            if not weights and primary_repos:
                weights = {k: float(v) for k, v in primary_repos.items()}
        total = float(sum(weights.values())) or 1.0
        languages = set(weights) | set(primary_repos)
        breakdown = []
        for lang in languages:
            breakdown.append({
                "language": lang,
                "percent": round(100.0 * weights.get(lang, 0) / total, 1) if weights else 0.0,
                "bytes": int(bytes_by_lang.get(lang, 0)),
                "repos_as_primary_language": int(primary_repos.get(lang, 0)),
                "presence_only": lang not in weights or weights.get(lang, 0) == 0,
            })
        breakdown.sort(key=lambda x: (-x["percent"], -x["repos_as_primary_language"], x["language"]))
        return {"breakdown": breakdown[:12], "source": source if breakdown else "none",
                "scanned_repos": scanned}, notes, partial

    def _activity(self, username: str, repos: List[Dict[str, Any]], original: List[Dict[str, Any]],
                  now: datetime) -> Dict[str, Any]:
        pushes: List[datetime] = [d for d in (_parse_dt(r.get("pushed_at")) for r in original) if d]
        events: List[Dict[str, Any]] = []
        events_failed = False
        try:
            events = self.client.get_paginated(f"/users/{username}/events/public", max_pages=2)
        except GitHubError:
            events_failed = True
        push_events = [e for e in events if e.get("type") == "PushEvent"]
        event_dates = [d for d in (_parse_dt(e.get("created_at")) for e in events) if d]

        commits = 0
        basis = "push_events"
        for e in push_events:
            payload = e.get("payload") or {}
            n = payload.get("distinct_size", payload.get("size"))
            if n is None and isinstance(payload.get("commits"), list):
                n = len(payload["commits"])
            if n is not None:
                basis = "payload_commit_counts"
            commits += int(n) if n is not None else 1

        candidates = pushes + event_dates
        last = max(candidates) if candidates else None
        days_since = (now - last).days if last else None
        window = self.active_window_days
        recent_repos = [r for r in original if (d := _parse_dt(r.get("pushed_at"))) and (now - d).days <= window]
        year_repos = [r for r in original if (d := _parse_dt(r.get("pushed_at"))) and (now - d).days <= 365]
        if days_since is None:
            status = "no_activity_found"
        elif days_since <= window:
            status = "active"
        elif days_since <= 730:
            status = "dormant"
        else:
            status = "abandoned"
        return {
            "status": status,
            "active_within_6_months": status == "active",
            "last_activity_at": last.isoformat() if last else None,
            "days_since_last_activity": days_since,
            "original_repos_pushed_last_6_months": len(recent_repos),
            "original_repos_pushed_last_12_months": len(year_repos),
            "push_events_90d": len(push_events),
            "estimated_commits_90d": commits,
            "commit_count_basis": basis,
            "distinct_repos_touched_90d": len({(e.get("repo") or {}).get("name") for e in push_events}),
            "_events_failed": events_failed,
            "_events_available": not events_failed,
        }

    @staticmethod
    def _repo_summary(repos: List[Dict[str, Any]], original: List[Dict[str, Any]], forks: List[Dict[str, Any]]
                      ) -> Dict[str, Any]:
        def entry(r: Dict[str, Any]) -> Dict[str, Any]:
            lic = r.get("license") or {}
            return {
                "name": r.get("name"), "url": r.get("html_url"), "description": r.get("description"),
                "language": r.get("language"), "stars": int(r.get("stargazers_count") or 0),
                "forks": int(r.get("forks_count") or 0), "pushed_at": r.get("pushed_at"),
                "topics": r.get("topics") or [], "license": lic.get("spdx_id") if isinstance(lic, dict) else None,
                "archived": bool(r.get("archived")),
            }

        top = sorted(original, key=lambda r: (int(r.get("stargazers_count") or 0) * 3 + int(r.get("forks_count") or 0) * 2,
                                              r.get("pushed_at") or ""), reverse=True)
        return {
            "total_public": len(repos),
            "original": len(original),
            "forked": len(forks),
            "archived": sum(1 for r in original if r.get("archived")),
            "total_stars": sum(int(r.get("stargazers_count") or 0) for r in original),
            "total_forks_received": sum(int(r.get("forks_count") or 0) for r in original),
            "top_repositories": [entry(r) for r in top[:6]],
        }

    def _pinned(self, username: str, original: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
        if self.client.authenticated:
            try:
                data = self.client.graphql(_PINNED_QUERY, {"login": username})
                nodes = (((data or {}).get("user") or {}).get("pinnedItems") or {}).get("nodes") or []
                pinned = [{
                    "name": n.get("name"), "url": n.get("url"), "description": n.get("description"),
                    "language": (n.get("primaryLanguage") or {}).get("name"),
                    "stars": n.get("stargazerCount"), "forks": n.get("forkCount"), "pushed_at": n.get("pushedAt"),
                } for n in nodes if n]
                return pinned, "graphql"
            except GitHubError as exc:
                logger.info("Pinned repository lookup failed: %s", exc)
        ranked = sorted(original, key=lambda r: (int(r.get("stargazers_count") or 0), r.get("pushed_at") or ""), reverse=True)
        featured = [{
            "name": r.get("name"), "url": r.get("html_url"), "description": r.get("description"),
            "language": r.get("language"), "stars": int(r.get("stargazers_count") or 0),
            "forks": int(r.get("forks_count") or 0), "pushed_at": r.get("pushed_at"),
        } for r in ranked[:6]]
        return featured, "heuristic_top_repos"

    @staticmethod
    def _maturity(original: List[Dict[str, Any]]) -> float:
        """0-1 average of simple hygiene signals over the 10 most recently pushed original repos."""
        sample = sorted(original, key=lambda r: r.get("pushed_at") or "", reverse=True)[:10]
        if not sample:
            return 0.0
        scores = []
        for r in sample:
            pts = 0
            pts += 1 if r.get("description") else 0
            pts += 1 if r.get("license") else 0
            pts += 1 if r.get("topics") else 0
            pts += 1 if int(r.get("stargazers_count") or 0) > 0 else 0
            pts += 1 if int(r.get("size") or 0) >= 100 else 0
            pts += 1 if r.get("homepage") else 0
            scores.append(pts / 6.0)
        return round(sum(scores) / len(scores), 3)

    # ------------------------------------------------------------------ scoring
    def _score(self, claimed: List[str], language_data: Dict[str, Any], activity: Dict[str, Any],
               repo_summary: Dict[str, Any], maturity: float, account_age_years: Optional[float],
               original: List[Dict[str, Any]], events_available: bool, claimed_years: float
               ) -> ResumeAuthenticityScore:
        n_original = repo_summary["original"]
        breakdown = language_data["breakdown"]
        gh_percent = {b["language"].lower(): b for b in breakdown}

        # Evidence richness -> confidence.
        richness = (0.6 * min(1.0, n_original / 5.0) + 0.2 * min(1.0, len(breakdown) / 3.0)
                    + 0.2 * (1.0 if events_available and activity["push_events_90d"] else 0.0))
        confidence = round(100.0 * richness, 1)

        if n_original == 0:
            return ResumeAuthenticityScore(
                score=None, verdict="INSUFFICIENT_PUBLIC_DATA", confidence=0.0, exaggeration_risk="UNKNOWN",
                components={"language_verification": [], "reason": "no original public repositories"},
                interpretation="The account has no original public repositories, so no claim can be verified or refuted.")

        # 1) Language verification.
        verification: List[Dict[str, Any]] = []
        weight_sum = 0.0
        credit = 0.0
        for lang in claimed:
            names = _EVIDENCE.get(lang, {lang})
            hits = [gh_percent[n] for n in names if n in gh_percent]
            pct = round(sum(h["percent"] for h in hits), 1)
            repo_count = sum(h["repos_as_primary_language"] for h in hits)
            if hits and (pct >= 3.0 or repo_count >= 2):
                status, value = "verified", 1.0
            elif hits:
                status, value = "weak", 0.5
            else:
                status, value = "unverified", 0.0
            weight = _LOW_WEIGHT.get(lang, 1.0)
            weight_sum += weight
            credit += weight * value
            verification.append({"language": _display(lang), "status": status, "github_percent": pct,
                                 "repos_as_primary_language": repo_count, "weight": weight})
        lang_score = (100.0 * credit / weight_sum) if weight_sum else None

        # Exaggeration risk.
        risk = "UNKNOWN"
        unverified_ratio = None
        core_unverified = False
        if verification:
            heavy = [v for v in verification if v["weight"] >= 0.7]
            pool = heavy or verification
            unverified_ratio = sum(1 for v in pool if v["status"] == "unverified") / len(pool)
            core_unverified = verification[0]["status"] == "unverified" and verification[0]["weight"] >= 0.7
            if (len(pool) >= 3 and unverified_ratio >= 0.5) or (core_unverified and unverified_ratio >= 0.34):
                risk = "HIGH"
            elif unverified_ratio >= 0.34 or core_unverified:
                risk = "MODERATE"
            else:
                risk = "LOW"

        # 2) Activity credibility.
        days = activity["days_since_last_activity"]
        if days is None:
            recency = 0.0
        elif days <= 90:
            recency = 100.0
        elif days <= self.active_window_days:
            recency = 80.0
        elif days <= 365:
            recency = 45.0
        elif days <= 730:
            recency = 20.0
        else:
            recency = 5.0
        act_parts: List[Tuple[float, float]] = [
            (0.45, recency),
            (0.20, 100.0 * min(1.0, n_original / 6.0)),
            (0.20, 100.0 * min(1.0, activity["original_repos_pushed_last_12_months"] / 3.0)),
        ]
        if events_available:
            act_parts.append((0.15, 100.0 * min(1.0, activity["push_events_90d"] / 8.0)))
        activity_score = sum(w * v for w, v in act_parts) / sum(w for w, _ in act_parts)

        # 3) Profile substance (kept gentle on stars: most good engineers have few).
        stars_part = 100.0 * min(1.0, math.log10(1 + repo_summary["total_stars"]) / 2.0)
        forks_part = 100.0 * min(1.0, math.log10(1 + repo_summary["total_forks_received"]) / 1.5)
        originality = 100.0 * (n_original / repo_summary["total_public"]) if repo_summary["total_public"] else 0.0
        age_part = 100.0 * min(1.0, (account_age_years or 0.0) / 3.0)
        substance_score = 0.25 * stars_part + 0.10 * forks_part + 0.30 * (maturity * 100.0) + 0.15 * originality + 0.20 * age_part

        if lang_score is not None:
            score = 0.55 * lang_score + 0.25 * activity_score + 0.20 * substance_score
        else:
            score = (0.25 * activity_score + 0.20 * substance_score) / 0.45
            confidence = round(confidence * 0.7, 1)

        cap_applied = None
        if self.apply_exaggeration_cap and n_original >= 3:
            if risk == "HIGH" and score > 50:
                score, cap_applied = 50.0, 50
            elif risk == "MODERATE" and score > 70:
                score, cap_applied = 70.0, 70
        score = round(_clamp(score), 1)

        if confidence < 25:
            verdict = "INSUFFICIENT_PUBLIC_DATA"
        elif score >= 80:
            verdict = "VERIFIED"
        elif score >= 60:
            verdict = "LIKELY_AUTHENTIC"
        elif score >= 40:
            verdict = "PARTIALLY_VERIFIED"
        else:
            verdict = "UNVERIFIED_CLAIMS"

        interpretation = {
            "VERIFIED": "Public repositories corroborate the claimed languages and show real, recent engineering work.",
            "LIKELY_AUTHENTIC": "Most claims are corroborated by public work; remaining gaps are plausible given private code.",
            "PARTIALLY_VERIFIED": "Some claims are corroborated but several languages have little or no public evidence. Probe them in the interview.",
            "UNVERIFIED_CLAIMS": "Few claimed languages appear in public work. This may reflect private repositories or exaggeration; verify with a live exercise.",
            "INSUFFICIENT_PUBLIC_DATA": "The public footprint is too small to support a reliable judgement.",
        }[verdict]
        components = {
            "language_verification": verification,
            "language_score": None if lang_score is None else round(lang_score, 1),
            "activity_score": round(activity_score, 1),
            "substance_score": round(substance_score, 1),
            "weights": {"language": 0.55 if lang_score is not None else 0.0, "activity": 0.25, "substance": 0.20},
            "unverified_ratio": None if unverified_ratio is None else round(unverified_ratio, 2),
            "core_language_unverified": core_unverified,
            "exaggeration_cap_applied": cap_applied,
        }
        return ResumeAuthenticityScore(score=score, verdict=verdict, confidence=confidence,
                                       exaggeration_risk=risk, components=components, interpretation=interpretation)

    # ------------------------------------------------------------------ narrative
    @staticmethod
    def _flags(claimed: List[str], auth: ResumeAuthenticityScore, activity: Dict[str, Any],
               repos: Dict[str, Any], age_years: Optional[float], claimed_years: float) -> Tuple[List[str], List[str]]:
        flags: List[str] = []
        positives: List[str] = []
        ver = auth.components.get("language_verification", [])
        unverified = [v["language"] for v in ver if v["status"] == "unverified"]
        verified = [v["language"] for v in ver if v["status"] == "verified"]
        if verified:
            positives.append("Languages verified in public repositories: " + ", ".join(verified) + ".")
        if auth.exaggeration_risk in ("HIGH", "MODERATE") and unverified:
            flags.append(f"{auth.exaggeration_risk} exaggeration risk: no public evidence for " + ", ".join(unverified) + ".")
        elif unverified:
            flags.append("No public evidence for: " + ", ".join(unverified) + " (may be private work).")
        if auth.components.get("core_language_unverified"):
            flags.append(f"The resume's most-emphasised language ({ver[0]['language']}) does not appear in public repositories.")
        status = activity.get("status")
        if status == "active":
            positives.append(f"Active in the last 6 months ({activity['estimated_commits_90d']} commits across "
                             f"{activity['push_events_90d']} push event(s) in 90 days).")
        elif status == "dormant":
            flags.append(f"Dormant: last public activity {activity['days_since_last_activity']} days ago.")
        elif status == "abandoned":
            flags.append(f"Abandoned account: last public activity {activity['days_since_last_activity']} days ago.")
        if repos["total_public"] and repos["forked"] / repos["total_public"] > 0.7:
            flags.append("Most public repositories are forks rather than original work.")
        if repos["total_stars"] >= 50:
            positives.append(f"{repos['total_stars']} total stars across original repositories.")
        if age_years is not None and claimed_years >= 3 and age_years < 1:
            flags.append("GitHub account is under a year old while the resume claims 3+ years of experience "
                         "(earlier work may be private or on another platform).")
        return flags, positives

    @staticmethod
    def _summary(auth: ResumeAuthenticityScore, activity: Dict[str, Any], repos: Dict[str, Any],
                 claimed: List[str], language_data: Dict[str, Any]) -> str:
        if auth.score is None:
            return auth.interpretation
        top = ", ".join(f"{b['language']} {b['percent']:.0f}%" for b in language_data["breakdown"][:3] if b["percent"] > 0)
        return (f"Authenticity {auth.score:.0f}/100 ({auth.verdict}, confidence {auth.confidence:.0f}). "
                f"{repos['original']} original repos, {activity['status']} account"
                + (f", top languages: {top}." if top else "."))

    # ------------------------------------------------------------------ misc
    def _rate_state(self) -> Dict[str, Any]:
        reset = (datetime.fromtimestamp(self.client.rate_limit_reset, tz=timezone.utc).isoformat()
                 if self.client.rate_limit_reset else None)
        return {"authenticated": self.client.authenticated, "remaining": self.client.rate_limit_remaining,
                "reset_at": reset, "requests_made": self.client.requests_made}

    def _empty_report(self, status: str, username: Optional[str], claimed: List[str], message: str,
                      retry_after_seconds: Optional[int] = None, reset_at: Optional[str] = None) -> Dict[str, Any]:
        verdict = {"user_not_found": "UNVERIFIED_CLAIMS"}.get(status, "INSUFFICIENT_PUBLIC_DATA")
        auth = ResumeAuthenticityScore(
            score=None, verdict=verdict, confidence=0.0, exaggeration_risk="UNKNOWN",
            components={"language_verification": []}, interpretation=message)
        flags = ["The GitHub handle on the resume does not exist."] if status == "user_not_found" else []
        return {
            "status": status, "username": username,
            "profile_url": f"https://github.com/{username}" if username else None,
            "authenticity_score": None, "verdict": verdict, "confidence": 0.0,
            "resume_authenticity": auth.to_dict(), "summary": message,
            "claimed_languages": [_display(c) for c in claimed],
            "language_breakdown": [], "language_data_source": "none", "language_verification": [],
            "profile": {}, "repositories": {}, "pinned_repositories": [], "pinned_repositories_source": None,
            "repo_maturity_index": None, "activity": {}, "positives": [], "flags": flags, "notes": [message],
            "retry_after_seconds": retry_after_seconds, "reset_at": reset_at,
            "rate_limit": self._rate_state(),
            "caveat": "No score was produced; treat this as 'unknown', not as a negative signal.",
        }


def inspect_candidate_github(candidate_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper: inspect the GitHub footprint of a parsed resume dict."""
    return GitHubInspector(client=GitHubClient(token=token)).inspect_candidate(candidate_data)

"""
Multi-Agent Recruiter Council
=============================

A consensus evaluation engine in which four specialist "recruiter" personas review a
parsed candidate profile against a parsed job description, cross-examine one another,
and hand a synthesized executive verdict to the hiring team.

Agents
------
1. ``TechLeadAgent``                     - architecture depth, craftsmanship, tooling, repo maturity.
2. ``CultureRetentionAgent``             - tenure consistency, progression, promotion velocity.
3. ``FairHiringAuditor``                 - audits the *other* agents for bias, produces a merit-only score.
4. ``SeniorityCompensationEstimator``    - L3-L6 leveling plus US (USD) and India (INR) comp bands.

Orchestration (``RecruitmentCouncil.evaluate_candidate_council``)
-----------------------------------------------------------------
    Round 1  independent scorecards (Tech Lead, Culture/Retention, Seniority/Comp)
    Round 1b optional LLM enrichment of each scorecard (Gemini / OpenAI) - never required
    Round 2  Fair Hiring Auditor reviews the evaluation (incl. any LLM-written text)
    Round 3  cross-examination "debate" between agents (deterministic, data-driven)
    Final    ExecutiveConsensus: weighted score, verdict, bulleted executive reasoning

Design guarantees
-----------------
* **Works offline.** Every agent has a deterministic local heuristic implementation.
  An LLM key only *enriches* qualitative text and nudges two agents' scores by at most
  +/-10 points. The final verdict is always computed locally so it stays auditable.
* **Privacy-aware LLM calls.** Name, e-mail, phone and profile URLs are redacted before any
  profile text leaves the process.
* **No new dependencies.** Standard library only. LLM calls use plain HTTPS (``urllib``) so
  they cannot conflict with ``google-generativeai`` or ``openai`` SDK versions. If the
  project's ``src.core.skill_ontology`` / ``src.config`` are importable they are used for
  skill-alias matching and ``.env`` loading; otherwise built-in fallbacks apply.
* **Fairness by construction.** Candidate name, gender, age, photo, nationality, college
  prestige, location and employment gaps never enter any score.

Typical use
-----------
    from src.core.agentic_council import RecruitmentCouncil

    council = RecruitmentCouncil()                       # offline unless a key is configured
    result = council.evaluate_candidate_council(candidate_data, jd_data)
    result["executive_consensus"]["verdict"]             # "STRONG_HIRE" | "HIRE" | "LEAN_HIRE" | "REJECT"

``candidate_data`` is the dict produced by ``ResumeParser.parse`` (keys such as ``skills``,
``experience``, ``projects``, ``sections``, ``raw_text``); ``jd_data`` is the dict produced by
``JDParser.parse`` (``job_title``, ``required_skills``, ``preferred_skills``,
``min_experience_years``). An optional ``candidate_data["github_report"]`` (output of
``GitHubInspector``) is used as extra repo-maturity evidence when present.

Compensation bands are *indicative defaults* for planning conversations, not market data.
Override them with ``RecruitmentCouncil(comp_bands=...)`` to match your own calibration.
"""

from __future__ import annotations

import json
import logging
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

try:  # Optional: reuse the project's ontology for alias-aware skill matching.
    from src.core.skill_ontology import SKILL_ONTOLOGY as _SKILL_ONTOLOGY
except Exception:  # pragma: no cover - ontology is optional
    _SKILL_ONTOLOGY = {}

logger = logging.getLogger(__name__)

__all__ = [
    "Verdict",
    "AgentScorecard",
    "ExecutiveConsensus",
    "TechLeadAgent",
    "CultureRetentionAgent",
    "FairHiringAuditor",
    "SeniorityCompensationEstimator",
    "RecruitmentCouncil",
    "evaluate_candidate_council",
]

COUNCIL_VERSION = "1.0.0"


# --------------------------------------------------------------------------------------
# Public data structures
# --------------------------------------------------------------------------------------
class Verdict(str, Enum):
    """Final hiring recommendation."""

    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    LEAN_HIRE = "LEAN_HIRE"
    REJECT = "REJECT"


@dataclass
class AgentScorecard:
    """One agent's independent evaluation.

    ``score`` is 0-100. For the ``FairHiringAuditor`` the score is the *merit-only* score
    (skills, experience fit, delivery evidence); its evaluation-integrity rating lives in
    ``metrics["fairness_integrity_score"]``.
    """

    agent: str
    role: str
    score: float
    rating: str
    summary: str
    observations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    source: str = "local"  # "local" or "local+llm:<provider>"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutiveConsensus:
    """Synthesized council decision."""

    verdict: str
    final_score: float
    confidence: float
    headline: str
    reasoning: List[str]
    reasoning_markdown: str
    weights_used: Dict[str, float]
    estimated_level: str
    compensation: Dict[str, Any]
    dissent: List[str] = field(default_factory=list)
    red_flags: List[Dict[str, str]] = field(default_factory=list)
    human_review_required: bool = False
    human_review_reasons: List[str] = field(default_factory=list)
    interview_focus: List[str] = field(default_factory=list)
    llm_narrative: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------------------
# Shared constants and helpers
# --------------------------------------------------------------------------------------
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_ALT = "jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec"
_DATE_RANGE_RE = re.compile(
    rf"(?:\b(?P<sm>{_MONTH_ALT})[a-z]*\.?,?\s+)?(?P<sy>(?:19|20)\d{{2}})\s*(?:-|–|—|to|until|till)\s*"
    rf"(?:\b(?P<em>{_MONTH_ALT})[a-z]*\.?,?\s+)?"
    rf"(?P<ey>(?:19|20)\d{{2}}|present|current|now|ongoing|till\s+date)\b",
    re.IGNORECASE,
)
_NON_JOB_LINE_RE = re.compile(
    r"\b(b\.?\s?tech|b\.?e\.?|m\.?\s?tech|m\.?e\.?|b\.?sc|m\.?sc|b\.?s\.?|m\.?s\.?|mba|phd|ph\.d|bca|mca|"
    r"diploma|university|college|institute|school|cgpa|gpa|percentage|certif\w*|course|project)\b",
    re.IGNORECASE,
)

# (regex, rank). Rank scale: 0 intern .. 5 principal/director.
_TITLE_RANKS: List[Tuple[re.Pattern, int]] = [
    (re.compile(r"\b(intern|internship|trainee|apprentice)\b", re.I), 0),
    (re.compile(r"\b(principal|distinguished|fellow|chief|head of|director|vp|vice president|architect)\b", re.I), 5),
    (re.compile(r"\b(staff|lead|manager|tech lead|team lead)\b", re.I), 4),
    (re.compile(r"\b(senior|sr\.?)\b", re.I), 3),
    (re.compile(r"\b(junior|jr\.?|associate|graduate|entry[- ]level)\b", re.I), 1),
]

_ARCHITECTURE_TERMS = [
    "microservices", "distributed", "system design", "scalab", "high availability", "event-driven",
    "event driven", "message queue", "kafka", "rabbitmq", "grpc", "load balanc", "caching", "redis",
    "sharding", "kubernetes", "service mesh", "api gateway", "serverless", "design pattern",
    "domain-driven", "cqrs", "observability", "monitoring", "terraform", "infrastructure as code",
    "fault toleran", "low latency", "multi-tenant", "data pipeline", "rest api", "graphql",
]
_CRAFT_TERMS = [
    "unit test", "pytest", "integration test", "test-driven", "tdd", "ci/cd", "github actions",
    "jenkins", "code review", "linting", "static analysis", "documentation", "refactor", "pull request",
    "type hint", "typescript", "sonarqube", "pre-commit", "design doc",
]
_SCOPE_TERMS = [
    "led", "lead", "mentored", "mentoring", "architected", "owned", "ownership", "spearheaded",
    "managed", "roadmap", "designed", "drove", "introduced", "established", "hired", "interviewed",
    "cross-functional", "stakeholder", "migrated", "scaled",
]
_DEPLOY_TERMS = [
    "deployed", "production", "docker", "kubernetes", "aws", "azure", "gcp", "released", "shipped",
    "live users", "ci/cd", "heroku", "vercel",
]
_IMPACT_RE = re.compile(
    r"(\d+(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?x\b|"
    r"\b\d[\d,\.]*\s?[kKmM]?\+?\s+(?:monthly\s+active\s+users|active\s+users|users|customers|requests|req/s|rps|"
    r"transactions|records|ms)\b)",
    re.IGNORECASE,
)

_PROTECTED_FIELD_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("date of birth / age", re.compile(r"\b(date of birth|d\.?o\.?b\.?|born on|age\s*[:\-]|\d{2}\s*years?\s*old)\b", re.I)),
    ("gender", re.compile(r"\b(gender|sex)\s*[:\-]", re.I)),
    ("marital / family status", re.compile(r"\b(marital status|married|unmarried|spouse|father'?s name|mother'?s name)\b", re.I)),
    ("religion / caste", re.compile(r"\b(religion|caste|community)\s*[:\-]", re.I)),
    ("nationality", re.compile(r"\b(nationality|citizenship)\s*[:\-]", re.I)),
    ("photograph", re.compile(r"\b(photograph|passport[- ]size photo)\b", re.I)),
]

_BIAS_PATTERNS: List[Tuple[str, str, re.Pattern]] = [
    ("age", "high", re.compile(r"\b(young|youthful|too old|too young|digital native|fresh blood|energetic|age)\b", re.I)),
    ("gender", "high", re.compile(r"\b(he|she|his|her|him|male|female|woman|women|girl|boy|maternity|pregnan\w*|manpower)\b", re.I)),
    ("family status", "high", re.compile(r"\b(married|single|kids|children|family (?:commitments|obligations)|spouse)\b", re.I)),
    ("nationality / language", "medium", re.compile(r"\b(native speaker|accent|foreigner|visa status)\b", re.I)),
    ("pedigree proxy", "medium", re.compile(r"\b(tier[- ]?1 (?:college|university)|ivy|top[- ]tier (?:college|university|institution)|iit|nit|prestigious (?:college|university))\b", re.I)),
    ("vague culture-fit language", "low", re.compile(r"\b(culture fit|cultural fit|gut feel|gut feeling|vibe|likeab\w+)\b", re.I)),
    ("overqualification stereotype", "medium", re.compile(r"\boverqualified\b", re.I)),
    ("employment-gap penalty", "medium", re.compile(r"\b(career gap|employment gap|resume gap|gap in employment|unexplained gap)\b", re.I)),
]

_REDACT_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_REDACT_PHONE = re.compile(r"(?<![\d.])(?:\+?\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s-]?\d{3,5}(?:[\s-]?\d{3,5})?(?![\d.])")
_REDACT_URL = re.compile(r"(?:https?://|www\.)\S+|(?:linkedin|github)\.com/\S+", re.I)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _rating(score: float) -> str:
    if score >= 85:
        return "Exceptional"
    if score >= 70:
        return "Strong"
    if score >= 55:
        return "Moderate"
    if score >= 40:
        return "Weak"
    return "Poor"


@lru_cache(maxsize=2048)
def _term_regex(term: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(term.lower().strip()) + r"(?![a-z0-9])")


def _contains_term(text_lower: str, term: str) -> bool:
    """Boundary-aware containment (so 'go' does not match 'google', 'c++' still works)."""
    if not term or not term.strip():
        return False
    return _term_regex(term).search(text_lower) is not None


def _contains_stem(text_lower: str, stem: str) -> bool:
    """Prefix containment used for architecture terms such as 'scalab' -> scalable/scalability."""
    return stem in text_lower


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _title_rank(text: str) -> int:
    for pattern, rank in _TITLE_RANKS:
        if pattern.search(text or ""):
            return rank
    return 2


def _skill_aliases(skill: str) -> List[str]:
    entry = _SKILL_ONTOLOGY.get(skill)
    aliases = list(entry.get("aliases", [])) if entry else []
    return [skill.lower()] + [a.lower() for a in aliases]


# --------------------------------------------------------------------------------------
# Feature extraction (computed once, shared by all agents)
# --------------------------------------------------------------------------------------
@dataclass
class _Role:
    label: str
    start: Tuple[int, int]  # (year, month)
    end: Tuple[int, int]
    months: int
    rank: int
    is_intern: bool
    is_current: bool


@dataclass
class _Features:
    name: str
    text: str
    text_lower: str
    skills: List[str]
    skills_lower: Set[str]
    years: float
    fulltime_years: float
    titles: List[str]
    projects: List[Dict[str, Any]]
    timeline: List[_Role]
    jd_title: str
    jd_text_lower: str
    required: List[str]
    preferred: List[str]
    req_hits: List[str]
    req_missing: List[str]
    pref_hits: List[str]
    min_years: float
    coverage: float
    pref_coverage: float
    req_evidenced: List[str]
    evid_coverage: float
    unevidenced_ratio: float
    hype_unevidenced: List[str]
    inverted_dates: int
    impact_hits: List[str]
    arch_terms: List[str]
    craft_terms: List[str]
    scope_terms: List[str]
    deploy_terms: List[str]
    github: Optional[Dict[str, Any]]
    word_count: int

    @property
    def has_timeline(self) -> bool:
        return bool(self.timeline)


def _month_number(token: Optional[str]) -> Optional[int]:
    if not token:
        return None
    t = token.lower()
    return _MONTHS.get(t[:4]) or _MONTHS.get(t[:3])


def _parse_timeline(text: str, today: datetime) -> List[_Role]:
    """Extract dated roles from free text. Education / project / certification lines are ignored."""
    roles: List[_Role] = []
    lines = [ln.strip() for ln in (text or "").splitlines()]
    for idx, line in enumerate(lines):
        match = _DATE_RANGE_RE.search(line)
        if not match or _NON_JOB_LINE_RE.search(line):
            continue
        sy = int(match.group("sy"))
        end_token = match.group("ey").lower()
        is_current = not end_token[0].isdigit()
        ey = today.year if is_current else int(end_token)
        if sy > ey or sy < 1980 or ey > today.year:
            continue
        sm_given = match.group("sm")
        em_given = match.group("em")
        sm = _month_number(sm_given)
        em = today.month if is_current else _month_number(em_given)
        # Year-only boundaries are assumed mid-year, which matches the project's parser convention.
        s_month = sm if sm else 6
        e_month = em if em else 6
        months = (ey - sy) * 12 + (e_month - s_month)
        months = max(months, 6 if sy == ey and not (sm and em) else 1)

        label = (line[: match.start()] + " " + line[match.end():]).strip(" |-–—,()[]:@")
        if len(label) < 4:
            for prev in range(idx - 1, max(idx - 3, -1), -1):
                if lines[prev] and not _DATE_RANGE_RE.search(lines[prev]):
                    label = lines[prev]
                    break
        label = re.sub(r"\s+", " ", label)[:140] or "Role"
        rank = _title_rank(label)
        roles.append(
            _Role(
                label=label,
                start=(sy, s_month),
                end=(ey, e_month),
                months=months,
                rank=rank,
                is_intern=rank == 0,
                is_current=is_current,
            )
        )
    roles.sort(key=lambda r: r.start)
    return roles


def _merged_months(roles: Sequence[_Role]) -> int:
    """Total months across roles with overlapping intervals merged (concurrent jobs counted once)."""
    spans = sorted((r.start[0] * 12 + r.start[1], r.start[0] * 12 + r.start[1] + r.months) for r in roles)
    total, cur_s, cur_e = 0, None, None
    for s, e in spans:
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s
    return total


def _collect_text(candidate: Dict[str, Any]) -> str:
    raw = candidate.get("raw_text")
    if isinstance(raw, str) and raw.strip():
        return raw
    parts: List[str] = []
    sections = candidate.get("sections")
    if isinstance(sections, dict):
        parts.extend(str(v) for v in sections.values() if isinstance(v, str))
    for proj in _as_list(candidate.get("projects")):
        if isinstance(proj, dict):
            parts.append(f"{proj.get('title', '')} {proj.get('description', '')} {' '.join(map(str, _as_list(proj.get('skills_used'))))}")
    parts.append(" ".join(str(s) for s in _as_list(candidate.get("skills"))))
    return "\n".join(p for p in parts if p)


_HYPE_SKILLS = ["quantum computing", "quantum", "blockchain", "web3", "metaverse", "solidity", "agi"]
_SKILLS_HEADER_RE = re.compile(r"^\s*(?:technical\s+)?(?:skills|core competencies|technologies|tech stack)\b", re.I)


_SECTION_BREAK_RE = re.compile(
    r"^\s*(?:work\s+|professional\s+)?(?:experience|education|projects?|key\s+projects|certifications?|summary|"
    r"professional\s+summary|achievements|awards|internships?|employment|publications|languages|interests)\b.{0,40}$", re.I)


def _strip_skills_block(text: str) -> str:
    """Remove the skills list so that skills can be checked for *proof* elsewhere (experience, projects)."""
    out: List[str] = []
    skipping = False
    for line in text.splitlines():
        if _SKILLS_HEADER_RE.match(line):
            skipping = True
            continue
        if skipping:
            if not line.strip() or _SECTION_BREAK_RE.match(line) or (line.strip().isupper() and len(line.strip()) < 40):
                skipping = False  # next section starts; fall through to keep this line
            else:
                continue
        out.append(line)
    return "\n".join(out)


def _count_inverted_dates(text: str, today: datetime) -> int:
    n = 0
    for m in re.finditer(r"((?:19|20)\d{2})\s*(?:-|\u2013|\u2014|to)\s*((?:19|20)\d{2}|present|current)", text, re.I):
        end = today.year if not m.group(2)[0].isdigit() else int(m.group(2))
        if int(m.group(1)) > end or end > today.year + 1:
            n += 1
    return n


def _build_features(candidate: Dict[str, Any], jd: Dict[str, Any], today: Optional[datetime] = None) -> _Features:
    today = today or datetime.now()
    text = _collect_text(candidate)
    text_lower = text.lower()
    skills = [str(s) for s in _as_list(candidate.get("skills")) if str(s).strip()]
    skills_lower = {s.lower() for s in skills}

    exp = candidate.get("experience")
    parsed_years = 0.0
    titles: List[str] = []
    if isinstance(exp, dict):
        parsed_years = _as_float(exp.get("years_of_experience"))
        titles = [str(t) for t in _as_list(exp.get("detected_titles"))]
    elif isinstance(exp, (int, float)):
        parsed_years = float(exp)

    sections = candidate.get("sections") if isinstance(candidate.get("sections"), dict) else {}
    exp_text = sections.get("experience") if isinstance(sections.get("experience"), str) else ""
    timeline = _parse_timeline(exp_text if exp_text.strip() else text, today)
    timeline_years = _merged_months(timeline) / 12.0 if timeline else 0.0
    fulltime = [r for r in timeline if not r.is_intern]
    fulltime_years = _merged_months(fulltime) / 12.0 if fulltime else 0.0

    years = parsed_years if parsed_years > 0 else timeline_years
    if timeline and fulltime_years > 0:
        leveling_years = fulltime_years
    elif timeline:
        leveling_years = fulltime_years  # only internships on record
    else:
        leveling_years = years

    required = [str(s) for s in _as_list(jd.get("required_skills")) if str(s).strip()]
    preferred = [str(s) for s in _as_list(jd.get("preferred_skills")) if str(s).strip()]

    def has_skill(skill: str) -> bool:
        aliases = _skill_aliases(skill)
        if any(a in skills_lower for a in aliases):
            return True
        return any(_contains_term(text_lower, a) for a in aliases)

    req_hits = [s for s in required if has_skill(s)]
    req_missing = [s for s in required if s not in req_hits]
    pref_hits = [s for s in preferred if has_skill(s)]
    coverage = (len(req_hits) / len(required)) if required else 0.0
    body_lower = _strip_skills_block(text).lower()

    def evidenced(skill: str) -> bool:
        return any(_contains_term(body_lower, a) for a in _skill_aliases(skill))

    req_evidenced = [s for s in req_hits if evidenced(s)]
    # A skill that is only listed (never used in experience / projects) earns half credit.
    evid_coverage = ((len(req_evidenced) + 0.5 * (len(req_hits) - len(req_evidenced))) / len(required)) if required else 0.0
    unevidenced = [s for s in skills if not evidenced(s)]
    unevidenced_ratio = (len(unevidenced) / len(skills)) if skills else 0.0
    hype_unevidenced = [s for s in unevidenced if s.lower() in _HYPE_SKILLS]
    pref_coverage = (len(pref_hits) / len(preferred)) if preferred else 0.0

    projects = [p for p in _as_list(candidate.get("projects")) if isinstance(p, dict)]
    github = candidate.get("github_report") if isinstance(candidate.get("github_report"), dict) else None

    return _Features(
        name=str(candidate.get("candidate_name") or candidate.get("name") or "Candidate"),
        text=text,
        text_lower=text_lower,
        skills=skills,
        skills_lower=skills_lower,
        years=years,
        fulltime_years=leveling_years,
        titles=titles,
        projects=projects,
        timeline=timeline,
        jd_title=str(jd.get("job_title") or "the role"),
        jd_text_lower=str(jd.get("raw_text") or "").lower(),
        required=required,
        preferred=preferred,
        req_hits=req_hits,
        req_missing=req_missing,
        pref_hits=pref_hits,
        min_years=_as_float(jd.get("min_experience_years")),
        coverage=coverage,
        pref_coverage=pref_coverage,
        req_evidenced=req_evidenced,
        evid_coverage=evid_coverage,
        unevidenced_ratio=unevidenced_ratio,
        hype_unevidenced=hype_unevidenced,
        inverted_dates=_count_inverted_dates(text, today),
        impact_hits=sorted({m.group(0).strip() for m in _IMPACT_RE.finditer(text)}, key=str.lower),
        arch_terms=[t for t in _ARCHITECTURE_TERMS if _contains_stem(text_lower, t)],
        craft_terms=[t for t in _CRAFT_TERMS if _contains_stem(text_lower, t)],
        scope_terms=[t for t in _SCOPE_TERMS if _contains_term(text_lower, t)],
        deploy_terms=[t for t in _DEPLOY_TERMS if _contains_term(text_lower, t)],
        github=github,
        word_count=len(text.split()),
    )


# --------------------------------------------------------------------------------------
# Agents
# --------------------------------------------------------------------------------------
class _BaseAgent:
    """Common contract for council agents."""

    key: str = "agent"
    name: str = "Agent"
    role: str = ""
    persona_prompt: str = ""
    #: Maximum LLM nudge to this agent's score, in points. 0 disables score adjustment.
    llm_score_adjust_limit: int = 0

    def evaluate(self, f: _Features, peers: Optional[Sequence[AgentScorecard]] = None) -> AgentScorecard:
        raise NotImplementedError

    def _card(self, score: float, summary: str, obs: List[str], strengths: List[str],
              concerns: List[str], metrics: Dict[str, Any]) -> AgentScorecard:
        score = round(_clamp(score), 1)
        return AgentScorecard(
            agent=self.name, role=self.role, score=score, rating=_rating(score), summary=summary,
            observations=obs, strengths=strengths, concerns=concerns, metrics=metrics,
        )


class TechLeadAgent(_BaseAgent):
    """Principal-engineer lens: skill coverage, architectural depth, craftsmanship, delivery proof."""

    key = "tech_lead"
    name = "TechLeadAgent"
    role = "Technical depth: architecture, code craftsmanship, tooling breadth, repo maturity"
    llm_score_adjust_limit = 10
    persona_prompt = (
        "You are a skeptical but fair Principal Engineer reviewing a candidate. Judge system-architecture depth, "
        "code craftsmanship, depth of tooling (not just keyword lists), evidence of production delivery and repo "
        "maturity. Prefer concrete evidence (metrics, shipped systems) over buzzwords."
    )

    def evaluate(self, f: _Features, peers: Optional[Sequence[AgentScorecard]] = None) -> AgentScorecard:
        coverage = f.evid_coverage if f.required else 0.65  # JD without parsed skills: neutral-positive
        depth = min(1.0, len(f.arch_terms) / 6.0)
        craft = min(1.0, len(f.craft_terms) / 4.0)
        impact = min(1.0, len(f.impact_hits) / 3.0)
        breadth = min(1.0, len(f.skills) / 12.0)

        rich_projects = [p for p in f.projects if len(str(p.get("description", ""))) >= 80]
        shipped = [
            p for p in f.projects
            if any(_contains_term(f"{p.get('title', '')} {p.get('description', '')}".lower(), t) for t in _DEPLOY_TERMS)
        ]
        maturity = min(1.0, 0.5 * min(1.0, len(rich_projects) / 3.0) + 0.5 * min(1.0, len(shipped) / 2.0))
        github_note = None
        if f.github:
            gh_score = f.github.get("authenticity_score", f.github.get("score"))
            if isinstance(gh_score, (int, float)):
                maturity = min(1.0, 0.7 * maturity + 0.3 * (float(gh_score) / 100.0))
                github_note = f"GitHub inspector authenticity score is {float(gh_score):.0f}/100."
        elif "github.com" in f.text_lower:
            maturity = min(1.0, maturity + 0.05)

        score = 100 * (0.40 * coverage + 0.20 * depth + 0.10 * craft + 0.10 * impact + 0.10 * maturity + 0.10 * breadth)

        obs: List[str] = []
        strengths: List[str] = []
        concerns: List[str] = []
        if f.required:
            obs.append(
                f"Lists {len(f.req_hits)}/{len(f.required)} required skills; {len(f.req_evidenced)} are backed by evidence in "
                f"experience or projects (evidence-weighted coverage {coverage:.0%}) for {f.jd_title}.")
            if f.req_hits:
                strengths.append(f"Direct match on required stack: {', '.join(f.req_hits[:6])}.")
            if f.req_missing:
                concerns.append(f"No evidence for required skills: {', '.join(f.req_missing[:6])}.")
        else:
            obs.append("The job description lists no parsed required skills, so skill coverage is scored neutrally.")
        if f.preferred:
            obs.append(f"Preferred-skill overlap: {len(f.pref_hits)}/{len(f.preferred)}.")
        if f.arch_terms:
            obs.append(f"Architecture vocabulary found: {', '.join(f.arch_terms[:6])}.")
        if depth >= 0.5:
            strengths.append("Shows hands-on exposure to distributed / scalable system design concepts.")
        else:
            concerns.append("Little evidence of system-design or architecture-level work in the resume.")
        if craft >= 0.5:
            strengths.append(f"Engineering hygiene signals present ({', '.join(f.craft_terms[:4])}).")
        else:
            concerns.append("No clear testing, CI/CD or code-review practice mentioned.")
        if f.impact_hits:
            strengths.append(f"Quantified delivery impact: {', '.join(f.impact_hits[:3])}.")
        else:
            concerns.append("Achievements are not quantified (no users, latency, throughput or % improvements).")
        if f.projects:
            obs.append(f"{len(f.projects)} project(s) listed; {len(shipped)} reference deployment or production use.")
        else:
            concerns.append("No projects are listed to validate tool depth.")
        if github_note:
            obs.append(github_note)
        if len(f.skills) > 25:
            concerns.append("Very long skills list; breadth may be keyword stuffing, so probe depth on the top 3 tools.")
        if len(f.skills) >= 10 and f.unevidenced_ratio >= 0.6:
            concerns.append(f"{f.unevidenced_ratio:.0%} of listed skills have no supporting evidence in experience or projects.")

        summary = (
            f"Technical fit is {_rating(score).lower()}: {coverage:.0%} required-skill coverage, "
            f"{len(f.arch_terms)} architecture signals and {len(f.impact_hits)} quantified outcomes."
        )
        metrics = {
            "required_skill_coverage": round(coverage, 3),
            "required_skills_listed": len(f.req_hits),
            "required_skills_evidenced": len(f.req_evidenced),
            "unevidenced_skill_ratio": round(f.unevidenced_ratio, 3),
            "architecture_signals": len(f.arch_terms),
            "craftsmanship_signals": len(f.craft_terms),
            "quantified_impacts": len(f.impact_hits),
            "projects_with_deployment_evidence": len(shipped),
            "repo_maturity_index": round(maturity, 3),
            "missing_required_skills": f.req_missing,
        }
        return self._card(score, summary, obs, strengths, concerns, metrics)


class CultureRetentionAgent(_BaseAgent):
    """People-analytics lens: tenure, stability, progression, promotion velocity.

    Employment gaps are reported as information only and never reduce the score, because gaps
    correlate with caregiving, health and layoffs and are not predictive of job performance.
    """

    key = "culture_retention"
    name = "CultureRetentionAgent"
    role = "Career progression, tenure consistency, job stability, promotion velocity"
    llm_score_adjust_limit = 10
    persona_prompt = (
        "You are a retention-focused talent partner. Analyse career progression, tenure consistency and promotion "
        "velocity from the dated work history only. Never penalise employment gaps, never infer personal "
        "circumstances, and avoid vague 'culture fit' language - cite concrete tenure facts."
    )

    def evaluate(self, f: _Features, peers: Optional[Sequence[AgentScorecard]] = None) -> AgentScorecard:
        obs: List[str] = []
        strengths: List[str] = []
        concerns: List[str] = []
        jobs = [r for r in f.timeline if not r.is_intern]
        interns = [r for r in f.timeline if r.is_intern]

        if not jobs:
            score = 62.0
            if interns:
                obs.append(f"Early-career profile with {len(interns)} internship(s) and no full-time history yet.")
                strengths.append("Internship experience shows early exposure to professional environments.")
            else:
                obs.append("No dated employment history was detected, so tenure and progression cannot be assessed.")
            obs.append("Scored neutrally: absence of history is not treated as a negative signal.")
            summary = "Insufficient dated employment history; neutral retention outlook (low confidence)."
            return self._card(score, summary, obs, strengths, concerns, {
                "roles_detected": len(f.timeline), "confidence": "low", "average_tenure_months": None,
            })

        completed = [r for r in jobs if not r.is_current]
        avg_tenure = statistics.mean(r.months for r in jobs)
        short = [r for r in completed if r.months < 10]
        current = next((r for r in reversed(jobs) if r.is_current), None)
        rank_changes = [jobs[i + 1].rank - jobs[i].rank for i in range(len(jobs) - 1)]
        promotions = sum(1 for d in rank_changes if d > 0)
        regressions = sum(1 for d in rank_changes if d < 0)
        total_years = max(_merged_months(jobs) / 12.0, 0.5)
        promo_velocity = promotions / total_years

        score = 68.0
        if avg_tenure >= 30:
            score += 14
            strengths.append(f"Long average tenure of {avg_tenure / 12:.1f} years per role signals stability.")
        elif avg_tenure >= 18:
            score += 8
            strengths.append(f"Healthy average tenure of {avg_tenure / 12:.1f} years per role.")
        elif avg_tenure < 12:
            score -= 12
            concerns.append(f"Short average tenure ({avg_tenure:.0f} months per role).")
        obs.append(f"{len(jobs)} full-time role(s); average tenure {avg_tenure:.0f} months.")

        if short:
            score -= min(24, 8 * len(short))
            concerns.append(f"{len(short)} completed role(s) lasted under 10 months; ask about the context for each move.")
        if promotions:
            score += min(18, 9 * promotions)
            strengths.append(f"{promotions} step(s) up in title across roles (about {promo_velocity:.2f} per year).")
        elif len(jobs) >= 2 and total_years >= 4:
            obs.append("No visible title progression across several years; may reflect IC-track growth that titles do not show.")
            score -= 3
        if regressions:
            score -= 4 * regressions
            obs.append(f"{regressions} move(s) to a lower title band; could be a deliberate stack or domain change.")
        if current and current.months >= 24:
            score += 4
            obs.append(f"Currently {current.months / 12:.1f} years in the present role.")
        if len(jobs) >= 2:
            gaps = 0
            for prev, nxt in zip(jobs, jobs[1:]):
                prev_end = prev.end[0] * 12 + prev.end[1]
                nxt_start = nxt.start[0] * 12 + nxt.start[1]
                if nxt_start - prev_end > 6:
                    gaps += 1
            if gaps:
                obs.append(f"{gaps} timeline interval(s) of 6+ months between roles; noted for information only and not scored.")

        if len(jobs) < 2:
            score = min(score, 78.0)
            obs.append("Only one full-time role on record, so progression cannot be assessed; score capped at 78.")
        summary = (
            f"Career trajectory looks {_rating(score).lower()}: avg tenure {avg_tenure / 12:.1f} yrs, "
            f"{promotions} promotion(s), {len(short)} short stint(s)."
        )
        metrics = {
            "roles_detected": len(jobs),
            "average_tenure_months": round(avg_tenure, 1),
            "short_stints_under_10_months": len(short),
            "promotions_detected": promotions,
            "promotion_velocity_per_year": round(promo_velocity, 2),
            "regressions_detected": regressions,
            "confidence": "medium" if len(jobs) >= 2 else "low",
        }
        return self._card(score, summary, obs, strengths, concerns, metrics)


class FairHiringAuditor(_BaseAgent):
    """Bias auditor. Reviews the other agents' output and computes a merit-only score.

    The merit score uses only job-relevant evidence: required/preferred skill coverage, experience
    versus the JD minimum, and evidence of delivered work. It never sees name, gender, age, location,
    school or employment gaps. This agent is deliberately run *after* the others and *after* any
    LLM enrichment, so it also audits machine-written prose.
    """

    key = "fair_auditor"
    name = "FairHiringAuditor"
    role = "Bias audit and merit-only skill scoring"
    llm_score_adjust_limit = 0  # the merit score stays deterministic
    persona_prompt = (
        "You are a Fair Hiring auditor. Review the other reviewers' comments for unconscious bias: age, gender, "
        "family status, nationality, college-prestige proxies, vague 'culture fit' and employment-gap penalties. "
        "Report only concrete findings that quote the offending phrase."
    )

    def evaluate(self, f: _Features, peers: Optional[Sequence[AgentScorecard]] = None) -> AgentScorecard:
        peers = list(peers or [])
        flags: List[Dict[str, Any]] = []

        # 1) Scan peer prose for biased language.
        for card in peers:
            blob = " ".join([card.summary, *card.observations, *card.strengths, *card.concerns])
            for category, severity, pattern in _BIAS_PATTERNS:
                m = pattern.search(blob)
                if m:
                    flags.append({
                        "agent": card.agent, "category": category, "severity": severity,
                        "evidence": m.group(0), "action": "Disregard this comment and re-justify using job-related evidence.",
                    })

        # 2) Merit-only score.
        req_part = f.evid_coverage if f.required else 0.6
        pref_part = f.pref_coverage if f.preferred else req_part
        skills_component = 50 * (0.8 * req_part + 0.2 * pref_part)
        if f.min_years > 0:
            exp_component = 25 * min(1.0, f.years / f.min_years)
        else:
            exp_component = 25 * 0.8
        project_evidence = len([p for p in f.projects if len(str(p.get("description", ""))) >= 60])
        evidence_component = 25 * (0.5 * min(1.0, len(f.impact_hits) / 3.0) + 0.5 * min(1.0, project_evidence / 3.0))
        merit = _clamp(skills_component + exp_component + evidence_component)

        # 3) Score divergence between the merit view and the subjective peers.
        subjective = [c.score for c in peers if c.agent in (TechLeadAgent.name, CultureRetentionAgent.name)]
        if subjective:
            gap = statistics.mean(subjective) - merit
            if abs(gap) > 18:
                flags.append({
                    "agent": "Council", "category": "merit divergence",
                    "severity": "medium" if abs(gap) > 28 else "low",
                    "evidence": f"peer mean {statistics.mean(subjective):.0f} vs merit-only {merit:.0f}",
                    "action": "Check that non-merit factors are not driving the subjective scores.",
                })

        # 4) Protected attributes visible in the resume (information + redaction advice, not scored).
        present = [label for label, pat in _PROTECTED_FIELD_PATTERNS if pat.search(f.text)]

        penalty = sum({"high": 25, "medium": 12, "low": 5}[x["severity"]] for x in flags)
        integrity = _clamp(100 - penalty)
        neutralized = sorted({x["agent"] for x in flags if x["agent"] in {TechLeadAgent.name, CultureRetentionAgent.name,
                                                                          SeniorityCompensationEstimator.name}
                              and x["severity"] in ("high", "medium")})

        obs = [
            f"Merit-only score {merit:.0f}/100 = skills {skills_component:.0f}/50 + experience fit {exp_component:.0f}/25 "
            f"+ delivery evidence {evidence_component:.0f}/25.",
            "Name, gender, age, location, school prestige and employment gaps were excluded from every score.",
        ]
        strengths: List[str] = []
        concerns: List[str] = []
        if not flags:
            strengths.append("No biased language or non-merit drivers detected in the other reviewers' output.")
        for x in flags:
            concerns.append(f"[{x['severity'].upper()}] {x['agent']}: {x['category']} - \"{x['evidence']}\". {x['action']}")
        if present:
            concerns.append(
                "Resume contains protected-attribute fields (" + ", ".join(present) + "). Redact them before human review; "
                "they were not used in scoring."
            )

        summary = (
            f"Evaluation integrity {integrity:.0f}/100 with {len(flags)} flag(s); merit-only score {merit:.0f}."
            if flags else f"Evaluation is clean on bias checks (integrity {integrity:.0f}/100); merit-only score {merit:.0f}."
        )
        metrics = {
            "fairness_integrity_score": round(integrity, 1),
            "merit_score": round(merit, 1),
            "bias_flags": flags,
            "neutralized_agents": neutralized,
            "protected_fields_in_resume": present,
            "merit_components": {
                "skills_out_of_50": round(skills_component, 1),
                "experience_fit_out_of_25": round(exp_component, 1),
                "delivery_evidence_out_of_25": round(evidence_component, 1),
            },
        }
        return self._card(merit, summary, obs, strengths, concerns, metrics)


# Indicative total-compensation planning bands. Override via RecruitmentCouncil(comp_bands=...).
DEFAULT_COMP_BANDS: Dict[int, Dict[str, Any]] = {
    3: {"title": "L3 - Associate Engineer", "usd": (85_000, 125_000), "inr_lpa": (6.0, 14.0)},
    4: {"title": "L4 - Software Engineer", "usd": (120_000, 175_000), "inr_lpa": (14.0, 28.0)},
    5: {"title": "L5 - Senior Engineer", "usd": (170_000, 250_000), "inr_lpa": (28.0, 50.0)},
    6: {"title": "L6 - Principal Engineer", "usd": (240_000, 380_000), "inr_lpa": (50.0, 90.0)},
}


class SeniorityCompensationEstimator(_BaseAgent):
    """Predicts L3-L6 level and compensation bands, then scores fit against the JD's target level."""

    key = "seniority_comp"
    name = "SeniorityCompensationEstimator"
    role = "Seniority leveling (L3-L6) and compensation band estimation (USD and INR)"
    llm_score_adjust_limit = 0
    persona_prompt = (
        "You are a compensation and leveling analyst. Estimate engineering level L3 (Associate) to L6 (Principal) "
        "from years of full-time experience, scope of ownership and title history, and state your confidence."
    )

    def __init__(self, comp_bands: Optional[Dict[int, Dict[str, Any]]] = None):
        self.bands = comp_bands or DEFAULT_COMP_BANDS

    @staticmethod
    def jd_target_level(f: _Features) -> int:
        title = f.jd_title.lower()
        if re.search(r"\b(principal|staff|architect|distinguished)\b", title):
            return 6
        if re.search(r"\b(senior|sr\.?|lead)\b", title):
            return 5
        if re.search(r"\b(junior|jr\.?|associate|intern|graduate|trainee|entry)\b", title):
            return 3
        if f.min_years >= 9:
            return 6
        if f.min_years >= 5:
            return 5
        if f.min_years >= 2:
            return 4
        return 3

    def estimate_level(self, f: _Features) -> Tuple[int, List[str]]:
        years = f.fulltime_years
        notes: List[str] = []
        if years < 2:
            level = 3
        elif years < 5:
            level = 4
        elif years < 9:
            level = 5
        else:
            level = 6
        notes.append(f"Base level L{level} from {years:.1f} years of full-time experience.")

        max_rank = max([r.rank for r in f.timeline] + [_title_rank(t) for t in f.titles] + [2])
        scope = len(f.scope_terms)
        if level < 6 and scope >= 4 and max_rank >= 4 and years >= {3: 1.5, 4: 4.0, 5: 7.5}[level]:
            level += 1
            notes.append(f"Promoted one band: {scope} scope signals ({', '.join(f.scope_terms[:4])}) and a lead-level title.")
        elif level >= 5 and scope < 2 and max_rank < 3:
            level -= 1
            notes.append("Lowered one band: tenure is long but title and ownership signals are limited.")
        if level == 6 and (scope < 3 or max_rank < 4):
            level = 5
            notes.append("Capped at L5: Principal level needs explicit org-level scope and lead/staff-level titles.")
        return level, notes

    def evaluate(self, f: _Features, peers: Optional[Sequence[AgentScorecard]] = None) -> AgentScorecard:
        level, notes = self.estimate_level(f)
        target = self.jd_target_level(f)
        diff = level - target
        fit_table = {0: 100, 1: 82, 2: 60, 3: 40, -1: 70, -2: 42, -3: 20}
        score = float(fit_table.get(max(-3, min(3, diff)), 20))

        band = self.bands[level]
        usd_lo, usd_hi = band["usd"]
        lpa_lo, lpa_hi = band["inr_lpa"]
        position = _clamp(0.25 + 0.45 * (f.coverage if f.required else 0.5) + 0.30 * min(1.0, len(f.scope_terms) / 6.0), 0.0, 1.0)
        comp = {
            "level": f"L{level}",
            "level_title": band["title"],
            "jd_target_level": f"L{target}",
            "usd": {
                "currency": "USD", "min": usd_lo, "max": usd_hi,
                "suggested_target": int(round((usd_lo + position * (usd_hi - usd_lo)) / 1000.0) * 1000),
            },
            "inr": {
                "currency": "INR", "unit": "LPA (lakhs per annum)", "min_lpa": lpa_lo, "max_lpa": lpa_hi,
                "suggested_target_lpa": round(lpa_lo + position * (lpa_hi - lpa_lo), 1),
                "min_inr": int(lpa_lo * 100_000), "max_inr": int(lpa_hi * 100_000),
            },
            "band_position_pct": int(round(position * 100)),
            "disclaimer": "Indicative total-compensation planning bands; calibrate against current market data before making offers.",
        }

        obs = list(notes)
        obs.append(f"Target level for {f.jd_title} is L{target}; estimated candidate level is L{level}.")
        obs.append(
            f"Indicative band: ${usd_lo:,.0f}-${usd_hi:,.0f} (US) and INR {lpa_lo:g}-{lpa_hi:g} LPA (India); "
            f"suggested placement at {comp['band_position_pct']}% of the band."
        )
        strengths: List[str] = []
        concerns: List[str] = []
        if diff == 0:
            strengths.append(f"Estimated level L{level} matches the role's target level.")
        elif diff > 0:
            concerns.append(
                f"Candidate scopes {diff} level(s) above the role (L{level} vs L{target}); expectations on scope and pay may exceed the role. "
                "Consider whether a higher-level opening is a better match."
            )
        else:
            concerns.append(f"Candidate scopes {-diff} level(s) below the role (L{level} vs L{target}); expect a ramp-up period or a level exception.")
        if f.years and not f.has_timeline:
            obs.append("Leveling is based on stated years only; no dated roles were found, so confidence is medium.")
        summary = f"Estimated {band['title']} against a target of L{target}; level-fit score {score:.0f}/100."
        metrics = {
            "estimated_level": f"L{level}",
            "estimated_level_number": level,
            "jd_target_level_number": target,
            "level_delta": diff,
            "fulltime_years_used": round(f.fulltime_years, 1),
            "scope_signals": f.scope_terms[:8],
            "compensation": comp,
        }
        return self._card(score, summary, obs, strengths, concerns, metrics)


# --------------------------------------------------------------------------------------
# Optional LLM bridge (REST only: no SDK dependency)
# --------------------------------------------------------------------------------------
def _load_project_settings() -> Any:
    try:  # honours .env through the project's pydantic settings when available
        from src.config import get_settings  # type: ignore

        return get_settings()
    except Exception:
        return None


class _LLMBridge:
    """Calls Gemini or OpenAI over HTTPS. Every failure degrades to ``None``; it never raises."""

    def __init__(self, enabled: Optional[bool], provider: Optional[str], api_key: Optional[str],
                 model: Optional[str], timeout: float):
        settings = _load_project_settings()
        env_provider = (provider or os.environ.get("COUNCIL_LLM_PROVIDER") or os.environ.get("LLM_PROVIDER")
                        or getattr(settings, "LLM_PROVIDER", "") or "").strip().lower()
        gemini_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        openai_key = os.environ.get("OPENAI_API_KEY")

        chosen: Optional[str] = None
        if env_provider in ("gemini", "openai"):
            chosen = env_provider
        elif enabled or (enabled is None and env_provider not in ("mock", "none", "off", "disabled") and (gemini_key or openai_key or api_key)):
            # Auto-detect from whichever key exists.
            chosen = "gemini" if (gemini_key or (api_key and not openai_key)) else "openai"

        self.provider = chosen
        key = api_key or (gemini_key if chosen == "gemini" else openai_key)
        self.api_key = key
        self.timeout = timeout
        if chosen == "gemini":
            self.model = model or os.environ.get("COUNCIL_LLM_MODEL") or getattr(settings, "LLM_MODEL", None) or "gemini-1.5-flash"
        else:
            self.model = model or os.environ.get("COUNCIL_LLM_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        self.enabled = bool(enabled is not False and chosen and key)
        self.errors: List[str] = []

    def complete_json(self, system: str, user: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            if self.provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                body = {
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
                }
                headers = {"Content-Type": "application/json", "x-goog-api-key": str(self.api_key)}
                payload = self._post(url, body, headers)
                text = payload["candidates"][0]["content"]["parts"][0]["text"]
            else:
                base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
                body = {
                    "model": self.model,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                }
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
                payload = self._post(f"{base}/chat/completions", body, headers)
                text = payload["choices"][0]["message"]["content"]
            return self._extract_json(text)
        except urllib.error.HTTPError as exc:
            self.errors.append(f"HTTP {exc.code} from {self.provider}")
        except Exception as exc:  # network, timeout, malformed payload ...
            self.errors.append(f"{type(exc).__name__}: {str(exc)[:120]}")
        return None

    def _post(self, url: str, body: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 - fixed https endpoints
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            data = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None


def _redact(text: str, name: str) -> str:
    out = _REDACT_EMAIL.sub("[email]", text)
    out = _REDACT_URL.sub("[link]", out)
    out = _REDACT_PHONE.sub("[phone]", out)
    for token in {name.strip(), *[t for t in name.split() if len(t) >= 3]}:
        if token and token != "Candidate":
            out = re.sub(re.escape(token), "Candidate", out, flags=re.I)
    return out


# --------------------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------------------
class RecruitmentCouncil:
    """Runs the four-agent council and synthesizes an executive consensus.

    Args:
        use_llm: ``None`` (default) auto-enables the LLM when a Gemini/OpenAI key is configured and
            ``LLM_PROVIDER`` is not ``mock``; ``True`` forces an attempt; ``False`` stays fully offline.
        llm_provider: ``"gemini"`` or ``"openai"``. Defaults to env / project settings / key auto-detect.
        api_key: Explicit key. Otherwise ``GEMINI_API_KEY`` / ``OPENAI_API_KEY`` are read.
        llm_model: Model id override (env ``COUNCIL_LLM_MODEL``; otherwise the project's ``LLM_MODEL``).
        llm_timeout: Per-request timeout in seconds.
        weights: Consensus weights for ``tech_lead``, ``merit`` (auditor), ``culture_retention``, ``seniority_fit``.
        comp_bands: Replacement compensation table, same shape as ``DEFAULT_COMP_BANDS``.
    """

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "tech_lead": 0.35, "merit": 0.25, "culture_retention": 0.20, "seniority_fit": 0.20,
    }
    VERDICT_THRESHOLDS: List[Tuple[float, Verdict]] = [
        (80.0, Verdict.STRONG_HIRE), (68.0, Verdict.HIRE), (55.0, Verdict.LEAN_HIRE),
    ]

    def __init__(
        self,
        use_llm: Optional[bool] = None,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_timeout: float = 25.0,
        weights: Optional[Dict[str, float]] = None,
        comp_bands: Optional[Dict[int, Dict[str, Any]]] = None,
    ):
        self.tech_lead = TechLeadAgent()
        self.culture = CultureRetentionAgent()
        self.auditor = FairHiringAuditor()
        self.seniority = SeniorityCompensationEstimator(comp_bands)
        self.llm = _LLMBridge(use_llm, llm_provider, api_key, llm_model, llm_timeout)
        merged = dict(self.DEFAULT_WEIGHTS)
        if weights:
            merged.update({k: float(v) for k, v in weights.items() if k in merged})
        total = sum(merged.values()) or 1.0
        self.weights = {k: v / total for k, v in merged.items()}

    # ------------------------------------------------------------------ public API
    def evaluate_candidate_council(self, candidate_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate one candidate against one job description.

        Returns a dict with:
            ``candidate_name``, ``job_title``,
            ``agent_scorecards`` - ``{agent_key: AgentScorecard-as-dict}`` (score 0-100, observations,
                strengths, concerns, metrics),
            ``debate`` - ordered cross-examination transcript,
            ``executive_consensus`` - ``ExecutiveConsensus`` as dict (``verdict`` is one of
                STRONG_HIRE / HIRE / LEAN_HIRE / REJECT, plus bulleted ``reasoning``),
            ``meta`` - timing, LLM status and version.
        """
        if not isinstance(candidate_data, dict):
            raise TypeError("candidate_data must be a dict (ResumeParser.parse output)")
        if not isinstance(jd_data, dict):
            raise TypeError("jd_data must be a dict (JDParser.parse output)")

        started = time.perf_counter()
        f = _build_features(candidate_data, jd_data)

        # Round 1: independent evaluations.
        tech = self.tech_lead.evaluate(f)
        culture = self.culture.evaluate(f)
        seniority = self.seniority.evaluate(f)

        # Round 1b: optional LLM enrichment (qualitative text + bounded nudges), in parallel.
        llm_used = False
        if self.llm.enabled:
            llm_used = self._enrich_with_llm(f, [(self.tech_lead, tech), (self.culture, culture), (self.seniority, seniority)])

        # Round 2: bias audit over everything written so far, including LLM prose.
        audit = self.auditor.evaluate(f, [tech, culture, seniority])
        if self.llm.enabled:
            llm_used = self._enrich_with_llm(f, [(self.auditor, audit)], peers=[tech, culture, seniority]) or llm_used

        cards = {"tech_lead": tech, "culture_retention": culture, "fair_auditor": audit, "seniority_comp": seniority}

        # Round 3: deterministic cross-examination.
        debate = self._run_debate(f, tech, culture, audit, seniority)

        # Final: executive consensus.
        consensus = self._synthesize(f, tech, culture, audit, seniority)
        if self.llm.enabled:
            narrative = self._llm_narrative(f, cards, consensus)
            if narrative:
                consensus.llm_narrative = narrative
                llm_used = True

        return {
            "candidate_name": f.name,
            "job_title": f.jd_title,
            "agent_scorecards": {k: v.to_dict() for k, v in cards.items()},
            "debate": debate,
            "executive_consensus": consensus.to_dict(),
            "meta": {
                "council_version": COUNCIL_VERSION,
                "mode": f"hybrid ({self.llm.provider}:{self.llm.model})" if llm_used else "local",
                "llm_enabled": self.llm.enabled,
                "llm_used": llm_used,
                "llm_errors": list(self.llm.errors),
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "weights": self.weights,
            },
        }

    # ------------------------------------------------------------------ debate
    def _run_debate(self, f: _Features, tech: AgentScorecard, culture: AgentScorecard,
                    audit: AgentScorecard, seniority: AgentScorecard) -> List[Dict[str, str]]:
        turns: List[Dict[str, str]] = []

        def say(speaker: str, to: str, stance: str, message: str) -> None:
            turns.append({"round": str(len(turns) + 1), "speaker": speaker, "to": to, "stance": stance, "message": message})

        merit = audit.score
        say(tech.agent, "All", "opening",
            f"Technical score {tech.score:.0f}. {tech.summary}")
        say(culture.agent, "All", "opening",
            f"Retention score {culture.score:.0f}. {culture.summary}")

        gap = tech.score - culture.score
        if gap >= 18:
            tenure = culture.metrics.get("average_tenure_months")
            say(tech.agent, culture.agent, "challenge",
                "The technical case is strong. Is the retention concern strong enough to block an interview?")
            say(culture.agent, tech.agent, "clarify",
                f"Not by itself. Average tenure is {tenure} months with {culture.metrics.get('short_stints_under_10_months', 0)} short stint(s). "
                "I would explore the reasons for moves in the interview rather than reject on pattern alone.")
        elif gap <= -18:
            say(culture.agent, tech.agent, "challenge",
                "The career trajectory is solid. Are the skill gaps trainable within one quarter?")
            missing = tech.metrics.get("missing_required_skills") or []
            say(tech.agent, culture.agent, "clarify",
                f"Gaps: {', '.join(missing[:4]) or 'depth signals rather than named skills'}. "
                "A take-home or pairing round would settle whether they are trainable.")
        else:
            say(culture.agent, tech.agent, "support", "Technical and trajectory views are broadly aligned.")

        delta = seniority.metrics.get("level_delta", 0)
        if delta >= 1:
            say(seniority.agent, "All", "challenge",
                f"Estimated {seniority.metrics['estimated_level']} against a target of L{seniority.metrics['jd_target_level_number']}. "
                "Scope and pay expectations may exceed this opening; check appetite for the level before investing interview time.")
        elif delta <= -1:
            say(seniority.agent, "All", "challenge",
                f"Estimated {seniority.metrics['estimated_level']} against a target of L{seniority.metrics['jd_target_level_number']}. "
                "Hire only with a ramp plan or a level exception.")
        else:
            say(seniority.agent, "All", "support", f"Level {seniority.metrics['estimated_level']} matches the role target.")

        flags = audit.metrics.get("bias_flags", [])
        if flags:
            for fl in flags[:3]:
                say(audit.agent, fl["agent"], "challenge",
                    f"Flagged {fl['category']} ('{fl['evidence']}', severity {fl['severity']}). {fl['action']}")
        else:
            say(audit.agent, "All", "support", "No bias flags raised; every score traces back to job-related evidence.")
        peer_mean = statistics.mean([tech.score, culture.score])
        if abs(peer_mean - merit) > 18:
            say(audit.agent, tech.agent, "challenge",
                f"Merit-only score is {merit:.0f} versus a subjective mean of {peer_mean:.0f}. Please cite the evidence behind the difference.")
        say("Council Chair", "All", "closing",
            f"Weighted view: technical {tech.score:.0f}, merit {merit:.0f}, retention {culture.score:.0f}, level fit {seniority.score:.0f}. Moving to consensus.")
        for i, t in enumerate(turns, start=1):
            t["round"] = str(i)
        return turns

    # ------------------------------------------------------------------ consensus
    def _synthesize(self, f: _Features, tech: AgentScorecard, culture: AgentScorecard,
                    audit: AgentScorecard, seniority: AgentScorecard) -> ExecutiveConsensus:
        weights = dict(self.weights)
        neutralized = set(audit.metrics.get("neutralized_agents", []))
        weight_notes: List[str] = []
        key_to_agent = {"tech_lead": tech.agent, "culture_retention": culture.agent, "seniority_fit": seniority.agent}
        for key, agent_name in key_to_agent.items():
            if agent_name in neutralized:
                weights[key] *= 0.5
                weight_notes.append(f"{agent_name} weight halved after a bias flag from the auditor.")
        total = sum(weights.values())
        weights = {k: round(v / total, 4) for k, v in weights.items()}

        components = {
            "tech_lead": tech.score, "merit": audit.score,
            "culture_retention": culture.score, "seniority_fit": seniority.score,
        }
        final = _clamp(sum(components[k] * weights[k] for k in components))

        verdict = Verdict.REJECT
        for threshold, v in self.VERDICT_THRESHOLDS:
            if final >= threshold:
                verdict = v
                break

        # Knock-out gates on required skills (the part of the decision that is least subjective).
        gate_notes: List[str] = []
        if f.required:
            if f.evid_coverage < 0.25:
                if verdict != Verdict.REJECT:
                    gate_notes.append(f"Downgraded to REJECT: only {f.evid_coverage:.0%} evidence-weighted required-skill coverage.")
                verdict = Verdict.REJECT
            elif f.evid_coverage < 0.5 and verdict in (Verdict.STRONG_HIRE, Verdict.HIRE):
                gate_notes.append(f"Capped at LEAN_HIRE: only {f.evid_coverage:.0%} evidence-weighted required-skill coverage.")
                verdict = Verdict.LEAN_HIRE

        # Red flags: concrete, individually explainable risks. They also gate the verdict.
        red_flags = self._red_flags(f, tech, culture, audit, seniority)
        high = [x for x in red_flags if x["severity"] == "high"]
        if len(high) >= 2 and verdict != Verdict.REJECT:
            gate_notes.append(f"Downgraded to REJECT: {len(high)} high-severity red flags.")
            verdict = Verdict.REJECT
        elif len(high) == 1 and verdict in (Verdict.STRONG_HIRE, Verdict.HIRE):
            gate_notes.append("Capped at LEAN_HIRE: one high-severity red flag.")
            verdict = Verdict.LEAN_HIRE

        # Confidence: agreement between agents and completeness of the underlying data.
        scores = list(components.values())
        spread = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        confidence = 100 - 1.2 * spread
        if not f.has_timeline:
            confidence -= 8
        if not f.skills:
            confidence -= 15
        if f.word_count < 150:
            confidence -= 10
        if not f.required:
            confidence -= 5
        confidence = round(_clamp(confidence, 20, 99), 1)

        dissent = [
            f"{name} scored {score:.0f}, {abs(score - final):.0f} points {'above' if score > final else 'below'} the consensus."
            for name, score in [(tech.agent, tech.score), (culture.agent, culture.score),
                                (audit.agent + " (merit)", audit.score), (seniority.agent, seniority.score)]
            if abs(score - final) > 20
        ]

        review_reasons: List[str] = []
        high_flags = [x for x in audit.metrics.get("bias_flags", []) if x["severity"] == "high"]
        if high_flags:
            review_reasons.append("High-severity bias flag raised by the Fair Hiring Auditor.")
        if audit.metrics.get("fairness_integrity_score", 100) < 70:
            review_reasons.append("Evaluation integrity below 70/100.")
        if confidence < 55:
            review_reasons.append(f"Low confidence ({confidence:.0f}/100) because of sparse or conflicting data.")
        if abs(final - 55) <= 2 or abs(final - 68) <= 2:
            review_reasons.append("Score sits within 2 points of a verdict boundary.")

        comp = seniority.metrics["compensation"]
        top_strength = (tech.strengths + culture.strengths + [""])[0]
        top_concern = next((c for c in tech.concerns + culture.concerns + seniority.concerns), "")
        reasoning: List[str] = [
            f"Verdict {verdict.value} at a consensus score of {final:.0f}/100 (confidence {confidence:.0f}/100) for {f.jd_title}.",
            f"Skills: {len(f.req_hits)}/{len(f.required)} required skills evidenced"
            + (f"; missing {', '.join(f.req_missing[:4])}." if f.req_missing else ".") if f.required
            else "Skills: the JD has no parsed required skills, so skills were scored against general engineering signals.",
        ]
        if top_strength:
            reasoning.append(f"Strongest signal: {top_strength}")
        if top_concern:
            reasoning.append(f"Main risk: {top_concern}")
        reasoning.append(
            f"Leveling: {comp['level_title']} (role target {comp['jd_target_level']}); indicative band "
            f"${comp['usd']['min']:,.0f}-${comp['usd']['max']:,.0f} US, INR {comp['inr']['min_lpa']:g}-{comp['inr']['max_lpa']:g} LPA India."
        )
        reasoning.append(
            f"Fairness: integrity {audit.metrics['fairness_integrity_score']:.0f}/100 with {len(audit.metrics['bias_flags'])} flag(s); "
            f"merit-only score {audit.score:.0f}/100."
        )
        if red_flags:
            reasoning.append("Red flags: " + "; ".join(f"{x['title']} ({x['severity']})" for x in red_flags) + ".")
        else:
            reasoning.append("Red flags: none detected.")
        reasoning.extend(gate_notes + weight_notes)
        if dissent:
            reasoning.append("Dissent: " + " ".join(dissent))
        if review_reasons:
            reasoning.append("Human review recommended: " + " ".join(review_reasons))

        interview_focus: List[str] = []
        for skill in f.req_missing[:3]:
            interview_focus.append(f"Probe real experience with {skill}, or how quickly the candidate could ramp up on it.")
        if culture.metrics.get("short_stints_under_10_months"):
            interview_focus.append("Ask about the reasons behind the short-tenure roles and what the candidate wants in the next one.")
        if not f.impact_hits:
            interview_focus.append("Ask for measurable outcomes (users, latency, cost, quality) from the candidate's two best projects.")
        if seniority.metrics.get("level_delta", 0) != 0:
            interview_focus.append("Align on level and scope expectations early in the process.")
        if tech.metrics.get("architecture_signals", 0) < 3:
            interview_focus.append("Include a short system-design discussion to test architectural depth.")

        headline = {
            Verdict.STRONG_HIRE: "Strong hire - fast-track to final interviews.",
            Verdict.HIRE: "Hire - proceed to the structured interview loop.",
            Verdict.LEAN_HIRE: "Lean hire - proceed with targeted probes on the flagged gaps.",
            Verdict.REJECT: "Reject - the evidence does not support moving forward for this role.",
        }[verdict]

        return ExecutiveConsensus(
            verdict=verdict.value,
            final_score=round(final, 1),
            confidence=confidence,
            headline=headline,
            reasoning=reasoning,
            reasoning_markdown="\n".join(f"- {r}" for r in reasoning),
            weights_used=weights,
            estimated_level=comp["level"],
            compensation=comp,
            dissent=dissent,
            red_flags=red_flags,
            human_review_required=bool(review_reasons),
            human_review_reasons=review_reasons,
            interview_focus=interview_focus,
        )

    def _red_flags(self, f: _Features, tech: AgentScorecard, culture: AgentScorecard,
                   audit: AgentScorecard, seniority: AgentScorecard) -> List[Dict[str, str]]:
        """Deterministic, individually explainable hiring risks."""
        flags: List[Dict[str, str]] = []

        def add(code: str, severity: str, title: str, detail: str) -> None:
            flags.append({"code": code, "severity": severity, "title": title, "detail": detail})

        if f.min_years > 0 and f.years < 0.6 * f.min_years:
            sev = "high" if f.years < 0.35 * f.min_years else "medium"
            add("EXPERIENCE_DEFICIT", sev, "Experience deficit",
                f"{f.years:g} years of experience against a {f.min_years:g}-year requirement.")
        if f.required and len(f.req_hits) and len(f.skills) >= 10 and f.unevidenced_ratio >= 0.6:
            add("UNVERIFIED_SKILL_CLAIMS", "high", "Unverified skill claims",
                f"{f.unevidenced_ratio:.0%} of {len(f.skills)} listed skills are never used in experience or projects.")
        elif f.hype_unevidenced:
            add("UNVERIFIED_SKILL_CLAIMS", "medium", "Unverified buzzword claims",
                "Listed without evidence: " + ", ".join(f.hype_unevidenced[:5]) + ".")
        if len(f.skills) >= 25:
            add("SKILL_STUFFING", "medium", "Keyword stuffing", f"{len(f.skills)} skills listed.")
        if f.years >= 1 and not f.impact_hits:
            add("NO_QUANTIFIED_IMPACT", "medium", "No quantified impact",
                "No measurable results (users, latency, % improvement) in the resume.")
        if f.inverted_dates:
            add("DATE_INCONSISTENCY", "medium", "Inconsistent dates",
                f"{f.inverted_dates} date range(s) end before they start or lie in the future.")
        if f.required and f.coverage < 0.5 or (f.required and len(f.req_missing) >= 4):
            add("REQUIRED_SKILLS_MISSING", "medium", "Required skills missing",
                "No evidence for: " + ", ".join(f.req_missing[:6]) + ".")
        delta = seniority.metrics.get("level_delta", 0)
        if abs(delta) >= 2:
            add("LEVEL_MISMATCH", "medium", "Level mismatch",
                f"Estimated {seniority.metrics['estimated_level']} vs role target L{seniority.metrics['jd_target_level_number']}.")
        for fl in audit.metrics.get("bias_flags", []):
            if fl["severity"] == "high":
                add("BIAS_RISK", "high", "Bias risk in evaluation", f"{fl['agent']}: {fl['category']} (\"{fl['evidence']}\").")
        return flags

    # ------------------------------------------------------------------ LLM enrichment
    def _profile_for_llm(self, f: _Features) -> Dict[str, Any]:
        """Redacted, size-bounded profile. No name, e-mail, phone or profile URLs leave the process."""
        return {
            "target_role": f.jd_title,
            "required_skills": f.required,
            "preferred_skills": f.preferred,
            "min_experience_years": f.min_years,
            "candidate_skills": f.skills[:40],
            "years_experience": round(f.years, 1),
            "roles": [
                {"title_and_company": _redact(r.label, f.name), "months": r.months, "current": r.is_current}
                for r in f.timeline[:8]
            ],
            "projects": [
                {"title": _redact(str(p.get("title", ""))[:80], f.name),
                 "description": _redact(str(p.get("description", ""))[:300], f.name)}
                for p in f.projects[:5]
            ],
            "resume_excerpt": _redact(f.text[:2500], f.name),
        }

    def _enrich_with_llm(self, f: _Features, pairs: Sequence[Tuple[_BaseAgent, AgentScorecard]],
                         peers: Optional[Sequence[AgentScorecard]] = None) -> bool:
        profile = json.dumps(self._profile_for_llm(f), ensure_ascii=False)
        schema = (
            'Respond with ONLY a JSON object: {"observations": [up to 3 short strings], "strengths": [up to 3], '
            '"concerns": [up to 3], "score_adjustment": integer between -10 and 10, "rationale": "one sentence"}. '
            "Ground every statement in the profile. Do not mention or guess the candidate's gender, age, ethnicity or nationality."
        )

        def one(pair: Tuple[_BaseAgent, AgentScorecard]) -> Optional[Dict[str, Any]]:
            agent, card = pair
            local = json.dumps({"score": card.score, "summary": card.summary, "concerns": card.concerns[:4], "strengths": card.strengths[:4]})
            peer_blob = ""
            if peers:
                peer_blob = "\nReviewer comments to audit:\n" + json.dumps(
                    [{"agent": p.agent, "observations": p.observations[:4], "concerns": p.concerns[:4]} for p in peers])
            user = f"Candidate profile (redacted):\n{profile}\n\nYour local heuristic assessment:\n{local}{peer_blob}\n\n{schema}"
            return self.llm.complete_json(agent.persona_prompt, user)

        used = False
        with ThreadPoolExecutor(max_workers=max(1, len(pairs))) as pool:
            results = list(pool.map(one, pairs))
        for (agent, card), res in zip(pairs, results):
            if not res:
                continue
            used = True
            tag = f"[{self.llm.provider} insight]"
            card.observations.extend(f"{tag} {s}" for s in self._clean_strings(res.get("observations")))
            card.strengths.extend(f"{tag} {s}" for s in self._clean_strings(res.get("strengths")))
            card.concerns.extend(f"{tag} {s}" for s in self._clean_strings(res.get("concerns")))
            limit = agent.llm_score_adjust_limit
            if limit:
                adj = int(_clamp(_as_float(res.get("score_adjustment")), -limit, limit))
                if adj:
                    card.score = round(_clamp(card.score + adj), 1)
                    card.rating = _rating(card.score)
                card.metrics["llm_score_adjustment"] = adj
                rationale = str(res.get("rationale") or "").strip()
                if rationale:
                    card.metrics["llm_rationale"] = rationale[:300]
            card.source = f"local+llm:{self.llm.provider}"
        return used

    @staticmethod
    def _clean_strings(values: Any, limit: int = 3) -> List[str]:
        return [str(v).strip()[:300] for v in _as_list(values) if str(v).strip()][:limit]

    def _llm_narrative(self, f: _Features, cards: Dict[str, AgentScorecard], consensus: ExecutiveConsensus) -> Optional[str]:
        system = (
            "You are the chair of a hiring council. Write a concise executive summary (max 90 words) that explains the "
            "already-decided verdict. Do not change the verdict, and do not mention protected attributes."
        )
        user = json.dumps({
            "verdict": consensus.verdict, "score": consensus.final_score, "role": f.jd_title,
            "reasoning": consensus.reasoning,
            "scorecards": {k: {"score": c.score, "summary": c.summary} for k, c in cards.items()},
        }) + '\nRespond with ONLY JSON: {"narrative": "..."}'
        res = self.llm.complete_json(system, user)
        narrative = str(res.get("narrative", "")).strip() if res else ""
        return narrative[:800] or None


def evaluate_candidate_council(candidate_data: Dict[str, Any], jd_data: Dict[str, Any],
                               use_llm: Optional[bool] = None) -> Dict[str, Any]:
    """Convenience wrapper: build a ``RecruitmentCouncil`` and evaluate one candidate."""
    return RecruitmentCouncil(use_llm=use_llm).evaluate_candidate_council(candidate_data, jd_data)

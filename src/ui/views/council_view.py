"""
Recruiter Council & GitHub Authenticity views (Obsidian Telemetry UI)
====================================================================

* ``render_council_panel``  - verdict banner, red flags, 4-column agent scorecards, consensus reasoning,
  compensation band and an expandable (and replayable) debate transcript.
* ``render_github_widget``  - authenticity ring, exaggeration-risk meter, verified-language chips, activity stats.
* ``render_council_view``   - full tab: candidate selector + both widgets.

Everything reads the *real* output of ``RecruitmentCouncil.evaluate_candidate_council`` and
``GitHubInspector.inspect_candidate`` (keys: ``agent_scorecards``, ``debate``, ``executive_consensus``,
``language_verification``, ``resume_authenticity`` ...). Nothing here is hard-coded or mocked, except the clearly
labelled *Offline demo* mode of the GitHub widget, which feeds simulated API payloads through the same scoring code
so the viva does not depend on Wi-Fi.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import streamlit as st

from src.core.agentic_council import RecruitmentCouncil
from src.core.bias_filter import BiasFilter
from src.core.github_inspector import (GitHubClient, GitHubInspector, extract_claimed_languages,
                                       extract_github_username)
from src.ui import theme as T

AGENT_META = {
    "tech_lead": ("TECH LEAD", "Architecture · craftsmanship · repo maturity", T.ACCENT, "TL"),
    "culture_retention": ("CULTURE & RETENTION", "Tenure · progression · stability", T.ACCENT, "CR"),
    "fair_auditor": ("FAIR HIRING AUDITOR", "Bias audit · merit-only score", T.ACCENT, "FA"),
    "seniority_comp": ("SENIORITY & COMP", "Level L3-L6 · USD / INR bands", "#4f46e5", "SC"),
}
AGENT_BY_NAME = {
    "TechLeadAgent": "tech_lead", "CultureRetentionAgent": "culture_retention", "FairHiringAuditor": "fair_auditor",
    "SeniorityCompensationEstimator": "seniority_comp",
}


# --------------------------------------------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------------------------------------------
def display_name(cand: Dict[str, Any]) -> str:
    """Candidate name, masked as 'Candidate #00N' when Blind Screening mode is on."""
    if st.session_state.get("blind_mode"):
        return f"Candidate #{int(cand.get('rank', 1)):03d}"
    return str(cand.get("candidate_name") or "Candidate")


def get_council_report(cand: Dict[str, Any], jd: Dict[str, Any]) -> Dict[str, Any]:
    """Runs (and caches per candidate + JD + blind-mode + LLM-key) the multi-agent council."""
    c_data = cand.get("candidate_data", {})
    blind = bool(st.session_state.get("blind_mode"))
    key = (cand.get("file_name"), jd.get("job_title"), tuple(jd.get("required_skills", [])), jd.get("min_experience_years"),
           blind, bool(st.session_state.get("llm_api_key")))
    cache = st.session_state.setdefault("council_cache", {})
    if key not in cache:
        data = BiasFilter().anonymize_candidate(c_data, int(cand.get("rank", 1))) if blind else c_data
        api_key = st.session_state.get("llm_api_key") or None
        council = RecruitmentCouncil(use_llm=True if api_key else False, api_key=api_key)
        cache[key] = council.evaluate_candidate_council(data, jd)
    return cache[key]


# --------------------------------------------------------------------------------------------------------------
# Council panel
# --------------------------------------------------------------------------------------------------------------
def _agent_card(key: str, card: Dict[str, Any]) -> str:
    title, subtitle, color, _ = AGENT_META[key]
    score = float(card.get("score", 0))
    metrics = card.get("metrics", {})
    extra = ""
    if key == "seniority_comp":
        comp = metrics.get("compensation", {})
        usd, inr = comp.get("usd", {}), comp.get("inr", {})
        pos = comp.get("band_position_pct", 50)
        extra = (
            f'<div style="margin-top:10px"><div class="ob-eyebrow">Predicted level</div>'
            f'<div class="ob-num" style="font-size:1.35rem;color:{color}">{T.esc(comp.get("level", "?"))}'
            f'<span class="ob-sub" style="font-size:.74rem"> {T.esc(comp.get("level_title", "").split(" - ")[-1])}</span></div>'
            f'<div class="ob-band"><div class="fill"></div><div class="mk" style="left:{pos}%"></div></div>'
            f'{T.chip("$%sk-$%sk" % (int(usd.get("min", 0) / 1000), int(usd.get("max", 0) / 1000)), T.AMBER)}'
            f'{T.chip("INR %g-%g LPA" % (inr.get("min_lpa", 0), inr.get("max_lpa", 0)), T.AMBER)}</div>'
        )
    elif key == "fair_auditor":
        integrity = metrics.get("fairness_integrity_score", 100)
        flags = len(metrics.get("bias_flags", []))
        extra = (f'<div style="margin-top:10px">{T.chip(f"integrity {integrity:.0f}/100", T.EMERALD if integrity >= 80 else T.AMBER)}'
                 f'{T.chip(f"{flags} bias flag(s)", T.EMERALD if not flags else T.ROSE)}'
                 f'{T.chip("merit-only", T.CYAN)}</div>')
    elif key == "tech_lead":
        extra = (f'<div style="margin-top:10px">{T.chip("evidence %s/%s" % (metrics.get("required_skills_evidenced", 0), metrics.get("required_skills_listed", 0)), T.CYAN)}'
                 f'{T.chip("%s arch signals" % metrics.get("architecture_signals", 0), T.MUTED)}'
                 f'{T.chip("%s metrics" % metrics.get("quantified_impacts", 0), T.MUTED)}</div>')
    else:
        tenure = metrics.get("average_tenure_months")
        extra = (f'<div style="margin-top:10px">{T.chip("tenure %s mo" % (f"{tenure:.0f}" if isinstance(tenure, (int, float)) else "n/a"), T.EMERALD)}'
                 f'{T.chip("%s promo" % metrics.get("promotions_detected", 0), T.MUTED)}'
                 f'{T.chip("conf: %s" % metrics.get("confidence", "n/a"), T.MUTED)}</div>')
    strengths = "".join(f"<li>{T.esc(s)}</li>" for s in card.get("strengths", [])[:2])
    concerns = "".join(f'<li style="color:#b91c1c">{T.esc(s)}</li>' for s in card.get("concerns", [])[:2])
    lists = f"<ul>{strengths}{concerns}</ul>" if (strengths or concerns) else ""
    return T.card(f"""
        <div class="ob-agent">
          <div class="ob-between"><span class="ob-eyebrow" style="color:{color}">{T.esc(title)}</span>
            <span class="ob-chip" style="--c:{color}">{T.esc(card.get('rating', ''))}</span></div>
          <div class="ob-sub" style="margin:2px 0 8px 0">{T.esc(subtitle)}</div>
          <div class="ob-between" style="align-items:flex-end"><span class="ob-num" style="font-size:2.1rem;color:{color}">{score:.0f}<span class="ob-sub" style="font-size:.8rem">/100</span></span></div>
          {T.score_bar(score, color)}
          <div class="ob-sub" style="margin-top:10px;color:#334155">{T.esc(card.get('summary', ''))}</div>
          {extra}{lists}
        </div>""", accent=color)


def _debate_html(debate: List[Dict[str, str]], upto: Optional[int] = None, animate: bool = True) -> str:
    out = []
    for i, turn in enumerate(debate[:upto] if upto else debate):
        key = AGENT_BY_NAME.get(turn["speaker"])
        color = AGENT_META[key][2] if key else T.MUTED
        initials = AGENT_META[key][3] if key else "CH"
        stance = {"challenge": "challenges", "support": "supports", "clarify": "responds", "opening": "opens", "closing": "closes"}.get(turn.get("stance", ""), "")
        to = f" → {turn['to']}" if turn.get("to") and turn["to"] != "All" else ""
        out.append(T.bubble(f"{turn['speaker']} · {stance}{to}", turn["message"], color, delay=(i * 0.12 if animate else 0), initials=initials))
    return "".join(out)


def render_council_panel(cand: Dict[str, Any], jd: Dict[str, Any], key_prefix: str = "council") -> Optional[Dict[str, Any]]:
    """Renders the full council evaluation for one ranked candidate. Returns the raw council report."""
    try:
        report = get_council_report(cand, jd)
    except Exception as exc:  # never break the page during a demo
        st.warning(f"Council evaluation unavailable: {exc}")
        return None
    ec = report["executive_consensus"]
    cards = report["agent_scorecards"]
    meta = report["meta"]
    verdict = ec["verdict"]
    vcolor = T.VERDICT_COLORS.get(verdict, T.CYAN)
    mode_chip = T.chip("LLM-enriched · " + str(meta["mode"]), T.CYAN) if meta.get("llm_used") else T.chip("local deterministic engine · offline", T.EMERALD)
    review = T.chip("human review advised", T.AMBER) if ec["human_review_required"] else ""

    T.md(f"""
    <div class="ob-card accent" style="--acc:{vcolor}"><div class="ob-between" style="gap:22px;align-items:center">
      <div class="ob-row" style="gap:22px">{T.ring(ec['final_score'], 'council score', vcolor, 124)}
        <div><div class="ob-eyebrow">Executive consensus</div>
          <div style="margin:6px 0 8px 0">{T.verdict_tag(verdict)}</div>
          <div class="ob-title" style="max-width:520px">{T.esc(ec['headline'])}</div>
          <div style="margin-top:8px">{T.chip('confidence %.0f' % ec['confidence'], T.CYAN)}{T.chip(ec['estimated_level'])}{mode_chip}{review}</div></div></div>
      <div style="min-width:220px;text-align:right"><div class="ob-eyebrow">Red flags</div>
        <div class="ob-num" style="font-size:2.2rem;color:{T.ROSE if ec['red_flags'] else T.EMERALD}">{len(ec['red_flags'])}</div>
        <div class="ob-sub">{'detected by the council' if ec['red_flags'] else 'none detected'}</div></div>
    </div></div>""")

    if ec["red_flags"]:
        T.spacer(6)
        T.md("".join(T.flag(f["title"], f["detail"], f["severity"]) for f in ec["red_flags"]))

    T.spacer(10)
    cols = st.columns(4, gap="small")
    for col, key in zip(cols, ["tech_lead", "culture_retention", "fair_auditor", "seniority_comp"]):
        with col:
            T.md(_agent_card(key, cards[key]))

    T.spacer(10)
    left, right = st.columns([1.35, 1], gap="small")
    with left:
        bullets = "".join(f"<li>{T.esc(r)}</li>" for r in ec["reasoning"])
        T.md(f'<div class="ob-card"><div class="ob-eyebrow">Executive reasoning</div><div class="ob-agent"><ul style="font-size:.84rem;color:#334155">{bullets}</ul></div></div>')
    with right:
        focus = "".join(f"<li>{T.esc(r)}</li>" for r in ec["interview_focus"]) or "<li>No special probes needed.</li>"
        weights = "".join(T.chip(f"{k} {v:.0%}", T.MUTED) for k, v in ec["weights_used"].items())
        T.md(f'<div class="ob-card"><div class="ob-eyebrow">Interview focus</div><div class="ob-agent"><ul style="font-size:.84rem;color:#334155">{focus}</ul></div>'
             f'<div class="ob-eyebrow" style="margin-top:10px">Consensus weights</div><div>{weights}</div></div>')

    with st.expander("🎙️  Council debate transcript", expanded=False):
        debate = report["debate"]
        slot = st.empty()
        slot.markdown(_debate_html(debate), unsafe_allow_html=True)
        if st.button("▶  Replay debate live", key=f"{key_prefix}_replay_{cand.get('file_name')}"):
            for n in range(1, len(debate) + 1):
                slot.markdown(_debate_html(debate, upto=n, animate=False), unsafe_allow_html=True)
                time.sleep(0.6)
    return report


# --------------------------------------------------------------------------------------------------------------
# GitHub widget
# --------------------------------------------------------------------------------------------------------------
def _simulated_transport(claimed: List[str]) -> Callable[..., Tuple[int, Dict[str, str], str]]:
    """Fake GitHub API (clearly labelled in the UI) that exercises the real inspector end-to-end offline.

    The simulated developer really uses roughly 70% of the languages the resume claims, so the demo shows verified,
    weak and unverified chips side by side.
    """
    now = datetime.now(timezone.utc)
    iso = lambda days: (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    gh_names = {"c++": "C++", "c#": "C#", "javascript": "JavaScript", "typescript": "TypeScript", "python": "Python", "java": "Java",
                "go": "Go", "rust": "Rust", "php": "PHP", "ruby": "Ruby", "kotlin": "Kotlin", "swift": "Swift", "scala": "Scala", "r": "R"}
    usable = [c for c in claimed if c in gh_names] or ["python", "javascript"]
    real = usable[: max(1, round(len(usable) * 0.7))]
    repos = []
    for i, lang in enumerate(real * 2):
        repos.append({"name": f"{lang.replace('+', 'p').replace('#', 's')}-project-{i}", "language": gh_names[lang], "stargazers_count": 14 - i * 3 if i < 4 else 0,
                      "forks_count": 2, "pushed_at": iso(12 + i * 40), "size": 800 + i * 120, "fork": False, "description": "demo repository",
                      "license": {"spdx_id": "MIT"}, "topics": ["demo"], "html_url": "https://github.com/demo/repo", "archived": False})
    state = {"user": "sim-dev"}

    def transport(method: str, url: str, headers: Dict[str, str], body: Optional[bytes], timeout: float):
        ok = {"x-ratelimit-remaining": "4999", "x-ratelimit-reset": str(int(time.time()) + 3600)}
        if url.endswith(f"/users/{state['user']}"):
            return 200, ok, json.dumps({"login": state["user"], "html_url": f"https://github.com/{state['user']}", "created_at": iso(1500), "followers": 21, "public_repos": len(repos), "name": "Simulated Developer"})
        if "/repos?" in url and "/users/" in url:
            return 200, ok, json.dumps(repos)
        if "/events/public" in url:
            return 200, ok, json.dumps([{"type": "PushEvent", "created_at": iso(5), "repo": {"name": "sim/a"}, "payload": {"size": 4}},
                                        {"type": "PushEvent", "created_at": iso(19), "repo": {"name": "sim/b"}, "payload": {"size": 6}}])
        if "/languages" in url:
            for r in repos:
                if f"/{r['name']}/languages" in url:
                    return 200, ok, json.dumps({r["language"]: 12000 + r["size"]})
        return 404, ok, "{}"

    return transport


def _lang_chip(item: Dict[str, Any]) -> str:
    status = item["status"]
    color, mark = {"verified": (T.EMERALD, "✓"), "weak": (T.AMBER, "≈"), "unverified": (T.ROSE, "?")}[status]
    pct = f" {item['github_percent']:.0f}%" if item["github_percent"] else ""
    return T.chip(f"{mark} {item['language']}{pct}", color)


def render_github_widget(cand: Dict[str, Any], key_prefix: str = "gh") -> None:
    """GitHub authenticity ring + exaggeration meter + verified-language chips for one candidate."""
    c_data = cand.get("candidate_data", {})
    blind = bool(st.session_state.get("blind_mode"))
    username = None if blind else extract_github_username(c_data)
    claimed = extract_claimed_languages(c_data)
    uid = f"{key_prefix}_{cand.get('file_name')}"

    head_l, head_r = st.columns([2.2, 1])
    with head_l:
        who = "identity hidden (Blind Screening)" if blind else (f"@{username}" if username else "no GitHub link on resume")
        T.md(f'<div class="ob-eyebrow">GitHub &amp; portfolio authenticity</div><div class="ob-title">{T.esc(who)}</div>'
             f'<div class="ob-sub">Claimed languages: {T.esc(", ".join(claimed) or "none detected")}</div>')
    with head_r:
        options = ["Live GitHub API", "Offline demo (simulated)"]
        mode = st.radio("Data source", options, key=f"{uid}_mode", horizontal=False, label_visibility="collapsed",
                        index=0 if (username and not blind) else 1)
    run = st.button("Run authenticity inspection", key=f"{uid}_run", type="primary")

    store = st.session_state.setdefault("gh_reports", {})
    store_key = (uid, mode, username, tuple(claimed))
    if run:
        with st.spinner("Cross-referencing resume claims with public repositories…"):
            if mode.startswith("Offline"):
                client = GitHubClient(token="", transport=_simulated_transport(claimed), cache_ttl=0)
                report = GitHubInspector(client).inspect_username("sim-dev", claimed_languages=claimed,
                                                                  claimed_years=float(c_data.get("experience", {}).get("years_of_experience") or 0))
                report["simulated"] = True
            else:
                client = GitHubClient(timeout=4.0, max_retry_wait=1.0)
                report = GitHubInspector(client).inspect_candidate(c_data)
                report["simulated"] = False
        store[store_key] = report
    report = store.get(store_key)
    if report is None:
        T.md('<div class="ob-card"><div class="ob-sub">Press <b>Run authenticity inspection</b>. Live mode queries the public GitHub REST API '
             '(set <code>GITHUB_TOKEN</code> for higher limits); <b>Offline demo</b> runs the same scoring code on simulated API payloads.</div></div>')
        return

    simulated = report.get("simulated")
    banner = T.chip("SIMULATED PROFILE · demonstrates scoring logic, not real data", T.AMBER, solid=True) if simulated else ""
    status = report["status"]
    if status not in ("ok", "partial") or report.get("authenticity_score") is None:
        msg = {"no_github_found": "No GitHub profile was found on this resume.", "user_not_found": "The GitHub handle on the resume does not exist.",
               "rate_limited": "GitHub rate limit reached. Add a GITHUB_TOKEN or use the offline demo.",
               "unavailable": "GitHub could not be reached (offline?). Switch to the offline demo."}.get(status, report.get("summary", "No score available."))
        T.md(f'<div class="ob-card accent" style="--acc:{T.AMBER}">{banner}<div class="ob-between"><div>{T.ring(None, "authenticity", size=112)}</div>'
             f'<div style="flex:1;min-width:260px"><div class="ob-title">{T.esc(status.replace("_", " ").upper())}</div><div class="ob-sub" style="margin-top:6px">{T.esc(msg)}</div>'
             f'<div class="ob-sub" style="margin-top:6px">Unknown is not a negative signal: private and employer repositories are invisible to this check.</div></div></div></div>')
        return

    auth = report["resume_authenticity"]
    ver = report["language_verification"]
    langs = report["language_breakdown"][:5]
    act = report["activity"]
    repos = report["repositories"]
    lang_bars = "".join(T.labeled_bar(l["language"], l["percent"], T.CYAN) for l in langs if l["percent"] > 0)
    flags = "".join(T.flag("Flag", f, "medium") for f in report["flags"])
    positives = "".join(f'<div class="ob-flag" style="--c:{T.EMERALD}"><div><b>verified signal</b>{T.esc(p)}</div></div>' for p in report["positives"])
    days = act.get("days_since_last_activity")
    stat_chips = (T.chip(act["status"], {"active": T.EMERALD, "dormant": T.AMBER}.get(act["status"], T.ROSE))
                  + T.chip(f"{act['estimated_commits_90d']} commits / 90d", T.CYAN)
                  + T.chip(f"last push {days}d ago" if days is not None else "no activity", T.MUTED)
                  + T.chip(f"{repos['original']} original repos", T.MUTED) + T.chip(f"★ {repos['total_stars']}", T.MUTED)
                  + T.chip(f"forks {repos['total_forks_received']}", T.MUTED))
    T.md(f"""
    <div class="ob-card accent" style="--acc:{T.score_color(report['authenticity_score'])}">{banner}
      <div class="ob-row" style="gap:26px;align-items:flex-start;margin-top:6px">
        <div style="min-width:140px">{T.ring(report['authenticity_score'], 'authenticity score', size=140)}
          <div style="text-align:center;margin-top:6px">{T.chip(report['verdict'].replace('_', ' '), T.score_color(report['authenticity_score']))}</div>
          <div class="ob-sub" style="text-align:center;margin-top:4px">confidence {report['confidence']:.0f}%</div></div>
        <div style="flex:1;min-width:260px">{T.risk_meter(auth['exaggeration_risk'])}
          <div class="ob-eyebrow" style="margin-top:12px">Resume claims vs public code</div><div style="margin-top:4px">{''.join(_lang_chip(v) for v in ver) or T.chip('no language claims to check')}</div>
          <div style="margin-top:10px">{stat_chips}</div></div>
        <div style="flex:1;min-width:220px"><div class="ob-eyebrow">Top languages by bytes</div>{lang_bars or '<div class="ob-sub">No language data.</div>'}</div>
      </div>
      <div class="ob-sub" style="margin-top:12px;color:#334155">{T.esc(report['summary'])}</div>
      <div style="margin-top:8px">{positives}{flags}</div>
      <div class="ob-sub" style="margin-top:8px;font-size:.72rem">{T.esc(report['caveat'])}</div>
    </div>""")


# --------------------------------------------------------------------------------------------------------------
# Full tab
# --------------------------------------------------------------------------------------------------------------
def select_candidate(ranked: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    """Candidate dropdown that stays in sync with the Command Center's 'Inspect' buttons."""
    if not ranked:
        return None
    labels = [f"#{c['rank']}  {display_name(c)}  ·  {c['overall_score']}%" for c in ranked]
    current = st.session_state.get("selected_candidate")
    default = 0
    if current:
        for i, c in enumerate(ranked):
            if c.get("file_name") == current.get("file_name"):
                default = i
                break
    choice = st.selectbox("Candidate", labels, index=default, key=key, label_visibility="collapsed")
    cand = ranked[labels.index(choice)]
    st.session_state["selected_candidate"] = cand
    return cand


def render_council_view(ranked: List[Dict[str, Any]], jd: Dict[str, Any]) -> None:
    T.md('<div class="ob-eyebrow">Autonomous multi-agent council</div>'
         '<div style="font-size:1.5rem;font-weight:800;letter-spacing:-.02em;margin-bottom:4px">Four specialists review. One consensus.</div>'
         '<div class="ob-sub" style="margin-bottom:10px">Tech Lead · Culture &amp; Retention · Fair Hiring Auditor · Seniority &amp; Compensation, with a cross-examination debate and an auditable verdict.</div>')
    if not ranked:
        st.info("No candidates screened yet. Add resumes in the Job & Upload tab.")
        return
    cand = select_candidate(ranked, "council_tab_select")
    if cand is None:
        return
    render_council_panel(cand, jd, key_prefix="tab")
    T.spacer(18)
    render_github_widget(cand, key_prefix="tabgh")

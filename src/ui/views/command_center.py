"""
Executive Command Center (Obsidian Telemetry UI)
================================================

Telemetry strip (live candidate count, model-status pill, active role banner), a floating glass RAG search bar with
instant prompt pills, and ranked candidate cards with animated score bars and council verdict tags.

All numbers come from the real pipeline: ``ranked_candidates`` (HybridRanker), ``TalentRAG`` and
``RecruitmentCouncil``. Blind Screening masks names and identifiers everywhere in this view.
"""

from __future__ import annotations

import socket
from typing import Any, Dict, List

import streamlit as st

from src.ui import theme as T
from src.ui.views.council_view import display_name, get_council_report

PROMPT_PILLS = [
    "Engineers with 2+ years in Python and PyTorch",
    "Backend developers who deployed with Docker and AWS",
    "Candidates with measurable latency or throughput results",
    "Who has NLP or transformer experience?",
]


def _embedding_status() -> Dict[str, str]:
    """Reports which semantic backend is active (MiniLM if installed, otherwise TF-IDF cosine)."""
    try:
        import importlib.util
        if importlib.util.find_spec("sentence_transformers") is not None:
            return {"label": "MiniLM dense + BM25", "color": T.EMERALD, "mode": "neural"}
    except Exception:
        pass
    return {"label": "TF-IDF + BM25 (offline)", "color": T.CYAN, "mode": "offline"}


@st.cache_data(ttl=20, show_spinner=False)
def _api_online(host: str = "127.0.0.1", port: int = 8000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def _skill_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("required_skill") or item.get("skill") or item.get("name") or "")
    return str(item)


def _rag_pool(ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pool = []
    for c in ranked:
        cd = dict(c.get("candidate_data", {}))
        cd["candidate_name"] = c.get("candidate_name", "Candidate")
        pool.append(cd)
    return pool


def _telemetry(ranked: List[Dict[str, Any]], jd: Dict[str, Any]) -> None:
    status = _embedding_status()
    llm_on = bool(st.session_state.get("llm_api_key"))
    api_up = _api_online()
    top = ranked[0] if ranked else None
    avg = round(sum(c["overall_score"] for c in ranked) / len(ranked), 1) if ranked else 0
    c1, c2, c3, c4 = st.columns([1, 1, 1.25, 1.6])
    with c1:
        T.md(T.telemetry_card("Candidates screened", len(ranked), f"avg match {avg}%", T.CYAN))
    with c2:
        T.md(T.telemetry_card("Top match", f"{top['overall_score']}%" if top else "-", display_name(top) if top else "no data",
                              T.EMERALD))
    with c3:
        pills = (T.pill(f"Engine · {status['label']}", status["color"], pulse=True)
                 + "<div style='height:6px'></div>"
                 + T.pill("LLM narrative on" if llm_on else "Local council · offline", T.CYAN if llm_on else T.MUTED)
                 + "<div style='height:6px'></div>"
                 + T.pill("API :8000 online" if api_up else "API :8000 idle", T.EMERALD if api_up else T.AMBER))
        T.md(T.card(f'<div class="ob-eyebrow">Model status</div><div style="margin-top:8px">{pills}</div>', T.EMERALD))
    with c4:
        skills = jd.get("required_skills", [])
        T.md(T.card(
            f'<div class="ob-eyebrow">Active role</div>'
            f'<div style="font-size:1.15rem;font-weight:800;letter-spacing:-.01em;margin:4px 0 6px">{T.esc(jd.get("job_title", "Role"))}</div>'
            f'<div class="ob-sub">min {T.esc(jd.get("min_experience_years", 0))} yrs · {len(skills)} required skills</div>'
            f'<div style="margin-top:6px">{T.chips(skills, T.CYAN, limit=5)}</div>', T.AMBER))


def _search(ranked: List[Dict[str, Any]]) -> None:
    from src.core.talent_rag import get_default_engine
    T.md('<div class="ob-eyebrow" style="margin:6px 0 6px">Ask the talent pool</div>')
    if "cc_query" not in st.session_state:
        st.session_state["cc_query"] = ""
    pill_cols = st.columns(len(PROMPT_PILLS))
    for i, (col, text) in enumerate(zip(pill_cols, PROMPT_PILLS)):
        with col:
            if st.button(text, key=f"cc_pill_{i}", use_container_width=True):
                st.session_state["cc_query"] = text
    query = st.text_input("Search", key="cc_query", label_visibility="collapsed",
                          placeholder="Describe who you need, e.g. engineers with 3+ years in distributed systems who used Docker")
    if not query.strip():
        return
    try:
        hits = get_default_engine().search_talent_pool(query.strip(), _rag_pool(ranked), top_k=4)
    except Exception as exc:  # never break the dashboard on a search error
        st.warning(f"Search unavailable: {exc}")
        return
    if not hits:
        st.info("No candidate closely matches this query.")
        return
    backend = hits[0].get("retrieval", {}).get("dense_backend", "")
    T.md(f'<div class="ob-sub" style="margin:8px 0">{len(hits)} matches · retrieval: {T.esc(backend)} + BM25</div>')
    by_name = {c.get("candidate_name"): c for c in ranked}
    for h in hits:
        orig = by_name.get(h.get("candidate_name"), {})
        name = display_name(orig) if orig else h.get("candidate_name")
        matched = [m.get("competency", m.get("name", "")) if isinstance(m, dict) else str(m)
                   for m in h.get("matched_competencies", [])]
        snippet = ""
        if h.get("snippets"):
            snippet = f'<div class="ob-snippet">{h["snippets"][0].get("html") or T.esc(h["snippets"][0].get("text", ""))}</div>'
        T.md(T.card(
            f'<div class="ob-between"><b>#{h.get("rank")} {T.esc(name)}</b>'
            f'<span class="ob-chip solid" style="--c:{T.score_color(h.get("relevance_score", 0))}">relevance {h.get("relevance_score", 0):.0f}%</span></div>'
            f'<div style="margin:6px 0">{T.chips(matched, T.EMERALD, limit=6)}</div>{snippet}'))


def _ranked_cards(ranked: List[Dict[str, Any]], jd: Dict[str, Any]) -> None:
    T.md('<div class="ob-eyebrow" style="margin:18px 0 6px">Leaderboard</div>')
    for cand in ranked:
        report = get_council_report(cand, jd)
        cons = report.get("executive_consensus", {})
        verdict = cons.get("verdict", "")
        gap = cand.get("gap_results", {})
        score = float(cand.get("overall_score", 0))
        flags = cons.get("red_flags", [])
        flag_chip = T.chip(f"{len(flags)} red flag{'s' if len(flags) != 1 else ''}", T.ROSE if flags else T.EMERALD)
        col_card, col_btn = st.columns([6, 1])
        with col_card:
            T.md(T.card(
                f'<div class="ob-between"><div style="display:flex;gap:12px;align-items:center">'
                f'<span class="ob-num" style="font-size:1.3rem;color:{T.score_color(score)}">#{cand.get("rank")}</span>'
                f'<div><b style="font-size:1.02rem">{T.esc(display_name(cand))}</b>'
                f'<div class="ob-sub">{T.esc(cand.get("file_name", "")) if not st.session_state.get("blind_mode") else "identity hidden"}</div></div></div>'
                f'<div style="display:flex;gap:8px;align-items:center">{T.verdict_tag(verdict)}'
                f'<span class="ob-num" style="font-size:1.25rem;color:{T.score_color(score)}">{score:.1f}%</span></div></div>'
                f'{T.score_bar(score)}'
                f'<div style="margin-top:8px">{T.chips([_skill_name(x) for x in gap.get("matched_skills", [])], T.EMERALD, limit=6)}'
                f'{T.chips([_skill_name(x) for x in gap.get("partially_matched_skills", [])], T.AMBER, limit=3)}'
                f'{T.chips([_skill_name(x) for x in gap.get("missing_skills", [])], T.ROSE, limit=3)} {flag_chip}</div>',
                T.score_color(score)))
        with col_btn:
            T.spacer(18)
            if st.button("Inspect", key=f"cc_inspect_{cand.get('file_name')}", use_container_width=True):
                st.session_state["selected_candidate"] = cand
                st.toast(f"Selected {display_name(cand)}. Open the Council or Deep-Dive tab.")


def render_command_center(ranked: List[Dict[str, Any]], jd: Dict[str, Any]) -> None:
    head, tog = st.columns([5, 2])
    with head:
        T.md('<div class="ob-eyebrow">Executive command telemetry</div>'
             '<div style="font-size:1.7rem;font-weight:800;letter-spacing:-.025em">Recruitment Command Center</div>')
    with tog:
        T.spacer(10)
        st.toggle("Blind screening", key="blind_mode",
                  help="Names and contact details are masked in the UI and before the council sees the resume.")
    _telemetry(ranked, jd)
    T.spacer(6)
    if not ranked:
        st.info("No candidates yet. Add resumes in the Job & Upload tab, then re-rank.")
        return
    _search(ranked)
    _ranked_cards(ranked, jd)

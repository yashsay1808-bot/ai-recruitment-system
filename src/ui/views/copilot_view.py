"""
Recruiter Talent Copilot (Obsidian Telemetry UI)
================================================

Right-rail chat with quick-prompt chips, a council-backed salary estimator and one-click Markdown export.
Chat answers come from the existing ``RecruiterChatbot``; the estimator reads the real
``SeniorityCompensationEstimator`` output of the council.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from src.core.recruiter_chatbot import RecruiterChatbot
from src.ui import theme as T
from src.ui.views.council_view import display_name, get_council_report

QUICK_PROMPTS = [
    "Who is the best candidate and why?",
    "Which candidates have red flags or risks?",
    "Compare the top 2 candidates",
    "What skills are missing across the pool?",
]


def _history() -> List[Dict[str, str]]:
    return st.session_state.setdefault("copilot_messages", [])


def _ask(chatbot: RecruiterChatbot, text: str, ranked, jd) -> None:
    hist = _history()
    hist.append({"role": "user", "content": text})
    try:
        answer = chatbot.answer_query(text, ranked, jd, db=None)
    except Exception as exc:
        answer = f"I could not answer that: {exc}"
    hist.append({"role": "assistant", "content": answer})


def _export_markdown(ranked, jd) -> str:
    lines = [f"# Recruiter Copilot Session - {jd.get('job_title', 'Role')}",
             f"_Exported {datetime.now():%Y-%m-%d %H:%M}_", "", "## Leaderboard", ""]
    for c in ranked:
        cons = get_council_report(c, jd).get("executive_consensus", {})
        lines.append(f"{c['rank']}. **{display_name(c)}** - {c['overall_score']}% - council: {cons.get('verdict', 'n/a')}")
    lines += ["", "## Conversation", ""]
    for m in _history():
        who = "Recruiter" if m["role"] == "user" else "Copilot"
        lines += [f"**{who}:**", "", m["content"], ""]
    return "\n".join(lines)


def _salary_estimator(ranked, jd) -> None:
    T.md('<div class="ob-eyebrow" style="margin-top:14px">Salary estimator</div>')
    labels = [f"#{c['rank']} {display_name(c)}" for c in ranked]
    choice = st.selectbox("Candidate", labels, key="copilot_salary_pick", label_visibility="collapsed")
    cand = ranked[labels.index(choice)]
    comp = get_council_report(cand, jd)["executive_consensus"].get("compensation") or {}
    inr = comp.get("inr", {})
    if not inr:
        st.caption("No compensation estimate available.")
        return
    T.md(T.card(
        f'<div class="ob-between"><b>{T.esc(comp.get("level_title", comp.get("level", "")))}</b>'
        f'<span class="ob-chip solid" style="--c:{T.CYAN}">target {T.esc(comp.get("jd_target_level", ""))}</span></div>'
        f'<div class="ob-num" style="font-size:1.25rem;margin-top:8px;color:{T.AMBER}">INR {inr["min_lpa"]:g} - {inr["max_lpa"]:g} LPA</div>'
        f'<div class="ob-sub">suggested {inr["suggested_target_lpa"]:g} LPA · band position {comp.get("band_position_pct", 0)}%</div>'
        f'<div class="ob-sub" style="margin-top:8px;font-size:.68rem">{T.esc(comp.get("disclaimer", ""))}</div>', T.EMERALD))


def render_copilot_panel(ranked: List[Dict[str, Any]], jd: Dict[str, Any], chatbot: RecruiterChatbot) -> None:
    T.md('<div class="ob-eyebrow">Talent copilot</div>'
         '<div style="font-size:1.3rem;font-weight:800;letter-spacing:-.02em;margin-bottom:6px">Ask anything about the pool</div>')
    if not ranked:
        st.info("Screen some resumes first.")
        return
    cols = st.columns(2)
    for i, text in enumerate(QUICK_PROMPTS):
        with cols[i % 2]:
            if st.button(text, key=f"cp_quick_{i}", use_container_width=True):
                _ask(chatbot, text, ranked, jd)
    hist = _history()
    if not hist:
        hist.append({"role": "assistant", "content":
                     f"I have reviewed {len(ranked)} candidates for {jd.get('job_title', 'this role')}. Pick a prompt or type a question."})
    box = st.container(height=420, border=False)
    with box:
        for m in hist:
            if m["role"] == "user":
                st.markdown(f'<div class="ob-bubble user" style="--c:{T.CYAN}"><div class="ob-avatar">YO</div>'
                            f'<div class="body"><div class="who">You</div>{T.esc(m["content"])}</div></div>', unsafe_allow_html=True)
            else:
                with st.chat_message("assistant"):
                    st.markdown(m["content"])
    with st.form("copilot_form", clear_on_submit=True):
        q = st.text_input("Message", label_visibility="collapsed", placeholder="Ask the copilot...")
        sent = st.form_submit_button("Send", use_container_width=True)
    if sent and q.strip():
        _ask(chatbot, q.strip(), ranked, jd)
        st.rerun()
    _salary_estimator(ranked, jd)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Export Markdown", _export_markdown(ranked, jd), file_name="copilot_session.md",
                           mime="text/markdown", use_container_width=True)
    with c2:
        if st.button("Clear chat", key="cp_clear", use_container_width=True):
            st.session_state["copilot_messages"] = []
            st.rerun()

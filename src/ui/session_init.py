"""
Shared Session Initializer & Sidebar Utility for Multi-Page Architecture
Ensures state consistency, authentication checks, and core model initialization
across all standalone page modules.
"""

import html
import streamlit as st

from src.core.resume_parser import ResumeParser
from src.core.jd_parser import JDParser
from src.core.hybrid_ranker import HybridRanker
from src.core.explainable_ai import ExplainableAI
from src.core.interview_generator import InterviewQuestionGenerator
from src.core.quality_analyzer import ResumeQualityAnalyzer
from src.core.database import RecruitmentDatabase
from src.ui.components import inject_custom_css
from src.ui.theme import inject_obsidian_theme
from src.ui.views.login_view import render_recruiter_login_view
from src.ui.views.job_management import SAMPLE_JOB_TEMPLATES


def ensure_initialized():
    """Initializes global ATS session states and loads default models."""
    inject_custom_css()
    inject_obsidian_theme()

    if "db" not in st.session_state:
        st.session_state["db"] = RecruitmentDatabase()
    if "resume_parser" not in st.session_state:
        st.session_state["resume_parser"] = ResumeParser()
    if "jd_parser" not in st.session_state:
        st.session_state["jd_parser"] = JDParser()
    if "hybrid_ranker" not in st.session_state:
        st.session_state["hybrid_ranker"] = HybridRanker()
    if "xai_engine" not in st.session_state:
        st.session_state["xai_engine"] = ExplainableAI()
    if "q_generator" not in st.session_state:
        st.session_state["q_generator"] = InterviewQuestionGenerator()
    if "quality_analyzer" not in st.session_state:
        st.session_state["quality_analyzer"] = ResumeQualityAnalyzer()

    # Authentication state: unauthenticated until a real sign-in succeeds
    if "authenticated_recruiter" not in st.session_state:
        st.session_state["authenticated_recruiter"] = None

    # Candidate data states
    if "parsed_candidates" not in st.session_state:
        st.session_state["parsed_candidates"] = []
    if "current_jd" not in st.session_state:
        default_tpl = SAMPLE_JOB_TEMPLATES["Machine Learning Engineer"]
        st.session_state["current_jd"] = st.session_state["jd_parser"].parse(
            default_tpl["text"], 
            title_hint="Machine Learning Engineer"
        )
        st.session_state["current_jd"]["min_experience_years"] = default_tpl["min_experience"]

    if "ranked_candidates" not in st.session_state:
        st.session_state["ranked_candidates"] = []

    if "weights" not in st.session_state:
        st.session_state["weights"] = HybridRanker.DEFAULT_WEIGHTS
    if "selected_candidate" not in st.session_state:
        st.session_state["selected_candidate"] = None


def check_authentication() -> bool:
    """
    Gate for every page. Returns True only for a signed-in recruiter; otherwise renders
    the sign-in card (and nothing else) and returns False so the caller stops rendering.
    """
    ensure_initialized()
    if st.session_state.get("authenticated_recruiter") is None:
        render_recruiter_login_view(st.session_state["db"])
        return False

    # First authenticated render: screen the default candidate pool once.
    if not st.session_state.get("ranked_candidates"):
        try:
            from src.ui.pipeline import process_and_rank_resumes
            process_and_rank_resumes()
        except Exception:
            pass
        ranked = st.session_state.get("ranked_candidates") or []
        if ranked and not st.session_state.get("selected_candidate"):
            st.session_state["selected_candidate"] = ranked[0]
    return True


def _initials(name: str) -> str:
    parts = [p for p in (name or "").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "R"


def render_account_block() -> None:
    """Quiet account footer for the sidebar: avatar, name, company and a Sign out button."""
    recruiter = st.session_state.get("authenticated_recruiter")
    if not recruiter:
        return
    name = html.escape(recruiter.get("name", "Recruiter"))
    sub = html.escape(recruiter.get("company") or recruiter.get("email", ""))
    st.markdown(
        f'<div class="acct"><div class="acct-avatar">{html.escape(_initials(recruiter.get("name", "")))}</div>'
        f'<div><div class="acct-name">{name}</div><div class="acct-sub">{sub}</div></div></div>',
        unsafe_allow_html=True,
    )
    if st.button("Sign out", key="signout_btn", use_container_width=True):
        for key in ("authenticated_recruiter", "ranked_candidates", "parsed_candidates", "selected_candidate", "auth_mode"):
            st.session_state.pop(key, None)
        st.rerun()


def render_shared_sidebar():
    """Persistent sidebar for the multi-page app: account, active role, re-rank, optional AI key."""
    if not st.session_state.get("authenticated_recruiter"):
        return

    with st.sidebar:
        render_account_block()

        st.divider()
        c_jd = st.session_state.get("current_jd", {})
        st.caption("Active role")
        st.markdown(f"**{c_jd.get('job_title', 'Role')}**")
        st.caption(f"{c_jd.get('min_experience_years', 0)} yrs min · {len(c_jd.get('required_skills', []))} required skills")

        if st.button("Re-rank candidates", type="primary", use_container_width=True, key="shared_rerank_btn"):
            from src.ui.pipeline import process_and_rank_resumes
            with st.spinner("Screening candidates..."):
                process_and_rank_resumes()
            st.rerun()

        with st.expander("Generative AI key (optional)", expanded=False):
            api_key = st.text_input("API key", type="password", value=st.session_state.get("llm_api_key", ""), key="shared_llm_key")
            if api_key:
                st.session_state["llm_api_key"] = api_key

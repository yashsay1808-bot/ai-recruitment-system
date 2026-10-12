"""
Shared Session Initializer & Sidebar Utility for Multi-Page Architecture
Ensures state consistency, authentication checks, and core model initialization
across all standalone page modules.
"""

import os
import glob
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

    # Authentication state (Pre-authorized in Demo Mode so pages are immediately accessible)
    if "authenticated_recruiter" not in st.session_state or st.session_state["authenticated_recruiter"] is None:
        st.session_state["authenticated_recruiter"] = {
            "id": 1,
            "name": "Yashashwini",
            "email": "recruiter@techcorp.com",
            "role": "Lead Technical Recruiter",
            "company": "TechCorp Global Technologies",
            "clearance_level": 2,
            "session_token": "AUTH-SEC-DEMO-2026"
        }

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

    if "ranked_candidates" not in st.session_state or not st.session_state["ranked_candidates"]:
        st.session_state["ranked_candidates"] = []
        try:
            from app import process_and_rank_resumes
            process_and_rank_resumes()
        except Exception:
            pass

    if "weights" not in st.session_state:
        st.session_state["weights"] = HybridRanker.DEFAULT_WEIGHTS
    if "selected_candidate" not in st.session_state:
        st.session_state["selected_candidate"] = st.session_state["ranked_candidates"][0] if st.session_state.get("ranked_candidates") else None


def check_authentication():
    """Verifies recruiter authentication. Returns True if logged in, False otherwise."""
    ensure_initialized()
    recruiter = st.session_state.get("authenticated_recruiter")
    if recruiter is None:
        db: RecruitmentDatabase = st.session_state["db"]
        render_recruiter_login_view(db)
        return False
    return True


def render_shared_sidebar():
    """Renders persistent recruiter profile, active role info, and action triggers."""
    recruiter = st.session_state.get("authenticated_recruiter")
    if not recruiter:
        return

    with st.sidebar:
        clearance = recruiter.get("clearance_level", 2)
        token = recruiter.get("session_token", "AUTH-SEC-2026")
        
        st.markdown(f"""
        <div style="background: #1e293b; border: 1px solid #38bdf8; border-radius: 8px; padding: 10px; margin-bottom: 12px;">
            <div style="color: #38bdf8; font-size: 0.75rem; font-weight: 700;">🛡️ AUTHORIZED RECRUITER ACTIVE</div>
            <div style="color: #f8fafc; font-size: 1.1rem; font-weight: 700; margin-top: 2px;">{recruiter.get('name', 'Recruiter')}</div>
            <div style="color: #94a3b8; font-size: 0.82rem;">{recruiter.get('role', 'Talent Acquisition')}</div>
            <div style="color: #64748b; font-size: 0.75rem; margin-top: 4px;">🏢 {recruiter.get('company', 'Enterprise')}</div>
            <div style="margin-top: 6px; font-size: 0.72rem; color: #a5b4fc; background: #312e81; padding: 2px 6px; border-radius: 4px; display: inline-block;">
                Clearance: Level {clearance} | Token: {token[:16]}...
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Terminate Session & Sign Out", type="secondary", use_container_width=True, key="shared_signout_btn"):
            st.session_state["authenticated_recruiter"] = None
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 Active Job Role")
        c_jd = st.session_state.get("current_jd", {})
        st.markdown(f"💼 **{c_jd.get('job_title', 'Role')}**")
        st.caption(f"Min Exp: `{c_jd.get('min_experience_years', 0)} yrs` | Skills: `{len(c_jd.get('required_skills', []))} required`")

        st.markdown("---")
        if st.button("🚀 Re-Rank Candidate Pool", type="primary", use_container_width=True, key="shared_rerank_btn"):
            from app import process_and_rank_resumes
            with st.spinner("Processing resumes & evaluating multi-score criteria..."):
                process_and_rank_resumes()
            st.success(f"Screened {len(st.session_state['ranked_candidates'])} candidates!")
            st.rerun()

        st.markdown("---")
        with st.expander("🔑 Optional Generative AI Integration", expanded=False):
            st.caption("Enter Gemini or OpenAI API key for live interview questions:")
            api_key = st.text_input("API Key", type="password", value=st.session_state.get("llm_api_key", ""), key="shared_llm_key")
            if api_key:
                st.session_state["llm_api_key"] = api_key
                st.success("API Key saved.")

"""
AI-Powered Intelligent Recruitment System (Phase 2 ATS)
Main Streamlit Application Entrypoint
Integrates:
- Dedicated Recruiter Authentication & Registration Portal
- Advanced Multi-Format Resume Parser & OCR
- Skill Synonym & Ontology Knowledge Base
- Hybrid AI Multi-Score Ranking Engine
- Explainable AI (XAI) & Recommendation Engine
- Skill Gap Analysis
- Multi-Candidate Comparison Matrix
- AI-Powered Interview Question Generator
- ATS Resume Quality Analyzer & Suggestions
- Fair & Bias-Aware Blind Screening Mode
- Recruiter Analytics Dashboard & SQLite Screening History
"""

import os
import glob
import streamlit as st

# Set Streamlit Page Configuration (Must be first Streamlit command)
st.set_page_config(
    page_title="AI-Powered Intelligent Recruitment System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.core.resume_parser import ResumeParser
from src.core.jd_parser import JDParser
from src.core.hybrid_ranker import HybridRanker
from src.core.explainable_ai import ExplainableAI
from src.core.interview_generator import InterviewQuestionGenerator
from src.core.quality_analyzer import ResumeQualityAnalyzer
from src.core.recruiter_chatbot import RecruiterChatbot
from src.core.database import RecruitmentDatabase
from src.ui.pipeline import process_and_rank_resumes
from src.ui.session_init import render_account_block
from src.ui.components import inject_custom_css
from src.ui.theme import inject_obsidian_theme
from src.ui.views.command_center import render_command_center
from src.ui.views.council_view import render_council_view
from src.ui.views.copilot_view import render_copilot_panel
from src.ui.views.login_view import render_recruiter_login_view
from src.ui.views.job_management import render_job_management_view, SAMPLE_JOB_TEMPLATES
from src.ui.views.screening_results import render_screening_results_view
from src.ui.views.candidate_details import render_candidate_details_view
from src.ui.views.candidate_comparison import render_candidate_comparison_view
from src.ui.views.interview_assistant import render_interview_assistant_view
from src.ui.views.analytics_dashboard import render_analytics_dashboard_view
from src.ui.views.chatbot_view import render_chatbot_view


def initialize_session_state():
    """Initializes Streamlit session variables."""
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

    # Authentication state
    if "authenticated_recruiter" not in st.session_state:
        st.session_state["authenticated_recruiter"] = None

    # Data states
    if "parsed_candidates" not in st.session_state:
        st.session_state["parsed_candidates"] = []
    if "ranked_candidates" not in st.session_state:
        st.session_state["ranked_candidates"] = []
    if "current_jd" not in st.session_state:
        # Default to Machine Learning Engineer
        default_tpl = SAMPLE_JOB_TEMPLATES["Machine Learning Engineer"]
        st.session_state["current_jd"] = st.session_state["jd_parser"].parse(
            default_tpl["text"], 
            title_hint="Machine Learning Engineer"
        )
        st.session_state["current_jd"]["min_experience_years"] = default_tpl["min_experience"]

    if "weights" not in st.session_state:
        st.session_state["weights"] = HybridRanker.DEFAULT_WEIGHTS
    if "selected_candidate" not in st.session_state:
        st.session_state["selected_candidate"] = None
    if "active_tab_index" not in st.session_state:
        st.session_state["active_tab_index"] = 0


def main():
    initialize_session_state()
    inject_custom_css()
    inject_obsidian_theme()

    db: RecruitmentDatabase = st.session_state["db"]
    jd_parser: JDParser = st.session_state["jd_parser"]
    q_gen: InterviewQuestionGenerator = st.session_state["q_generator"]

    # ------------------ Recruiter Authentication Gate ------------------
    recruiter = st.session_state.get("authenticated_recruiter")
    if recruiter is None:
        render_recruiter_login_view(db)
        return

    # ------------------ Sidebar (account, active role, actions) ------------------
    with st.sidebar:
        render_account_block()

        st.divider()
        c_jd = st.session_state.get("current_jd", {})
        st.caption("Active role")
        st.markdown(f"**{c_jd.get('job_title', 'Role')}**")
        st.caption(f"{c_jd.get('min_experience_years', 0)} yrs min · {len(c_jd.get('required_skills', []))} required skills")

        if st.button("Run screening", type="primary", use_container_width=True):
            with st.spinner("Screening candidates..."):
                process_and_rank_resumes()
            st.rerun()

        with st.expander("Generative AI key (optional)", expanded=False):
            api_key = st.text_input("API key", type="password", value=st.session_state.get("llm_api_key", ""))
            if api_key:
                st.session_state["llm_api_key"] = api_key

    # Automatically run initial screening if not already screened
    if not st.session_state.get("ranked_candidates"):
        process_and_rank_resumes()

    # ------------------ Top Navigation Tabs ------------------
    ranked = st.session_state.get("ranked_candidates", [])
    jd = st.session_state.get("current_jd", {})
    if "chatbot_engine" not in st.session_state:
        st.session_state["chatbot_engine"] = RecruiterChatbot()

    t_cmd, t_job, t_council, t_deep, t_cmp, t_int, t_ana, t_cop = st.tabs([
        "Command Center", "Job & Upload", "Council & GitHub", "Deep-Dive & XAI",
        "Comparison", "Interview Assistant", "Analytics", "Copilot"
    ])

    with t_cmd:
        main_col, rail = st.columns([2.6, 1.15], gap="large")
        with main_col:
            render_command_center(ranked, jd)
        with rail:
            render_copilot_panel(ranked, jd, st.session_state["chatbot_engine"])

    with t_job:
        render_job_management_view(db, jd_parser)

    with t_council:
        render_council_view(ranked, jd)

    with t_deep:
        render_candidate_details_view(st.session_state.get("selected_candidate"), jd)

    with t_cmp:
        render_candidate_comparison_view(ranked, jd)

    with t_int:
        render_interview_assistant_view(ranked, jd, q_gen)

    with t_ana:
        render_analytics_dashboard_view(ranked, jd, db)

    with t_cop:
        render_chatbot_view(ranked_candidates=ranked, current_jd=jd, chatbot=st.session_state["chatbot_engine"])


if __name__ == "__main__":
    main()

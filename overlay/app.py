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


def process_and_rank_resumes():
    """Parses, evaluates, and ranks all active candidate resumes against the current JD."""
    resume_parser: ResumeParser = st.session_state["resume_parser"]
    hybrid_ranker: HybridRanker = st.session_state["hybrid_ranker"]
    xai_engine: ExplainableAI = st.session_state["xai_engine"]
    qa_engine: ResumeQualityAnalyzer = st.session_state["quality_analyzer"]
    current_jd = st.session_state["current_jd"]
    weights = st.session_state.get("weights", HybridRanker.DEFAULT_WEIGHTS)

    hybrid_ranker.weights = weights

    raw_candidates = []

    # 1. Check if user uploaded files
    uploaded_files = st.session_state.get("uploaded_raw_files", [])
    if uploaded_files:
        for f in uploaded_files:
            file_bytes = f.read()
            f.seek(0)
            parsed = resume_parser.parse(file_bytes, f.name)
            raw_candidates.append(parsed)

    # 2. Check if sample resumes are loaded
    if st.session_state.get("load_sample_resumes", False) or (not raw_candidates and not uploaded_files):
        sample_files = glob.glob("data/sample_resumes/*.*")
        for s_path in sample_files:
            fname = os.path.basename(s_path)
            with open(s_path, "rb") as fp:
                b = fp.read()
                parsed = resume_parser.parse(b, fname)
                raw_candidates.append(parsed)
        st.session_state["load_sample_resumes"] = False

    st.session_state["parsed_candidates"] = raw_candidates

    # 3. Compute Quality Scores
    quality_scores = {}
    for cand in raw_candidates:
        q_res = qa_engine.analyze(cand, current_jd.get("required_skills", []))
        quality_scores[cand["file_name"]] = q_res["quality_score"]

    # 4. Rank Candidates
    ranked = hybrid_ranker.rank_all_candidates(raw_candidates, current_jd, quality_scores)

    # 5. Enrich with Explainable AI (XAI)
    for cand in ranked:
        cand["explanation"] = xai_engine.generate_explanation(cand, current_jd)

    st.session_state["ranked_candidates"] = ranked
    if ranked:
        st.session_state["selected_candidate"] = ranked[0]


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

    # ------------------ Authenticated Recruiter Sidebar ------------------
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

        if st.button("🚪 Terminate Session & Sign Out", type="secondary", use_container_width=True):
            st.session_state["authenticated_recruiter"] = None
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 Active Role")
        c_jd = st.session_state.get("current_jd", {})
        st.markdown(f"💼 **{c_jd.get('job_title', 'Role')}**")
        st.caption(f"Min Exp: `{c_jd.get('min_experience_years', 0)} yrs` | Skills: `{len(c_jd.get('required_skills', []))} required`")

        st.markdown("---")
        if st.button("🚀 Run Screening & Rank Candidates", type="primary", use_container_width=True):
            with st.spinner("Executing multi-format parsing, synonym expansion, and hybrid scoring..."):
                process_and_rank_resumes()
            st.success(f"Screened {len(st.session_state['ranked_candidates'])} candidates!")
            st.rerun()

        st.markdown("---")
        with st.expander("🔑 Optional Generative AI Integration", expanded=False):
            st.caption("Enter Gemini or OpenAI API key for real-time generative interview question crafting:")
            api_key = st.text_input("API Key", type="password", value=st.session_state.get("llm_api_key", ""))
            if api_key:
                st.session_state["llm_api_key"] = api_key
                st.success("API Key saved.")

        st.markdown("---")
        st.markdown("<div style='font-size: 0.8rem; color: #94a3b8;'>✓ 100% Offline Capable<br>✓ Multi-Format & OCR Support<br>✓ Bias-Aware Blind Screening<br>✓ Explainable AI (XAI) Ranking</div>", unsafe_allow_html=True)

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

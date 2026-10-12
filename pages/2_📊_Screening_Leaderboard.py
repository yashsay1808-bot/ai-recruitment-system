"""
Page 2: Candidate Screening & Ranked Leaderboard
Standalone Page Module for Ranked Candidate Table, Recruiter Filters, and Blind Hiring Toggle.
"""

import streamlit as st

st.set_page_config(
    page_title="Screening Leaderboard - AI Recruitment System",
    page_icon="📊",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.ui.views.screening_results import render_screening_results_view

if check_authentication():
    render_shared_sidebar()
    
    # Ensure candidates are screened
    if not st.session_state.get("ranked_candidates"):
        from src.ui.pipeline import process_and_rank_resumes
        process_and_rank_resumes()

    render_screening_results_view(
        st.session_state.get("ranked_candidates", []),
        st.session_state.get("current_jd", {}),
        st.session_state["db"]
    )

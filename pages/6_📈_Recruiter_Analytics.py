"""
Page 6: Recruiter Analytics & Screening History
Standalone Page Module for Visual Talent Pool Distributions, Skill Bottlenecks, and Email Gen.
"""

import streamlit as st

st.set_page_config(
    page_title="Recruiter Analytics - AI Recruitment System",
    page_icon="📈",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.ui.views.analytics_dashboard import render_analytics_dashboard_view

if check_authentication():
    render_shared_sidebar()

    if not st.session_state.get("ranked_candidates"):
        from src.ui.pipeline import process_and_rank_resumes
        process_and_rank_resumes()

    db = st.session_state["db"]
    render_analytics_dashboard_view(
        st.session_state.get("ranked_candidates", []),
        st.session_state.get("current_jd", {}),
        db
    )

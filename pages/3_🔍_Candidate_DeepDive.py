"""
Page 3: Candidate Deep-Dive & Explainable AI (XAI)
Standalone Page Module for Rationale Breakdown, Skill Gap Badges, and ATS Quality Audit.
"""

import streamlit as st

st.set_page_config(
    page_title="Candidate Deep-Dive & XAI - AI Recruitment System",
    page_icon="🔍",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.ui.views.candidate_details import render_candidate_details_view

if check_authentication():
    render_shared_sidebar()

    if not st.session_state.get("ranked_candidates"):
        from src.ui.pipeline import process_and_rank_resumes
        process_and_rank_resumes()

    ranked = st.session_state.get("ranked_candidates", [])
    if ranked and not st.session_state.get("selected_candidate"):
        st.session_state["selected_candidate"] = ranked[0]

    render_candidate_details_view(
        st.session_state.get("selected_candidate"),
        st.session_state.get("current_jd", {})
    )

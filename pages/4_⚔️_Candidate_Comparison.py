"""
Page 4: Candidate Comparison Matrix & Radar Charts
Standalone Page Module for Side-by-Side Multi-Candidate Benchmarking and Plotly Radar Charts.
"""

import streamlit as st

st.set_page_config(
    page_title="Candidate Comparison - AI Recruitment System",
    page_icon="⚔️",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.ui.views.candidate_comparison import render_candidate_comparison_view

if check_authentication():
    render_shared_sidebar()

    if not st.session_state.get("ranked_candidates"):
        from src.ui.pipeline import process_and_rank_resumes
        process_and_rank_resumes()

    render_candidate_comparison_view(
        st.session_state.get("ranked_candidates", []),
        st.session_state.get("current_jd", {})
    )

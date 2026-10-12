"""
Page 5: AI Interview Assistant & Question Kit
Standalone Page Module for Customized Technical, Project, and Behavioral Interview Preparation.
"""

import streamlit as st

st.set_page_config(
    page_title="Interview Prep Kit - AI Recruitment System",
    page_icon="🎙️",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.ui.views.interview_assistant import render_interview_assistant_view

if check_authentication():
    render_shared_sidebar()

    if not st.session_state.get("ranked_candidates"):
        from src.ui.pipeline import process_and_rank_resumes
        process_and_rank_resumes()

    q_gen = st.session_state["q_generator"]
    render_interview_assistant_view(
        st.session_state.get("ranked_candidates", []),
        st.session_state.get("current_jd", {}),
        q_gen
    )

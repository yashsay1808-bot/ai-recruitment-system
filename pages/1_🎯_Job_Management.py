"""
Page 1: Job Description & Candidate Resume Upload
Standalone Page Module for Job Role Management, Weight Sliders & Resume Upload.
"""

import streamlit as st

st.set_page_config(
    page_title="Job & Upload - AI Recruitment System",
    page_icon="🎯",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.ui.views.job_management import render_job_management_view

if check_authentication():
    render_shared_sidebar()
    db = st.session_state["db"]
    jd_parser = st.session_state["jd_parser"]
    render_job_management_view(db, jd_parser)

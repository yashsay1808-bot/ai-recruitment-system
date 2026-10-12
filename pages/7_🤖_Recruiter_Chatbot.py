"""
Page 7: AI Recruiter Assistant Chatbot
Standalone Page Module for Interactive Natural Language Inquiries over Candidates & Screening Results.
"""

import streamlit as st

st.set_page_config(
    page_title="AI Recruiter Copilot - AI Recruitment System",
    page_icon="🤖",
    layout="wide"
)

from src.ui.session_init import check_authentication, render_shared_sidebar
from src.core.recruiter_chatbot import RecruiterChatbot
from src.ui.views.chatbot_view import render_chatbot_view

if check_authentication():
    render_shared_sidebar()

    # Ensure candidates are parsed & evaluated
    if not st.session_state.get("ranked_candidates"):
        from src.ui.pipeline import process_and_rank_resumes
        process_and_rank_resumes()

    if "chatbot_engine" not in st.session_state:
        st.session_state["chatbot_engine"] = RecruiterChatbot()

    chatbot = st.session_state["chatbot_engine"]
    render_chatbot_view(
        ranked_candidates=st.session_state.get("ranked_candidates", []),
        current_jd=st.session_state.get("current_jd", {}),
        chatbot=chatbot
    )

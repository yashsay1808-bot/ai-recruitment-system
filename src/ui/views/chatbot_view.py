"""
Interactive Recruiter Chatbot UI View
Provides a natural language conversational assistant for HR recruiters and talent acquisition leads.
Supports prompt chips, candidate targeting, salary estimation, risk checks, and transcript exports.
"""

import streamlit as st
from typing import Dict, List, Any
from src.core.recruiter_chatbot import RecruiterChatbot


def render_chatbot_view(
    ranked_candidates: List[Dict[str, Any]],
    current_jd: Dict[str, Any],
    chatbot: RecruiterChatbot
):
    """Renders the upgraded AI Recruiter Copilot interface."""
    job_title = current_jd.get("job_title", "Target Role")
    total_candidates = len(ranked_candidates)
    top_cand = ranked_candidates[0] if ranked_candidates else None
    top_name = top_cand.get("candidate_name", "N/A") if top_cand else "N/A"
    top_score = top_cand.get("overall_score", 0.0) if top_cand else 0.0

    # Header Card with Ambient Styling
    st.markdown(f"""
    <div class="copilot-header-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="color: #4f46e5; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;">
                    Recruiter copilot
                </div>
                <h2 style="color: #0f172a; margin: 4px 0 6px 0; font-size: 1.5rem; font-weight: 650;">
                    Ask about your candidates
                </h2>
                <div style="color: #64748b; font-size: 0.9rem;">
                    Conversational talent intelligence, candidate gap probing, market salary benchmarking & risk auditing.
                </div>
            </div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 18px; text-align: right;">
                <div style="color: #64748b; font-size: 0.72rem; text-transform: uppercase; font-weight: 600;">Active role</div>
                <div style="color: #0f172a; font-weight: 600; font-size: 1.05rem;">{job_title}</div>
                <div style="color: #059669; font-size: 0.82rem; font-weight: 500;">Top:  {top_name} ({top_score}%)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not ranked_candidates:
        st.info("⚠️ No candidate resumes screened yet. Please configure a Job Description and upload resumes in **Page 1 (Job & Upload)** to start chatting with the Copilot.")
        return

    # Initialize Chat History
    if "chatbot_messages" not in st.session_state:
        st.session_state["chatbot_messages"] = [
            {
                "role": "assistant",
                "content": f"👋 Hello! I am your **AI Recruiter Copilot**. I have analyzed **{total_candidates} candidate resumes** for the **{job_title}** position.\n\n"
                           f"Our current leaderboard is led by **{top_name}** (`{top_score}%` match). How can I assist your hiring decision today?"
            }
        ]

    # Target Candidate Focus Dropdown + Quick Context Filter
    cand_options = ["All Candidates"] + [f"{c.get('candidate_name')} (Rank #{c.get('rank', i+1)})" for i, c in enumerate(ranked_candidates)]
    
    col_filter, col_reset = st.columns([4, 1])
    with col_filter:
        selected_focus = st.selectbox(
            "🎯 Focus Query on Specific Candidate:",
            options=cand_options,
            index=0,
            key="chatbot_candidate_focus",
            help="Directs prompts specifically to this candidate's background."
        )
    with col_reset:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Reset Chat", use_container_width=True, key="reset_chat_top"):
            st.session_state["chatbot_messages"] = [
                {
                    "role": "assistant",
                    "content": f"👋 Chat session reset. Ask me anything about candidates for **{job_title}**!"
                }
            ]
            st.rerun()

    # Determine candidate name prefix if focused
    target_name_prefix = ""
    if selected_focus != "All Candidates":
        target_name_prefix = selected_focus.split(" (Rank")[0].strip()

    prompt_to_send = None

    # Categorized Prompt Tabs
    tab_strat, tab_skills, tab_comp = st.tabs([
        "🏆 Strategy & Rankings",
        "🔍 Skills & Risks",
        "💰 Comp & Outreach"
    ])

    with tab_strat:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏆 Who is #1 and why?", use_container_width=True, key="btn_top_cand"):
                prompt_to_send = "Who is the top candidate and why?"
        with c2:
            if st.button("⚖️ Compare Top 2 Candidates", use_container_width=True, key="btn_compare"):
                prompt_to_send = "Compare the top 2 candidates side by side"
        with c3:
            if st.button("📊 Screening Batch Summary", use_container_width=True, key="btn_summary"):
                prompt_to_send = "Summarize the current screening batch statistics"

    with tab_skills:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔍 Most Common Skill Gaps", use_container_width=True, key="btn_gaps"):
                prompt_to_send = "What are the common missing skills across the candidate pool?"
        with c2:
            target_str = f" for {target_name_prefix}" if target_name_prefix else ""
            if st.button(f"🚨 Analyze Red Flags{target_str}", use_container_width=True, key="btn_redflags"):
                prompt_to_send = f"Analyze red flags and hiring risks for {target_name_prefix}" if target_name_prefix else "Analyze red flags and hiring risks across candidates"
        with c3:
            if st.button("💼 Candidates with 2+ Yrs Exp", use_container_width=True, key="btn_exp"):
                prompt_to_send = "Show me candidates with more than 2 years of experience"

    with tab_comp:
        c1, c2, c3 = st.columns(3)
        with c1:
            target_str = f" for {target_name_prefix}" if target_name_prefix else " for top candidate"
            if st.button(f"💰 Estimate Salary & Leveling{target_str}", use_container_width=True, key="btn_salary"):
                prompt_to_send = f"Estimate market salary and leveling for {target_name_prefix}" if target_name_prefix else "Estimate market salary and leveling for top candidate"
        with c2:
            target_str = f" for {target_name_prefix}" if target_name_prefix else " for top candidate"
            if st.button(f"✉️ Draft Interview Invite{target_str}", use_container_width=True, key="btn_invite"):
                prompt_to_send = f"Draft an interview invitation email for {target_name_prefix}" if target_name_prefix else "Draft an interview invitation email for top candidate"
        with c3:
            target_str = f" for {target_name_prefix}" if target_name_prefix else " for top candidate"
            if st.button(f"🎙️ Interview Questions{target_str}", use_container_width=True, key="btn_interview_q"):
                prompt_to_send = f"What interview questions should I ask {target_name_prefix}?" if target_name_prefix else "What interview questions should I ask the top candidate?"

    st.markdown("---")

    # Render Chat History Stream
    for msg in st.session_state["chatbot_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input Box
    user_input = st.chat_input("Ask about candidate scores, skill gaps, market rates, red flags, or draft emails...")

    query = prompt_to_send or user_input

    if query:
        # Append User Message
        st.session_state["chatbot_messages"].append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("AI Talent Copilot analyzing candidate knowledge base..."):
                response = chatbot.answer_query(
                    user_query=query,
                    ranked_candidates=ranked_candidates,
                    current_jd=current_jd
                )
                st.markdown(response)

        # Append Assistant Response
        st.session_state["chatbot_messages"].append({"role": "assistant", "content": response})

    # Footer Actions: Export Transcript
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    c_space, c_export = st.columns([4, 1])
    with c_export:
        # Format chat transcript as markdown
        transcript_text = f"# AI Recruiter Copilot Session Transcript\n**Job Role:** {job_title}\n**Total Candidates:** {total_candidates}\n\n---\n\n"
        for m in st.session_state["chatbot_messages"]:
            speaker = "AI Recruiter Copilot" if m["role"] == "assistant" else "Recruiter"
            transcript_text += f"### {speaker}:\n{m['content']}\n\n"

        st.download_button(
            label="📥 Export Chat (MD)",
            data=transcript_text,
            file_name=f"recruiter_copilot_{job_title.lower().replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )

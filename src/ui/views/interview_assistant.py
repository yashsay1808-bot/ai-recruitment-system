"""
AI Interview Assistant & Question Kit Generator
Generates candidate-tailored technical, project-based, gap-probing,
and HR behavioral interview questionnaires with scoring guidelines.
"""

import streamlit as st
from typing import Dict, List, Any
from src.core.interview_generator import InterviewQuestionGenerator
from src.core.llm_client import LLMClient


def render_interview_assistant_view(
    ranked_candidates: List[Dict[str, Any]],
    current_jd: Dict[str, Any],
    q_generator: InterviewQuestionGenerator
):
    """Renders the interactive AI interview preparation kit and questionnaire."""
    st.markdown("## 🎙️ AI Interview Preparation Kit")
    st.markdown("Generates candidate-specific technical, project, and behavioral interview questions with recruiter evaluation keys.")

    if not ranked_candidates:
        st.info("Please screen candidates first before generating interview questions.")
        return

    # Select Candidate
    cand_options = {f"#{c.get('rank', 1)} - {c.get('candidate_name')} ({c.get('overall_score')}%)": c for c in ranked_candidates}
    
    # Check if there is already a preselected candidate in session state
    default_idx = 0
    if "selected_candidate" in st.session_state and st.session_state["selected_candidate"]:
        sel_c = st.session_state["selected_candidate"]
        sel_key = f"#{sel_c.get('rank', 1)} - {sel_c.get('candidate_name')} ({sel_c.get('overall_score')}%)"
        if sel_key in cand_options:
            default_idx = list(cand_options.keys()).index(sel_key)

    chosen_key = st.selectbox("Select Candidate for Interview Prep", list(cand_options.keys()), index=default_idx)
    candidate = cand_options[chosen_key]

    c_data = candidate.get("candidate_data", {})
    gap = candidate.get("gap_results", {})
    job_title = current_jd.get("job_title", "Technical Role")

    # Generate or retrieve questions
    cache_key = f"q_{candidate.get('file_name', '')}_{job_title}"
    if cache_key not in st.session_state:
        # Base offline questions
        questions = q_generator.generate_questionnaire(c_data, current_jd, gap)
        
        # Check if optional LLM is configured
        llm = LLMClient(api_key=st.session_state.get("llm_api_key"))
        if llm.is_enabled:
            with st.spinner("Enriching questionnaire with Generative AI..."):
                questions = llm.enhance_interview_questions(
                    candidate_name=candidate.get("candidate_name", "Candidate"),
                    job_title=job_title,
                    matched_skills=gap.get("matched_skills", []),
                    missing_skills=gap.get("missing_skills", []),
                    projects=c_data.get("projects", []),
                    fallback_questions=questions
                )
        st.session_state[cache_key] = questions

    questions = st.session_state[cache_key]

    st.markdown("---")

    # Top Candidate Profile Bar
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.markdown(f"**Target Role:** {job_title}")
    with col_c2:
        st.markdown(f"**Candidate:** {candidate.get('candidate_name')}")
    with col_c3:
        st.markdown(f"**Experience:** {c_data.get('experience', {}).get('years_of_experience', 0)} Years")

    st.markdown("---")

    # Question Tabs
    tab_tech, tab_proj, tab_gap, tab_hr = st.tabs([
        "💻 Technical Questions", 
        "🚀 Project Deep-Dive", 
        "🔍 Skill Gap Probing", 
        "🤝 Behavioral & HR"
    ])

    with tab_tech:
        st.subheader("💻 Core Technical Questions")
        tech_q = questions.get("technical_questions", [])
        if tech_q:
            for i, q in enumerate(tech_q):
                diff = q.get("difficulty", "Medium")
                diff_color = "#059669" if diff == "Easy" else ("#d97706" if diff == "Medium" else "#dc2626")
                st.markdown(f"##### Q{i+1}. {q.get('question')}")
                st.markdown(f"<span style='color: {diff_color}; font-weight: 600;'>[Difficulty: {diff}]</span> • Target Skill: `{q.get('skill', 'Technical')}`", unsafe_allow_html=True)
                with st.expander("🔑 Recruiter Evaluation Key & Expected Answer"):
                    st.info(q.get("eval_criteria", "Look for clear explanations and real-world trade-off awareness."))
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No specific technical questions generated.")

    with tab_proj:
        st.subheader("🚀 Project-Specific Architecture Questions")
        proj_q = questions.get("project_questions", [])
        if proj_q:
            for i, q in enumerate(proj_q):
                st.markdown(f"##### Q{i+1}. {q.get('question')}")
                st.caption(f"Project Reference: {q.get('project_title', 'Practical Project')}")
                with st.expander("🔑 What to look for in Candidate's Answer"):
                    st.info(q.get("eval_criteria", "Assess architectural decisions, edge case handling, and scalability."))
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No project questions generated.")

    with tab_gap:
        st.subheader("🔍 Skill Gap Probing Questions")
        st.caption("Probe candidate's ability to ramp up on technologies required by the role:")
        gap_q = questions.get("gap_probing_questions", [])
        if gap_q:
            for i, q in enumerate(gap_q):
                st.markdown(f"##### Q{i+1}. {q.get('question')}")
                st.caption(f"Missing Skill Evaluated: {q.get('missing_skill', 'Competency')}")
                with st.expander("🔑 Evaluation Guidelines"):
                    st.info(q.get("eval_criteria", "Look for self-learning velocity, parallel fundamentals, and growth mindset."))
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.success("Candidate has no major skill gaps! All core competencies matched.")

    with tab_hr:
        st.subheader("🤝 Behavioral & Cultural Alignment")
        hr_q = questions.get("behavioral_questions", [])
        if hr_q:
            for i, q in enumerate(hr_q):
                st.markdown(f"##### Q{i+1}. {q.get('question')}")
                with st.expander("🔑 Behavioral Evaluation Criteria"):
                    st.info(q.get("eval_criteria", "Assess teamwork, communication, and resilience."))
                st.markdown("<br>", unsafe_allow_html=True)

    # Export Kit
    st.markdown("---")
    st.subheader("📄 Export Interview Kit")
    
    # Generate Markdown export text
    export_md = f"# Interview Question Kit: {candidate.get('candidate_name')} for {job_title}\n"
    export_md += f"Overall Match Score: {candidate.get('overall_score')}%\n\n"
    export_md += "## Technical Questions\n"
    for q in questions.get("technical_questions", []):
        export_md += f"- **Q:** {q.get('question')} ({q.get('difficulty')})\n  - *Eval Key:* {q.get('eval_criteria')}\n\n"
    export_md += "## Project Questions\n"
    for q in questions.get("project_questions", []):
        export_md += f"- **Q:** {q.get('question')}\n  - *Eval Key:* {q.get('eval_criteria')}\n\n"
    export_md += "## Skill Gap Probing Questions\n"
    for q in questions.get("gap_probing_questions", []):
        export_md += f"- **Q:** {q.get('question')}\n  - *Eval Key:* {q.get('eval_criteria')}\n\n"
    export_md += "## Behavioral Questions\n"
    for q in questions.get("behavioral_questions", []):
        export_md += f"- **Q:** {q.get('question')}\n  - *Eval Key:* {q.get('eval_criteria')}\n\n"

    st.download_button(
        label="📥 Download Complete Interview Kit (Markdown)",
        data=export_md,
        file_name=f"Interview_Kit_{candidate.get('candidate_name').replace(' ', '_')}.md",
        mime="text/markdown"
    )

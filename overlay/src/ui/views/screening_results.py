"""
Candidate Screening & Ranked Leaderboard View
Displays ranked candidates, multi-score breakdowns, recruiter filters,
bias-free blind recruitment toggle, and fast action triggers.
Integrates Hybrid RAG natural language search over the screened candidate pool.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from src.ui.components import render_recommendation_badge, render_metric_card
from src.core.database import RecruitmentDatabase
from src.core.bias_filter import BiasFilter
from src.core.talent_rag import TalentRAG


def render_screening_results_view(
    ranked_candidates: List[Dict[str, Any]],
    current_jd: Dict[str, Any],
    db: RecruitmentDatabase
):
    """Renders the interactive ranked candidate leaderboard and recruiter filter system."""
    st.markdown("## 📊 Candidate Screening & Ranked Leaderboard")
    
    if not ranked_candidates:
        st.info("No candidates screened yet. Please configure a Job Description and upload resumes in the **Job & Upload** tab.")
        return

    # Top Control Bar: Blind Screening Toggle & Save Session
    col_ctrl1, col_ctrl2 = st.columns([1.5, 1], gap="medium")
    
    with col_ctrl1:
        blind_mode = st.toggle(
            "🛡️ Fair & Bias-Aware Blind Screening Mode", 
            value=st.session_state.get("blind_mode", False), 
            help="Anonymizes candidate names, contact details, and demographic clues for unbiased, merit-only evaluation."
        )
        st.session_state["blind_mode"] = blind_mode

    with col_ctrl2:
        session_title = st.text_input(
            "Screening Session Name", 
            value=f"{current_jd.get('job_title', 'Role')} - Batch 1", 
            label_visibility="collapsed"
        )
        if st.button("💾 Save Screening Session to History", use_container_width=True):
            job_id = 1
            s_id = db.save_screening_session(
                job_id=job_id,
                session_name=session_title,
                evaluated_candidates=ranked_candidates
            )
            st.success(f"Screening Session #{s_id} saved to historical records!")

    # Summary Metrics Row
    total_cand = len(ranked_candidates)
    shortlisted = sum(1 for c in ranked_candidates if c.get("overall_score", 0) >= 65.0)
    avg_score = round(sum(c.get("overall_score", 0) for c in ranked_candidates) / max(total_cand, 1), 1)
    top_score = max(c.get("overall_score", 0) for c in ranked_candidates)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Total Resumes", total_cand, "Processed across formats")
    with m2:
        render_metric_card("Shortlisted", shortlisted, f"{round(shortlisted/total_cand*100, 1)}% acceptance rate")
    with m3:
        render_metric_card("Average Match", f"{avg_score}%", "Across all candidates")
    with m4:
        render_metric_card("Top Candidate Match", f"{top_score}%", "Highest match score")

    st.markdown("---")

    # SPICE UPGRADE: Hybrid RAG Natural Language Search
    with st.expander("⚡ 🔎 Natural Language Hybrid RAG Talent Search (Dense + Okapi-BM25)", expanded=False):
        st.caption("Retrieve candidates using natural language questions combining experience years, architecture concepts, and tooling:")
        
        # Quick RAG Suggestions
        col_s1, col_s2, col_s3 = st.columns(3)
        sample_query = None
        with col_s1:
            if st.button("🔍 'ML engineers with 2+ yrs PyTorch'", use_container_width=True):
                sample_query = "Find engineers with 2+ years experience in Python and PyTorch who built ML models"
        with col_s2:
            if st.button("🔍 'Backend with Docker and AWS'", use_container_width=True):
                sample_query = "Find backend developers who know Docker and deployed to AWS"
        with col_s3:
            if st.button("🔍 'Fullstack with React & REST API'", use_container_width=True):
                sample_query = "Developers with React, JavaScript, and REST APIs"

        rag_input = st.text_input(
            "Search Query", 
            value=sample_query or "",
            placeholder="e.g. Find engineers with 2+ years in Python who deployed microservices with Docker and AWS"
        )
        
        if rag_input and rag_input.strip():
            # Prepare resume pool for RAG
            pool_for_rag = []
            for c in ranked_candidates:
                cd = dict(c.get("candidate_data", {}))
                cd["candidate_name"] = c.get("candidate_name", "Candidate")
                pool_for_rag.append(cd)

            try:
                from src.core.talent_rag import get_default_engine
                rag = get_default_engine()
                hits = rag.search_talent_pool(rag_input.strip(), pool_for_rag, top_k=4)
                if hits:
                    st.markdown(f"##### Top {len(hits)} Semantic Matches:")
                    for h in hits:
                        with st.container():
                            st.markdown(f"""
                            <div class="metric-card" style="margin-bottom: 10px; padding: 14px 18px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: #38bdf8; font-size: 1.05rem;">#{h.get('rank', 1)} {h.get('candidate_name')}</strong>
                                    <span class="badge-matched">RAG Relevance: {h.get('relevance_score', 0)}%</span>
                                </div>
                                <div style="margin-top: 6px; font-size: 0.82rem; color: #cbd5e1;">
                                    ✓ Matched: {', '.join((m.get('competency') or m.get('name') or '') if isinstance(m, dict) else str(m) for m in h.get('matched_competencies', [])) or 'General semantic fit'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            if h.get("snippets"):
                                st.caption(f"Context Snippet: {h['snippets'][0].get('markdown', '')[:200]}...")
                else:
                    st.info("No candidates closely match this specific query.")
            except Exception as e:
                st.warning(f"RAG search notice: {e}")

    # Recruiter Filters Section
    with st.expander("🔍 Recruiter Search & Multi-Criteria Filters", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        
        with f1:
            min_score = st.slider("Minimum Match Score (%)", 0, 100, 50, step=5)
        
        with f2:
            exp_filter = st.selectbox("Experience Level", ["All Experience Levels", "Freshers (< 1 yr)", "1 - 3 Years", "3+ Years"])
            
        with f3:
            all_jd_skills = current_jd.get("required_skills", [])
            req_skill_filter = st.multiselect("Must-Have Skills Filter", all_jd_skills)
            
        with f4:
            status_filter = st.selectbox("Recommendation Filter", ["All Statuses", "Strongly Recommended", "Recommended", "HR Review", "Not Recommended"])

    # Apply Filtering
    bias_filter = BiasFilter()
    filtered_candidates = []

    for idx, cand in enumerate(ranked_candidates):
        score = cand.get("overall_score", 0)
        c_data = cand.get("candidate_data", {})
        exp_years = c_data.get("experience", {}).get("years_of_experience", 0.0)
        c_skills = c_data.get("skills", [])
        status_label = cand.get("explanation", {}).get("status_label", "")

        # Score filter
        if score < min_score:
            continue

        # Exp filter
        if exp_filter == "Freshers (< 1 yr)" and exp_years >= 1.0:
            continue
        elif exp_filter == "1 - 3 Years" and not (1.0 <= exp_years < 3.0):
            continue
        elif exp_filter == "3+ Years" and exp_years < 3.0:
            continue

        # Required skill filter
        if req_skill_filter:
            if not all(s in c_skills for s in req_skill_filter):
                continue

        # Status filter
        if status_filter != "All Statuses":
            if status_filter.lower() not in status_label.lower():
                continue

        # Apply blind mode if active
        if blind_mode:
            display_cand = dict(cand)
            blind_cdata = bias_filter.anonymize_candidate(c_data, candidate_index=cand.get("rank", idx+1))
            display_cand["candidate_name"] = blind_cdata["candidate_name"]
            display_cand["candidate_data"] = blind_cdata
            filtered_candidates.append(display_cand)
        else:
            filtered_candidates.append(cand)

    st.markdown(f"### 🏆 Ranked Candidates ({len(filtered_candidates)} of {total_cand})")

    # Table rendering
    table_rows = []
    for c in filtered_candidates:
        b = c.get("breakdown", {})
        c_data = c.get("candidate_data", {})
        exp_str = f"{c_data.get('experience', {}).get('years_of_experience', 0)} yrs"
        edu_str = f"{c_data.get('education', {}).get('degree', 'B.E.')}"
        
        table_rows.append({
            "Rank": f"#{c.get('rank', 1)}",
            "Candidate Name": c.get("candidate_name"),
            "Overall Match": f"{c.get('overall_score')}%",
            "Skills Match": f"{b.get('technical_skills')}%",
            "Semantic Fit": f"{b.get('semantic_jd')}%",
            "Experience": exp_str,
            "Education": edu_str,
            "ATS Quality": f"{b.get('resume_quality')}%",
            "Recommendation": c.get("explanation", {}).get("status_label", "Recommended")
        })

    if table_rows:
        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning("No candidates match the specified filter criteria.")

    # Candidate Quick Selection for Deep-Dive
    st.markdown("---")
    st.markdown("### 🔍 Select Candidate for Detailed Deep-Dive & XAI Inspection")

    cand_names = [f"#{c.get('rank', 1)} - {c.get('candidate_name')} ({c.get('overall_score')}%)" for c in filtered_candidates]
    if cand_names:
        selected_cand_str = st.selectbox("Select Candidate to Inspect", cand_names, index=0)
        selected_rank = int(selected_cand_str.split(" - ")[0].lstrip("#"))
        
        # Find candidate
        selected_candidate = next((c for c in filtered_candidates if c.get("rank") == selected_rank), filtered_candidates[0])
        st.session_state["selected_candidate"] = selected_candidate

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔎 Open Candidate Deep-Dive & XAI Tab", type="primary", use_container_width=True):
                st.session_state["active_tab_index"] = 2  # Deep-dive tab
                st.rerun()
        with col_btn2:
            if st.button("🎙️ Open AI Interview Prep Kit", use_container_width=True):
                st.session_state["active_tab_index"] = 4  # Interview tab
                st.rerun()

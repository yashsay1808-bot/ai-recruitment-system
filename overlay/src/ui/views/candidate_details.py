"""
Candidate Deep-Dive & Explainable AI (XAI) View
Provides transparent inspection of candidate scores, detailed skill gap analysis,
autonomous Multi-Agent Recruiter Council debate, GitHub Authenticity verification,
resume quality critique, and actionable suggestions.
"""

import streamlit as st
from typing import Dict, List, Any
from src.ui.components import (
    render_skill_badges, 
    render_recommendation_badge, 
    create_candidate_breakdown_bar_chart, 
    render_metric_card
)
from src.core.quality_analyzer import ResumeQualityAnalyzer


def render_candidate_details_view(
    candidate: Dict[str, Any],
    current_jd: Dict[str, Any]
):
    """Renders exhaustive explainable AI breakdown and candidate profile deep-dive."""
    if not candidate:
        st.info("No candidate selected. Please select a candidate from the **Screening Leaderboard** tab.")
        return

    c_data = candidate.get("candidate_data", {})
    breakdown = candidate.get("breakdown", {})
    gap = candidate.get("gap_results", {})
    explanation = candidate.get("explanation", {})
    overall_score = candidate.get("overall_score", 0)

    # 1. Header Banner
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown(f"## 👤 {candidate.get('candidate_name', 'Candidate')} (Rank #{candidate.get('rank', 1)})")
        st.caption(f"📁 Source File: `{candidate.get('file_name', 'resume.pdf')}` | Email: `{c_data.get('email', 'N/A')}` | Phone: `{c_data.get('phone', 'N/A')}`")
        links_md = []
        if c_data.get("linkedin"):
            links_md.append(f"[LinkedIn]({c_data.get('linkedin')})")
        if c_data.get("github"):
            links_md.append(f"[GitHub]({c_data.get('github')})")
        if links_md:
            st.markdown("🌐 " + " • ".join(links_md))
    with col_h2:
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        render_recommendation_badge(
            explanation.get("status_key", "RECOMMENDED"),
            explanation.get("status_label", "🟢 Recommended")
        )
        st.markdown(f"<h1 style='color: #38bdf8; margin: 0; padding: 0;'>{overall_score}%</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # 2. Multi-Agent Recruiter Council + 3. GitHub authenticity (Obsidian renderers, real engine output)
    from src.ui.views.council_view import render_council_panel, render_github_widget
    try:
        render_council_panel(candidate, current_jd, key_prefix="dd")
    except Exception as e:
        st.warning(f"Council evaluation notice: {e}")
    st.markdown("---")
    try:
        render_github_widget(candidate, key_prefix="ddgh")
    except Exception as e:
        st.info(f"GitHub verification unavailable: {e}")

    st.markdown("---")

    # 4. Explainable AI (XAI) Executive Summary Card
    st.subheader("🧠 Explainable AI (XAI) Decision Rationale")
    st.markdown(f"""
    <div class="xai-card">
        <h4 style="color: #a5b4fc; margin-top: 0;">AI Recruiter Rationale & Executive Summary</h4>
        <p style="color: #e0e7ff; font-size: 1.02rem; line-height: 1.5;">
            {explanation.get("executive_summary", "")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_why1, col_why2 = st.columns(2, gap="medium")
    with col_why1:
        st.markdown("##### 🌟 Key Strengths")
        strengths = explanation.get("strengths", [])
        if strengths:
            for s in strengths:
                st.markdown(f"- ✅ **{s}**")
        else:
            st.markdown("- Meets standard requirements.")

    with col_why2:
        st.markdown("##### ⚠️ Competency Shortfalls / Gaps")
        warnings = explanation.get("warnings", [])
        if warnings:
            for w in warnings:
                st.markdown(f"- ⚠️ <span style='color: #fda4af;'>{w}</span>", unsafe_allow_html=True)
        else:
            st.markdown("- No critical deficiencies flagged.")

    st.markdown("---")

    # 5. Multi-Dimensional Score Breakdown & Skill Gap
    col_chart, col_gap = st.columns([1.1, 0.9], gap="medium")

    with col_chart:
        st.subheader("📊 Multi-Score Dimension Breakdown")
        st.caption("Hybrid weights applied across all 7 evaluation pillars:")
        fig_bar = create_candidate_breakdown_bar_chart(breakdown)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_gap:
        st.subheader("🎯 Skill Gap Analysis")
        st.caption(f"Matched {gap.get('matched_count', 0)} of {gap.get('total_required', 0)} required technical skills:")
        
        render_skill_badges(
            gap.get("matched_skills", []),
            gap.get("partially_matched_skills", []),
            gap.get("missing_skills", [])
        )

        cat_scores = gap.get("category_scores", {})
        if cat_scores:
            st.markdown("###### Domain Coverage:")
            for cat, score in cat_scores.items():
                st.progress(score / 100.0, text=f"{cat}: {score}%")

    st.markdown("---")

    # 6. Structured Profile: Experience, Education, Projects
    col_p1, col_p2 = st.columns(2, gap="medium")

    with col_p1:
        st.subheader("💼 Work Experience & Qualifications")
        exp = c_data.get("experience", {})
        edu = c_data.get("education", {})
        
        st.markdown(f"**Total Experience:** `{exp.get('years_of_experience', 0)} Years` ({exp.get('experience_level', 'Mid Level')})")
        if exp.get("detected_titles"):
            st.markdown(f"**Detected Titles:** {', '.join(exp.get('detected_titles', []))}")
        
        st.markdown(f"**Degree:** `{edu.get('degree', 'Degree')}`")
        st.markdown(f"**Branch / Field:** `{edu.get('branch', 'Engineering')}`")
        st.markdown(f"**CGPA / Score:** `{edu.get('cgpa', 'N/A')}` | **Graduation Year:** `{edu.get('graduation_year', 'N/A')}`")

        certs = c_data.get("certifications", [])
        if certs:
            st.markdown("**Certifications & Honors:**")
            for c in certs:
                st.markdown(f"- 📜 {c}")

    with col_p2:
        st.subheader("🚀 Practical Projects")
        projects = c_data.get("projects", [])
        if projects:
            for p in projects:
                p_title = p.get("title", "Project")
                p_skills = ", ".join(p.get("skills_used", [])) or "Technical Stack"
                st.markdown(f"**• {p_title}**")
                st.caption(f"Tech Stack: {p_skills}")
                if p.get("description"):
                    st.markdown(f"_{p.get('description')[:200]}..._")
        else:
            st.info("No structured projects section extracted.")

    st.markdown("---")

    # 7. Resume Quality & ATS Suggestions
    st.subheader("📝 Resume ATS Quality & Candidate Feedback")
    
    qa = ResumeQualityAnalyzer()
    q_res = qa.analyze(c_data, current_jd.get("required_skills", []))
    
    col_q1, col_q2 = st.columns([1, 2], gap="medium")
    with col_q1:
        render_metric_card("ATS Quality Score", f"{q_res['quality_score']}/100", f"Rating: {q_res['rating']} ({q_res['word_count']} words)")
    
    with col_q2:
        tab_good, tab_imp, tab_sug = st.tabs(["✓ Positive Elements", "⚠ Needs Improvement", "💡 AI Suggestions"])
        with tab_good:
            for g in q_res["good_points"]:
                st.markdown(f"- {g}")
        with tab_imp:
            for imp in q_res["improvements"]:
                st.markdown(f"- {imp}")
        with tab_sug:
            for sug in q_res["suggestions"]:
                st.markdown(f"- 💡 **{sug}**")

    # 8. Raw Extracted Text Viewer
    with st.expander("📄 View Raw Parsed Resume Text"):
        st.text_area("Extracted Plain Text", value=c_data.get("raw_text", ""), height=250, disabled=True)

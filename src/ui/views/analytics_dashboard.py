"""
Recruiter Analytics Dashboard & Screening History View
Visualizes aggregate screening metrics, candidate score distributions,
in-demand vs missing skill frequency, historical sessions, and automated email generation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
from src.core.database import RecruitmentDatabase
from src.ui.components import render_metric_card


def render_analytics_dashboard_view(
    ranked_candidates: List[Dict[str, Any]],
    current_jd: Dict[str, Any],
    db: RecruitmentDatabase
):
    """Renders comprehensive recruiter analytics, historical audits, and email templates."""
    st.markdown("## 📈 Recruiter Analytics & Historical Screening")
    st.markdown("Aggregate insights into candidate talent pools, skill demand bottlenecks, and screening audit history.")

    tab_curr, tab_hist, tab_email = st.tabs([
        "📊 Current Batch Analytics", 
        "🏛️ Screening History & Audit", 
        "✉️ Shortlist Email Generator"
    ])

    # ------------------ TAB 1: Current Batch Analytics ------------------
    with tab_curr:
        if not ranked_candidates:
            st.info("No active candidate batch screened yet. Process resumes in the **Job & Upload** tab.")
        else:
            total_cand = len(ranked_candidates)
            shortlisted = sum(1 for c in ranked_candidates if c.get("overall_score", 0) >= 65.0)
            under_review = sum(1 for c in ranked_candidates if 50.0 <= c.get("overall_score", 0) < 65.0)
            rejected = sum(1 for c in ranked_candidates if c.get("overall_score", 0) < 50.0)
            avg_score = round(sum(c.get("overall_score", 0) for c in ranked_candidates) / max(total_cand, 1), 1)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_metric_card("Total Evaluated", total_cand)
            with c2:
                render_metric_card("Shortlisted", shortlisted, f"{round(shortlisted/total_cand*100, 1)}% rate")
            with c3:
                render_metric_card("Under Review", under_review)
            with c4:
                render_metric_card("Average Match", f"{avg_score}%")

            st.markdown("---")

            col_g1, col_g2 = st.columns(2, gap="medium")

            # Chart 1: Candidate Score Distribution
            with col_g1:
                st.subheader("📊 Candidate Match Score Distribution")
                scores = [c.get("overall_score", 0) for c in ranked_candidates]
                fig_hist = px.histogram(
                    x=scores,
                    nbins=10,
                    labels={"x": "Overall Match Score (%)"},
                    title="",
                    color_discrete_sequence=["#4f46e5"]
                )
                fig_hist.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#e2e8f0"),
                    yaxis=dict(gridcolor="#e2e8f0", title="Candidate Count"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=280
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            # Chart 2: Decision Funnel Donut
            with col_g2:
                st.subheader("🎯 Screening Decision Funnel")
                fig_donut = go.Figure(data=[go.Pie(
                    labels=["Shortlisted (>=65%)", "Under Review (50-64%)", "Rejected (<50%)"],
                    values=[shortlisted, under_review, rejected],
                    hole=0.5,
                    marker=dict(colors=["#059669", "#d97706", "#dc2626"])
                )])
                fig_donut.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#334155"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=280
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            st.markdown("---")

            col_s1, col_s2 = st.columns(2, gap="medium")

            # Chart 3: Most Common Skills in Candidate Pool
            with col_s1:
                st.subheader("🧩 Most Common Skills in Talent Pool")
                all_skills_pool = []
                for c in ranked_candidates:
                    all_skills_pool.extend(c.get("candidate_data", {}).get("skills", []))
                
                if all_skills_pool:
                    skill_counts = pd.Series(all_skills_pool).value_counts().head(8)
                    fig_skills = px.bar(
                        x=skill_counts.values,
                        y=skill_counts.index,
                        orientation='h',
                        labels={"x": "Frequency", "y": "Skill"},
                        color_discrete_sequence=["#4f46e5"]
                    )
                    fig_skills.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(gridcolor="#e2e8f0"),
                        yaxis=dict(autorange="reversed", gridcolor="#e2e8f0"),
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=280
                    )
                    st.plotly_chart(fig_skills, use_container_width=True)
                else:
                    st.info("No skills detected in pool.")

            # Chart 4: Common Missing Skills / Bottlenecks
            with col_s2:
                st.subheader("⚠️ Common Missing Skill Bottlenecks")
                all_missing_pool = []
                for c in ranked_candidates:
                    all_missing_pool.extend(c.get("gap_results", {}).get("missing_skills", []))
                
                if all_missing_pool:
                    missing_counts = pd.Series(all_missing_pool).value_counts().head(8)
                    fig_missing = px.bar(
                        x=missing_counts.values,
                        y=missing_counts.index,
                        orientation='h',
                        labels={"x": "Candidate Gap Count", "y": "Skill"},
                        color_discrete_sequence=["#dc2626"]
                    )
                    fig_missing.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(gridcolor="#e2e8f0"),
                        yaxis=dict(autorange="reversed", gridcolor="#e2e8f0"),
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=280
                    )
                    st.plotly_chart(fig_missing, use_container_width=True)
                else:
                    st.success("No missing skills in candidate pool!")

    # ------------------ TAB 2: Historical Screening Sessions ------------------
    with tab_hist:
        st.subheader("🏛️ Historical Screening Sessions in SQLite Database")
        sessions = db.get_all_sessions()
        
        if not sessions:
            st.info("No previous screening sessions saved yet. Click **Save Screening Session to History** in the Screening tab to persist records.")
        else:
            session_rows = []
            for s in sessions:
                session_rows.append({
                    "Session ID": f"#{s['id']}",
                    "Session Name": s['session_name'],
                    "Job Role": s.get('job_title', 'General Role'),
                    "Total Candidates": s['total_candidates'],
                    "Shortlisted": s['shortlisted_count'],
                    "Avg Score": f"{s['avg_score']}%",
                    "Screened At": s['created_at']
                })
            
            st.dataframe(pd.DataFrame(session_rows), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🔍 Inspect Past Session Candidates")
            sess_dict = {f"Session #{s['id']} - {s['session_name']}": s['id'] for s in sessions}
            selected_sess_label = st.selectbox("Select Past Session to Inspect", list(sess_dict.keys()))
            selected_sess_id = sess_dict[selected_sess_label]

            past_candidates = db.get_session_candidates(selected_sess_id)
            if past_candidates:
                past_rows = []
                for pc in past_candidates:
                    past_rows.append({
                        "Rank": f"#{pc['rank']}",
                        "Candidate Name": pc['candidate_name'],
                        "Email": pc['email'],
                        "Score": f"{pc['overall_score']}%",
                        "Decision": pc['decision']
                    })
                st.dataframe(pd.DataFrame(past_rows), use_container_width=True, hide_index=True)

    # ------------------ TAB 3: Shortlist Email Generator ------------------
    with tab_email:
        st.subheader("✉️ Automated Shortlist & Interview Invitation Email Generator")
        st.caption("Generate ready-to-send interview invitation emails for shortlisted candidates.")

        if ranked_candidates:
            shortlisted_candidates = [c for c in ranked_candidates if c.get("overall_score", 0) >= 60.0]
            cand_names = [c.get("candidate_name") for c in (shortlisted_candidates or ranked_candidates)]
            selected_cand_name = st.selectbox("Select Candidate for Email", cand_names)
            
            c_cand = next((c for c in ranked_candidates if c.get("candidate_name") == selected_cand_name), ranked_candidates[0])
            c_email = c_cand.get("candidate_data", {}).get("email", "candidate@email.com")

            e_type = st.radio("Email Type", ["Interview Invitation (Shortlist)", "Conditional Technical Assessment", "Polite Rejection / Talent Pool Notice"], horizontal=True)

            job_title = current_jd.get("job_title", "Software Specialist")

            if "Invitation" in e_type:
                subject = f"Interview Invitation: {job_title} role at Our Team"
                body = f"""Dear {selected_cand_name},

Thank you for your application for the {job_title} position.

Our AI-assisted recruitment review was very impressed with your background, hands-on technical competencies, and relevant project experience. We would like to invite you to a 45-minute technical interview round.

During this session, we will discuss your experience, dive into your key projects, and explore how your skills align with our current engineering challenges.

Please select a convenient time slot using our scheduling calendar or reply with your availability for this week:
- Option 1: Tomorrow at 2:00 PM IST
- Option 2: Thursday at 11:00 AM IST

We look forward to speaking with you!

Warm regards,
Recruitment & Talent Acquisition Team
"""
            elif "Conditional" in e_type:
                missing_str = ", ".join(c_cand.get("gap_results", {}).get("missing_skills", [])[:2]) or "core domains"
                subject = f"Next Steps: Technical Assessment for {job_title}"
                body = f"""Dear {selected_cand_name},

Thank you for applying for the {job_title} role. 

We reviewed your profile and noticed strong alignment with our technical stack. As part of our technical evaluation, we would like to invite you to complete a brief practical assessment focusing on {missing_str}.

Assessment Link: https://assessment.platform.com/candidate/take
Duration: 60 minutes
Deadline: Within 3 business days

Please reach out if you have any questions.

Best regards,
Engineering Hiring Team
"""
            else:
                subject = f"Update regarding your application for {job_title}"
                body = f"""Dear {selected_cand_name},

Thank you for taking the time to apply for the {job_title} position.

After careful review of all applicants, we have decided to proceed with other candidates whose experience more closely matches our specific technical requirements at this stage.

We have saved your resume in our talent database and will reach out if a relevant opportunity aligning with your skillset arises.

We wish you all the best in your career endeavors.

Sincerely,
Talent Acquisition Team
"""

            st.text_input("To (Candidate Email)", value=c_email)
            st.text_input("Email Subject", value=subject)
            st.text_area("Email Content", value=body, height=260)
            
            st.download_button(
                "📥 Download Email Template (.txt)",
                data=f"To: {c_email}\nSubject: {subject}\n\n{body}",
                file_name=f"Email_{selected_cand_name.replace(' ', '_')}.txt",
                mime="text/plain"
            )
        else:
            st.info("Screen resumes to generate customized email invitations.")

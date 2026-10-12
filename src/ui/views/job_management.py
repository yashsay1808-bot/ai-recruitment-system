"""
Job Management & Resume Upload View
Allows HR to create/select job descriptions, customize hybrid scoring weights,
and upload resumes across formats (PDF, DOCX, TXT, OCR).
"""

import streamlit as st
import os
from typing import Dict, List, Any
from src.core.jd_parser import JDParser
from src.core.database import RecruitmentDatabase
from src.core.skill_ontology import get_all_canonical_skills

# Preloaded Industry Job Templates
SAMPLE_JOB_TEMPLATES = {
    "Machine Learning Engineer": {
        "department": "AI & Data Science",
        "min_experience": 2.0,
        "text": """Job Title: Machine Learning Engineer
Department: AI & Data Science
Experience: 2+ years of relevant experience in ML engineering.

Responsibilities:
- Design, build, and deploy production machine learning pipelines and deep learning models.
- Implement NLP and transformer-based architectures (BERT, LLMs, LangChain) for document intelligence.
- Develop REST APIs using FastAPI/Flask to serve low-latency ML inferences.
- Optimize models using Scikit-Learn, PyTorch, or TensorFlow.
- Experience with Docker containerization, AWS cloud infrastructure, and CI/CD pipelines.

Required Skills:
Python, Machine Learning, Deep Learning, Natural Language Processing, PyTorch, Scikit-Learn, Pandas, NumPy, FastAPI, Docker, AWS, Git

Preferred Qualifications:
- B.E./B.Tech or M.Tech in Computer Science, Data Science, or equivalent.
- Experience with Large Language Models (LLMs), RAG pipelines, or MLOps (MLflow/Kubeflow).
"""
    },
    "Python Backend Developer": {
        "department": "Engineering",
        "min_experience": 1.5,
        "text": """Job Title: Python Backend Developer
Department: Engineering
Experience: 1.5+ years in backend API development.

Responsibilities:
- Build robust microservices and RESTful APIs using Python, FastAPI, and Flask.
- Architect relational and NoSQL database schemas with PostgreSQL, MySQL, and Redis.
- Write clean, modular, and unit-tested code with PyTest.
- Containerize services using Docker and manage deployments on Linux environments.

Required Skills:
Python, FastAPI, Flask, REST API, PostgreSQL, Redis, Docker, Git, Linux, Testing/QA

Preferred Qualifications:
- B.E. / B.Tech in CSE / ISE / IT.
- Familiarity with AWS (EC2, S3, RDS) and CI/CD pipelines.
"""
    },
    "Data Analyst / BI Specialist": {
        "department": "Analytics",
        "min_experience": 1.0,
        "text": """Job Title: Data Analyst / BI Specialist
Department: Analytics & Insights
Experience: 1+ years in data analytics and visualization.

Responsibilities:
- Extract, clean, and transform data from SQL databases and data lakes.
- Build interactive executive dashboards and KPI reports using Power BI and Tableau.
- Perform exploratory data analysis and statistical modeling using Python (Pandas, NumPy, Matplotlib).
- Collaborate with stakeholders to deliver actionable business intelligence.

Required Skills:
SQL, Python, Pandas, NumPy, Power BI, Tableau, Data Visualization, Statistics, ETL, Excel

Preferred Qualifications:
- Bachelor's in CS, Statistics, Mathematics, or Business Analytics.
"""
    },
    "Cloud & DevOps Engineer": {
        "department": "Infrastructure",
        "min_experience": 3.0,
        "text": """Job Title: Senior Cloud & DevOps Engineer
Department: Cloud Infrastructure
Experience: 3+ years in cloud engineering and automation.

Responsibilities:
- Manage multi-cloud infrastructure across AWS and Azure using Terraform (IaC).
- Architect Kubernetes clusters (k8s), Docker containers, and automated CI/CD pipelines.
- Ensure high availability, security compliance, monitoring, and zero-downtime deployments.

Required Skills:
AWS, Kubernetes, Docker, CI/CD, Terraform, Linux, Bash/Shell, Python, Git, Cybersecurity

Preferred Qualifications:
- Degree in Computer Science or Cloud certifications (AWS Solutions Architect, CKA).
"""
    }
}


def render_job_management_view(db: RecruitmentDatabase, parser: JDParser):
    """Renders the Job Description, Weight Configuration, and Upload panel."""
    st.markdown("## 🎯 Job Description & Evaluation Setup")
    st.markdown("Define recruitment criteria, adjust hybrid scoring weights, and upload candidate resumes.")

    col1, col2 = st.columns([1.2, 0.8], gap="medium")

    with col1:
        st.subheader("1. Job Role & Requirements")
        
        # Load saved jobs from DB or template
        saved_jobs = db.get_all_jobs()
        job_options = ["Create New Job"] + list(SAMPLE_JOB_TEMPLATES.keys())
        if saved_jobs:
            job_options += [f"Saved: {j['title']} (ID: {j['id']})" for j in saved_jobs]

        selected_option = st.selectbox(
            "Select Job Template or Existing Role",
            job_options,
            index=1  # Default to Machine Learning Engineer template
        )

        default_title = "Machine Learning Engineer"
        default_dept = "AI & Data Science"
        default_exp = 2.0
        default_text = SAMPLE_JOB_TEMPLATES["Machine Learning Engineer"]["text"]

        if selected_option in SAMPLE_JOB_TEMPLATES:
            tpl = SAMPLE_JOB_TEMPLATES[selected_option]
            default_title = selected_option
            default_dept = tpl["department"]
            default_exp = tpl["min_experience"]
            default_text = tpl["text"]
        elif selected_option.startswith("Saved:"):
            # Find in saved jobs
            job_id = int(selected_option.split("ID: ")[1].rstrip(")"))
            sj = db.get_job_by_id(job_id)
            if sj:
                default_title = sj["title"]
                default_dept = sj.get("department", "Engineering")
                default_exp = sj.get("min_experience", 0.0)
                default_text = sj.get("description_text", "")

        job_title = st.text_input("Job Title", value=default_title)
        c_dept, c_exp = st.columns(2)
        with c_dept:
            department = st.text_input("Department / Domain", value=default_dept)
        with c_exp:
            min_exp = st.number_input("Minimum Experience (Years)", min_value=0.0, max_value=20.0, value=float(default_exp), step=0.5)

        jd_text = st.text_area("Full Job Description & Responsibilities", value=default_text, height=220)

        # Parse JD button
        parsed_jd = parser.parse(jd_text, title_hint=job_title)
        parsed_jd["min_experience_years"] = min_exp
        st.session_state["current_jd"] = parsed_jd

        st.markdown("**Detected Required Skills from JD:**")
        req_chips = " ".join([f"<span class='badge-matched'>{s}</span>" for s in parsed_jd["required_skills"]])
        st.markdown(req_chips if req_chips else "_No specific skills detected in text._", unsafe_allow_html=True)

        if st.button("💾 Save Job to Database", type="secondary"):
            new_id = db.create_job(
                title=job_title,
                department=department,
                min_experience=min_exp,
                required_skills=parsed_jd["required_skills"],
                preferred_skills=parsed_jd["preferred_skills"],
                description_text=jd_text
            )
            st.success(f"Job Description saved successfully (ID: #{new_id})!")

    with col2:
        st.subheader("2. Hybrid Scoring Weights")
        st.caption("Customize the importance of each evaluation dimension:")

        w_skills = st.slider("Technical Skills Match (%)", 0, 100, 35, step=5)
        w_sem = st.slider("Semantic Context Match (%)", 0, 100, 20, step=5)
        w_exp = st.slider("Experience Alignment (%)", 0, 100, 15, step=5)
        w_edu = st.slider("Education Credentials (%)", 0, 100, 10, step=5)
        w_proj = st.slider("Project Depth & Tech Stack (%)", 0, 100, 10, step=5)
        w_cert = st.slider("Industry Certifications (%)", 0, 100, 5, step=5)
        w_qual = st.slider("Resume ATS Quality / Impact (%)", 0, 100, 5, step=5)

        total_w = w_skills + w_sem + w_exp + w_edu + w_proj + w_cert + w_qual
        if total_w != 100:
            st.warning(f"⚠️ Total weights equal {total_w}% (Will be automatically normalized to 100%)")
        else:
            st.success("✓ Total weights perfectly equal 100%")

        st.session_state["weights"] = {
            "technical_skills": w_skills / 100.0,
            "semantic_jd": w_sem / 100.0,
            "experience": w_exp / 100.0,
            "education": w_edu / 100.0,
            "projects": w_proj / 100.0,
            "certifications": w_cert / 100.0,
            "resume_quality": w_qual / 100.0
        }

    st.markdown("---")
    st.subheader("3. Candidate Resumes Upload")
    st.markdown("Upload candidate resumes in **PDF** (text & scanned OCR), **DOCX**, or **TXT** format.")

    c_up, c_btn = st.columns([2, 1], gap="medium")
    with c_up:
        uploaded_files = st.file_uploader(
            "Upload Resumes (Multi-file select supported)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        if uploaded_files:
            st.session_state["uploaded_raw_files"] = uploaded_files
            st.info(f"📁 {len(uploaded_files)} resumes ready for processing.")

    with c_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Load Built-in Benchmark Resumes", use_container_width=True):
            st.session_state["load_sample_resumes"] = True
            st.rerun()

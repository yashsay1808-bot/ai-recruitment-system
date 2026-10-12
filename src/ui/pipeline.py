"""
Screening pipeline shared by the main app and the multi-page modules:
parse resumes (cached) -> quality scores -> hybrid ranking -> explainable-AI rationale.
"""

import os
import glob
import streamlit as st

from src.core.resume_parser import ResumeParser
from src.core.hybrid_ranker import HybridRanker
from src.core.explainable_ai import ExplainableAI
from src.core.quality_analyzer import ResumeQualityAnalyzer


@st.cache_data(show_spinner=False, max_entries=256)
def _parse_resume_cached(file_bytes: bytes, file_name: str):
    """Parsing (PDF/DOCX/OCR) is pure and costly; reuse results across reruns and sessions."""
    return ResumeParser().parse(file_bytes, file_name)


def process_and_rank_resumes():
    """Parses, evaluates, and ranks all active candidate resumes against the current JD."""
    resume_parser: ResumeParser = st.session_state["resume_parser"]
    hybrid_ranker: HybridRanker = st.session_state["hybrid_ranker"]
    xai_engine: ExplainableAI = st.session_state["xai_engine"]
    qa_engine: ResumeQualityAnalyzer = st.session_state["quality_analyzer"]
    current_jd = st.session_state["current_jd"]
    weights = st.session_state.get("weights", HybridRanker.DEFAULT_WEIGHTS)

    hybrid_ranker.weights = weights

    raw_candidates = []

    # 1. Check if user uploaded files
    uploaded_files = st.session_state.get("uploaded_raw_files", [])
    if uploaded_files:
        for f in uploaded_files:
            file_bytes = f.read()
            f.seek(0)
            parsed = _parse_resume_cached(file_bytes, f.name)
            raw_candidates.append(parsed)

    # 2. Check if sample resumes are loaded
    if st.session_state.get("load_sample_resumes", False) or (not raw_candidates and not uploaded_files):
        sample_files = glob.glob("data/sample_resumes/*.*")
        for s_path in sample_files:
            fname = os.path.basename(s_path)
            with open(s_path, "rb") as fp:
                b = fp.read()
                parsed = _parse_resume_cached(b, fname)
                raw_candidates.append(parsed)
        st.session_state["load_sample_resumes"] = False

    st.session_state["parsed_candidates"] = raw_candidates

    # 3. Compute Quality Scores
    quality_scores = {}
    for cand in raw_candidates:
        q_res = qa_engine.analyze(cand, current_jd.get("required_skills", []))
        quality_scores[cand["file_name"]] = q_res["quality_score"]

    # 4. Rank Candidates
    ranked = hybrid_ranker.rank_all_candidates(raw_candidates, current_jd, quality_scores)

    # 5. Enrich with Explainable AI (XAI)
    for cand in ranked:
        cand["explanation"] = xai_engine.generate_explanation(cand, current_jd)

    st.session_state["ranked_candidates"] = ranked
    if ranked:
        st.session_state["selected_candidate"] = ranked[0]

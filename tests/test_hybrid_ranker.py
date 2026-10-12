"""
Unit tests for Hybrid Multi-Score Ranking and Explainable AI.
"""

import pytest
from src.core.hybrid_ranker import HybridRanker
from src.core.explainable_ai import ExplainableAI


def test_hybrid_scoring_and_explanation():
    ranker = HybridRanker()
    xai = ExplainableAI()

    candidate_data = {
        "candidate_name": "Rahul Nair",
        "file_name": "rahul_nair.pdf",
        "raw_text": "Machine learning engineer with Python, PyTorch, BERT, Scikit-Learn, Docker, AWS.",
        "skills": ["Python", "Machine Learning", "Deep Learning", "Natural Language Processing", "PyTorch", "Scikit-Learn", "Docker", "AWS"],
        "education": {
            "degree": "B.E. / B.Tech",
            "branch": "Information Science & Engineering",
            "cgpa": "8.9"
        },
        "experience": {
            "years_of_experience": 2.5,
            "is_fresher": False
        },
        "projects": [
            {"title": "ATS Resume Screening", "skills_used": ["Python", "Machine Learning", "NLP"]}
        ],
        "certifications": ["AWS Certified Machine Learning"]
    }

    jd_data = {
        "job_title": "Machine Learning Engineer",
        "required_skills": ["Python", "Machine Learning", "Natural Language Processing", "Docker", "AWS", "FastAPI"],
        "preferred_skills": ["Kubernetes"],
        "min_experience_years": 2.0,
        "preferred_degrees": ["B.E. / B.Tech"],
        "raw_text": "We are seeking a Machine Learning Engineer with Python, NLP, Docker, AWS experience."
    }

    eval_res = ranker.evaluate_candidate(candidate_data, jd_data, quality_score=85.0)
    
    assert eval_res["overall_score"] >= 75.0
    assert eval_res["breakdown"]["technical_skills"] >= 80.0
    assert eval_res["breakdown"]["experience"] >= 85.0

    explanation = xai.generate_explanation(eval_res, jd_data)
    assert explanation["status_key"] in ["STRONGLY_RECOMMENDED", "RECOMMENDED"]
    assert len(explanation["strengths"]) > 0
    assert len(explanation["reasons"]) > 0

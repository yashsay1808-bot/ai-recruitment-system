"""
Unit tests for Resume Parser and Section Extraction.
"""

import pytest
from src.core.resume_parser import ResumeParser


def test_resume_parser_with_text():
    sample_text = """Rahul Nair
Email: rahul.nair@email.com
Phone: +91 98450 12345
Location: Bengaluru, India
LinkedIn: https://linkedin.com/in/rahul-nair-ml
GitHub: https://github.com/rahulnair-ai

PROFESSIONAL SUMMARY
Machine Learning Engineer with 2.5 years of experience building NLP models and FastAPI services.

TECHNICAL SKILLS
Python, Machine Learning, Deep Learning, Natural Language Processing, PyTorch, Scikit-Learn, Docker, AWS

EDUCATION
B.E. in Information Science & Engineering
VTU Bengaluru | CGPA: 8.9/10 | Graduated: 2022

WORK EXPERIENCE
Machine Learning Engineer | ThoughtWorks (Jan 2023 - Present)
• Built BERT pipeline boosting accuracy by 28%.
• Engineered FastAPI microservices serving 50,000 daily requests.

KEY PROJECTS
ATS Resume Screening Engine
• Built hybrid ranking engine with SentenceTransformers and FastAPI.
"""
    parser = ResumeParser()
    parsed = parser.parse(sample_text.encode('utf-8'), "rahul_nair.txt")

    assert parsed["candidate_name"] == "Rahul Nair"
    assert parsed["email"] == "rahul.nair@email.com"
    assert "98450" in parsed["phone"]
    assert "Bengaluru" in parsed["location"]
    assert "Python" in parsed["skills"]
    assert "Machine Learning" in parsed["skills"]
    assert parsed["education"]["degree"] == "B.E. / B.Tech"
    assert parsed["experience"]["years_of_experience"] >= 1.5
    assert len(parsed["projects"]) >= 1

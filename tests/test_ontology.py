"""
Unit tests for Skill Ontology and Synonym Normalization Engine.
"""

import pytest
from src.core.skill_ontology import (
    normalize_skill,
    get_skill_category,
    extract_skills_from_text,
    match_skills
)


def test_synonym_normalization():
    assert normalize_skill("python 3") == "Python"
    assert normalize_skill("ml") == "Machine Learning"
    assert normalize_skill("deep learning") == "Deep Learning"
    assert normalize_skill("sklearn") == "Scikit-Learn"
    assert normalize_skill("nlp") == "Natural Language Processing"
    assert normalize_skill("js") == "JavaScript"
    assert normalize_skill("react.js") == "React"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("aws") == "AWS"
    assert normalize_skill("dbms") == "DBMS"


def test_extract_skills_from_free_text():
    sample_text = "Proficient in Python, building ML and NLP pipelines with scikit-learn and PyTorch. Deployed with Docker on AWS."
    skills = extract_skills_from_text(sample_text)
    
    assert "Python" in skills
    assert "Machine Learning" in skills
    assert "Natural Language Processing" in skills
    assert "Scikit-Learn" in skills
    assert "PyTorch" in skills
    assert "Docker" in skills
    assert "AWS" in skills


def test_skill_gap_matching():
    jd_skills = ["Python", "Machine Learning", "FastAPI", "Docker", "AWS"]
    resume_skills = ["Python", "Machine Learning", "Flask", "Docker"]
    
    result = match_skills(jd_skills, resume_skills)
    
    assert "Python" in result["matched"]
    assert "Machine Learning" in result["matched"]
    assert "Docker" in result["matched"]
    assert "AWS" in result["missing"]
    
    # FastAPI and Flask should partially match because both are Web Frameworks
    part_skills = [p["required_skill"] for p in result["partially_matched"]]
    assert "FastAPI" in part_skills
    assert result["match_percentage"] > 60.0

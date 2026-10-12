"""
Unit tests for AI Recruiter Chatbot Engine.
"""

import pytest
from src.core.recruiter_chatbot import RecruiterChatbot


def test_recruiter_chatbot_queries():
    chatbot = RecruiterChatbot()

    current_jd = {
        "job_title": "Machine Learning Engineer",
        "required_skills": ["Python", "Machine Learning", "Docker", "AWS"],
        "min_experience_years": 2.0
    }

    ranked_candidates = [
        {
            "rank": 1,
            "candidate_name": "Rahul Nair",
            "overall_score": 90.3,
            "breakdown": {"technical_skills": 94.0, "semantic_jd": 91.0},
            "gap_results": {
                "matched_skills": ["Python", "Machine Learning", "Docker"],
                "missing_skills": ["AWS"]
            },
            "candidate_data": {
                "experience": {"years_of_experience": 2.5},
                "education": {"degree": "B.E.", "branch": "ISE", "cgpa": "8.9"}
            },
            "explanation": {
                "status_label": "🟢 Strongly Recommended",
                "executive_summary": "Strong fit across ML and Python."
            }
        },
        {
            "rank": 2,
            "candidate_name": "Aarav Sharma",
            "overall_score": 82.5,
            "breakdown": {"technical_skills": 85.0, "semantic_jd": 80.0},
            "gap_results": {
                "matched_skills": ["Python", "Docker"],
                "missing_skills": ["Machine Learning", "AWS"]
            },
            "candidate_data": {
                "experience": {"years_of_experience": 1.5},
                "education": {"degree": "B.E.", "branch": "CSE", "cgpa": "8.2"}
            },
            "explanation": {
                "status_label": "🟢 Recommended",
                "executive_summary": "Good backend candidate."
            }
        }
    ]

    # Test 1: Top Candidate Query
    res_top = chatbot.answer_query("Who is the top candidate?", ranked_candidates, current_jd)
    assert "Rahul Nair" in res_top
    assert "90.3%" in res_top

    # Test 2: Comparison Query
    res_comp = chatbot.answer_query("Compare Rahul Nair and Aarav Sharma", ranked_candidates, current_jd)
    assert "Rahul Nair" in res_comp
    assert "Aarav Sharma" in res_comp

    # Test 3: Missing Skills Query
    res_gaps = chatbot.answer_query("What are the missing skills?", ranked_candidates, current_jd)
    assert "AWS" in res_gaps

    # Test 4: Experience Query
    res_exp = chatbot.answer_query("Show candidates with 2 years of experience", ranked_candidates, current_jd)
    assert "Rahul Nair" in res_exp

    # Test 5: Interview Questions Query
    res_interview = chatbot.answer_query("Give interview questions for the top candidate", ranked_candidates, current_jd)
    assert "Technical Question" in res_interview

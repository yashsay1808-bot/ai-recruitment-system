"""Tests for the Multi-Agent Recruiter Council (offline mode, plus a stubbed LLM)."""

from src.core.agentic_council import RecruitmentCouncil

JD = {"job_title": "Software Engineer", "required_skills": ["Python", "Docker", "AWS"],
      "preferred_skills": [], "min_experience_years": 2}

STRONG = {
    "candidate_name": "Jane Roe",
    "skills": ["Python", "Docker", "AWS", "Kafka"],
    "experience": {"years_of_experience": 0, "detected_titles": []},
    "sections": {"experience": "Software Engineer | Acme (Jan 2019 - Mar 2020)\n"
                               "Senior Software Engineer | Beta (Apr 2020 - Nov 2022)\n"
                               "Staff Engineer | Gamma (Jan 2023 - Present)\nB.Tech 2015 - 2019"},
    "projects": [{"title": "Platform", "description": "Led migration to microservices on Kubernetes serving 2M users, "
                                                      "cut latency by 40% with Redis caching, deployed on AWS.",
                  "skills_used": ["Docker"]}],
    "raw_text": "Jane Roe jane@x.com +91 98765 43210 DOB: 01/01/1990\nLed team, mentored, architected microservices, kafka, "
                "pytest, CI/CD, 40% faster, owned roadmap, designed systems. Python Docker AWS",
}


def test_scorecards_and_consensus_shape():
    out = RecruitmentCouncil(use_llm=False).evaluate_candidate_council(STRONG, JD)
    assert set(out["agent_scorecards"]) == {"tech_lead", "culture_retention", "fair_auditor", "seniority_comp"}
    for card in out["agent_scorecards"].values():
        assert 0 <= card["score"] <= 100
        assert {"observations", "strengths", "concerns"} <= set(card)
    ec = out["executive_consensus"]
    assert ec["verdict"] in {"STRONG_HIRE", "HIRE", "LEAN_HIRE", "REJECT"}
    assert ec["reasoning"] and ec["reasoning_markdown"].startswith("- ")
    assert out["meta"]["mode"] == "local"


def test_protected_fields_flagged_but_not_scored():
    out = RecruitmentCouncil(use_llm=False).evaluate_candidate_council(STRONG, JD)
    assert "date of birth / age" in out["agent_scorecards"]["fair_auditor"]["metrics"]["protected_fields_in_resume"]


def test_missing_required_skills_cannot_hire():
    weak = {"candidate_name": "X", "skills": ["Excel"], "raw_text": "Excel user " * 30, "experience": {"years_of_experience": 5}}
    ec = RecruitmentCouncil(use_llm=False).evaluate_candidate_council(weak, JD)["executive_consensus"]
    assert ec["verdict"] == "REJECT"


def test_leveling_and_comp_bands():
    sen = RecruitmentCouncil(use_llm=False).evaluate_candidate_council(STRONG, JD)["agent_scorecards"]["seniority_comp"]
    comp = sen["metrics"]["compensation"]
    assert comp["level"] in {"L3", "L4", "L5", "L6"}
    assert comp["usd"]["min"] < comp["usd"]["max"] and comp["inr"]["min_lpa"] < comp["inr"]["max_lpa"]


def test_llm_bias_text_is_audited_and_score_nudge_is_bounded():
    council = RecruitmentCouncil(use_llm=True, llm_provider="gemini", api_key="dummy")
    prompts = []

    def fake(system, user):
        prompts.append(user)
        if "narrative" in user:
            return {"narrative": "ok"}
        return {"observations": ["She seems young and energetic"], "strengths": [], "concerns": [],
                "score_adjustment": 99, "rationale": "r"}

    council.llm.complete_json = fake
    out = council.evaluate_candidate_council(STRONG, JD)
    cats = {f["category"] for f in out["agent_scorecards"]["fair_auditor"]["metrics"]["bias_flags"]}
    assert {"age", "gender"} <= cats
    assert out["agent_scorecards"]["tech_lead"]["metrics"]["llm_score_adjustment"] == 10
    assert out["executive_consensus"]["human_review_required"] is True
    joined = " ".join(prompts)
    assert "Jane" not in joined and "jane@x.com" not in joined and "98765" not in joined


def test_llm_failure_falls_back_silently():
    council = RecruitmentCouncil(use_llm=True, llm_provider="openai", api_key="dummy", llm_timeout=0.01)
    council.llm._post = lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
    out = council.evaluate_candidate_council(STRONG, JD)
    assert out["meta"]["llm_used"] is False and out["meta"]["llm_errors"]
    assert out["executive_consensus"]["verdict"]

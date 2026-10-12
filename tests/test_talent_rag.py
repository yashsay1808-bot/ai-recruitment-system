"""Tests for hybrid talent search (TF-IDF dense backend so no model download is needed)."""

from src.core.talent_rag import TalentRAG


def _resume(name, years, skills, exp, projects=()):
    return {"candidate_name": name, "skills": skills,
            "experience": {"years_of_experience": years, "detected_titles": []},
            "sections": {"experience": exp},
            "projects": [{"title": t, "description": d, "skills_used": []} for t, d in projects]}


POOL = [
    _resume("Dist Dev", 5, ["Python", "Docker", "AWS"],
            "Senior Backend Engineer | Acme (2020 - Present)\n• Designed distributed systems with Kafka and gRPC across 12 microservices.\n"
            "• Deployed services to AWS EKS with Docker.", [("Orders", "Event-driven microservices deployed on AWS ECS with Docker.")]),
    _resume("Frontend Fan", 1, ["React", "HTML"], "Frontend Intern | Foo (2025 - Present)\n• Built React landing pages."),
    _resume("Docker Junior", 2, ["Docker", "Python"], "Software Engineer | Bar (2024 - Present)\n• Containerized Flask apps and deployed on AWS EC2."),
]
QUERY = "Find engineers with 3+ years in distributed systems who know Docker and deployed microservices on AWS"


def test_query_plan_extracts_experience_and_competencies():
    plan = TalentRAG(embedding_backend="tfidf").parse_query(QUERY)
    names = {c.name for c in plan.competencies}
    assert plan.min_years == 3.0
    assert {"distributed systems", "docker", "microservices", "aws", "deployment"} <= names


def test_best_candidate_ranks_first_with_explanations():
    hits = TalentRAG(embedding_backend="tfidf").search_talent_pool(QUERY, POOL, top_k=3)
    assert hits[0]["candidate_name"] == "Dist Dev" and hits[0]["rank"] == 1
    assert hits[0]["missing_competencies"] == [] and hits[0]["meets_experience_requirement"] is True
    snippet = hits[0]["snippets"][0]
    assert "**" in snippet["markdown"] and "<mark>" in snippet["html"]
    assert hits[0]["relevance_score"] > hits[-1]["relevance_score"]


def test_experience_filter_and_irrelevant_query():
    rag = TalentRAG(embedding_backend="tfidf")
    strict = rag.search_talent_pool(QUERY, POOL, top_k=5, strict_experience=True)
    assert [h["candidate_name"] for h in strict] == ["Dist Dev"]
    assert rag.search_talent_pool("blockchain solidity smart contracts", POOL) == []
    assert rag.search_talent_pool("docker", []) == [] and rag.search_talent_pool("  ", POOL) == []


def test_index_is_cached_between_queries():
    rag = TalentRAG(embedding_backend="tfidf")
    assert rag.build_index(POOL) is rag.build_index(list(POOL))

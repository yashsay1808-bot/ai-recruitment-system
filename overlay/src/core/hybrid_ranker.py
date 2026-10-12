"""
Hybrid AI Multi-Score Ranking Engine
Combines multiple evaluation dimensions into an explainable, weighted ranking:
- Technical Skill Match (35%)
- Semantic JD Context Match (20%) - Dense Transformer / TF-IDF Vector Embeddings
- Experience Match (15%)
- Education Match (10%)
- Project Match (10%)
- Certification Match (5%)
- Resume Quality / Completeness (5%)
"""

import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.core.gap_analyzer import SkillGapAnalyzer

# Optional SentenceTransformer for dense embeddings
_SENTENCE_MODEL = None
_MODEL_TRIED = False

def get_sentence_transformer():
    """Lazy load SentenceTransformer for fast startup."""
    global _SENTENCE_MODEL, _MODEL_TRIED
    if not _MODEL_TRIED:
        _MODEL_TRIED = True
        try:
            from sentence_transformers import SentenceTransformer
            # Fast, lightweight high-accuracy model
            _SENTENCE_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Dense embedding model notice (using high-speed TF-IDF fallback): {e}")
            _SENTENCE_MODEL = None
    return _SENTENCE_MODEL


class HybridRanker:
    """Multi-dimensional candidate scoring and ranking engine."""

    DEFAULT_WEIGHTS = {
        "technical_skills": 0.35,
        "semantic_jd": 0.20,
        "experience": 0.15,
        "education": 0.10,
        "projects": 0.10,
        "certifications": 0.05,
        "resume_quality": 0.05
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.gap_analyzer = SkillGapAnalyzer()

    def compute_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Computes dense semantic or TF-IDF cosine similarity between resume and JD.
        Returns score scaled 0 - 100.
        """
        if not resume_text or not jd_text:
            return 0.0

        model = get_sentence_transformer()
        if model is not None:
            try:
                embeddings = model.encode([resume_text[:2000], jd_text[:2000]])
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                # Scale semantic similarity from typical 0.3-0.8 range to 0-100
                scaled = max(0.0, min(100.0, float(sim) * 100.0))
                return round(scaled, 1)
            except Exception:
                pass

        # TF-IDF fallback
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=3000)
            matrix = vectorizer.fit_transform([resume_text, jd_text])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            # TF-IDF cosine similarity for documents typically tops out around 0.5-0.7; boost linearly
            scaled = max(0.0, min(100.0, float(sim) * 150.0))
            return round(scaled, 1)
        except Exception:
            return 50.0

    def compute_experience_score(self, cand_exp: Dict[str, Any], min_required_years: float) -> float:
        """Evaluates candidate years of experience against JD requirement."""
        cand_years = cand_exp.get("years_of_experience", 0.0)

        if min_required_years <= 0.0:
            # Fresher or unspecified requirement
            return 90.0 if cand_years > 0 else 80.0

        if cand_years >= min_required_years:
            # Full match with extra bonus for strong background
            surplus = cand_years - min_required_years
            score = 85.0 + min(15.0, surplus * 5.0)
            return round(score, 1)
        else:
            # Partial match based on ratio
            ratio = cand_years / min_required_years
            score = max(25.0, ratio * 80.0)
            return round(score, 1)

    def compute_education_score(self, cand_edu: Dict[str, Any], preferred_degrees: List[str]) -> float:
        """Evaluates degree level, field relevance, and academic score."""
        degree = cand_edu.get("degree", "").lower()
        branch = cand_edu.get("branch", "").lower()
        cgpa_str = str(cand_edu.get("cgpa", "N/A"))

        base_score = 75.0
        
        # Degree level
        if "high school" in degree or "secondary" in degree:
            base_score = 45.0
        elif "ph.d." in degree:
            base_score = 100.0
        elif "m.e." in degree or "m.tech" in degree or "m.s." in degree or "master" in degree:
            base_score = 95.0
        elif "b.e." in degree or "b.tech" in degree or "bachelor" in degree:
            base_score = 88.0
        elif "bca" in degree or "mca" in degree:
            base_score = 85.0

        # Branch relevance bonus
        if any(b in branch for b in ["computer", "information", "ai", "data science", "electronics"]):
            base_score += 5.0

        # CGPA bonus
        try:
            cgpa_val = float(cgpa_str)
            if cgpa_val >= 8.5 or cgpa_val >= 85.0:
                base_score += 7.0
            elif cgpa_val >= 7.5 or cgpa_val >= 75.0:
                base_score += 3.0
        except ValueError:
            pass

        return round(min(100.0, base_score), 1)

    def compute_project_score(self, cand_projects: List[Dict[str, Any]], jd_skills: List[str]) -> float:
        """Evaluates relevance and depth of practical candidate projects."""
        if not cand_projects:
            return 40.0

        project_count = len(cand_projects)
        base = min(60.0, 30.0 + project_count * 15.0)

        # Tech stack alignment in projects
        all_proj_skills = set()
        for p in cand_projects:
            for s in p.get("skills_used", []):
                all_proj_skills.add(s)

        matched_in_projects = [s for s in jd_skills if s in all_proj_skills]
        if jd_skills:
            alignment_ratio = len(matched_in_projects) / len(jd_skills)
            alignment_bonus = alignment_ratio * 40.0
        else:
            alignment_bonus = 20.0

        score = base + alignment_bonus
        return round(min(100.0, max(20.0, score)), 1)

    def compute_certification_score(self, certs: List[str], jd_skills: List[str]) -> float:
        """Evaluates industry recognized certifications."""
        if not certs:
            return 40.0  # Neutral baseline
        
        count = len(certs)
        score = min(100.0, 60.0 + count * 15.0)
        return round(score, 1)

    def evaluate_candidate(
        self,
        candidate_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        quality_score: float = 75.0
    ) -> Dict[str, Any]:
        """
        Executes full hybrid multi-score evaluation for a single candidate against a Job Description.
        """
        jd_skills = jd_data.get("required_skills", [])
        cand_skills = candidate_data.get("skills", [])
        
        # 1. Skill Gap Analysis
        gap_results = self.gap_analyzer.analyze(jd_skills, cand_skills)
        skill_score = gap_results["match_percentage"]

        # 2. Semantic JD Relevance
        semantic_score = self.compute_semantic_similarity(
            candidate_data.get("raw_text", ""),
            jd_data.get("raw_text", "")
        )

        # 3. Experience Match
        exp_score = self.compute_experience_score(
            candidate_data.get("experience", {}),
            jd_data.get("min_experience_years", 0.0)
        )

        # 4. Education Match
        edu_score = self.compute_education_score(
            candidate_data.get("education", {}),
            jd_data.get("preferred_degrees", [])
        )

        # 5. Project Relevance
        proj_score = self.compute_project_score(
            candidate_data.get("projects", []),
            jd_skills
        )

        # 6. Certification Match
        cert_score = self.compute_certification_score(
            candidate_data.get("certifications", []),
            jd_skills
        )

        # 7. Weighted Overall Score
        w = self.weights
        total_weight = sum(w.values())
        norm_w = {k: v / total_weight for k, v in w.items()}

        overall_score = (
            skill_score * norm_w.get("technical_skills", 0.35) +
            semantic_score * norm_w.get("semantic_jd", 0.20) +
            exp_score * norm_w.get("experience", 0.15) +
            edu_score * norm_w.get("education", 0.10) +
            proj_score * norm_w.get("projects", 0.10) +
            cert_score * norm_w.get("certifications", 0.05) +
            quality_score * norm_w.get("resume_quality", 0.05)
        )
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)

        breakdown = {
            "overall_score": overall_score,
            "technical_skills": skill_score,
            "semantic_jd": semantic_score,
            "experience": exp_score,
            "education": edu_score,
            "projects": proj_score,
            "certifications": cert_score,
            "resume_quality": round(quality_score, 1)
        }

        return {
            "candidate_name": candidate_data.get("candidate_name", "Candidate"),
            "file_name": candidate_data.get("file_name", ""),
            "overall_score": overall_score,
            "breakdown": breakdown,
            "gap_results": gap_results,
            "candidate_data": candidate_data,
            "weights_used": norm_w
        }

    def rank_all_candidates(
        self,
        candidates_list: List[Dict[str, Any]],
        jd_data: Dict[str, Any],
        quality_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Evaluates and ranks a batch of candidates in descending order of overall score."""
        results = []
        quality_scores = quality_scores or {}

        for cand in candidates_list:
            fname = cand.get("file_name", "")
            q_score = quality_scores.get(fname, 75.0)
            eval_res = self.evaluate_candidate(cand, jd_data, q_score)
            results.append(eval_res)

        # Sort by overall score descending
        ranked = sorted(results, key=lambda x: x["overall_score"], reverse=True)
        
        # Add rank position
        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked

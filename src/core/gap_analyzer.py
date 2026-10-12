"""
Skill Gap Analysis Engine
Computes granular skill intersections between Job Descriptions and Candidate profiles:
- Matched Skills (Full exact or synonym match)
- Partially Matched Skills (Semantic domain overlap)
- Missing Skills (Required by JD but missing in Resume)
- Competency distribution across domains (Languages, ML, Cloud, Web, DB)
"""

from typing import Dict, List, Any
from src.core.skill_ontology import match_skills, get_skill_category


class SkillGapAnalyzer:
    """Performs deep skill gap assessment and category coverage breakdown."""

    def analyze(self, jd_skills: List[str], candidate_skills: List[str]) -> Dict[str, Any]:
        """
        Calculates skill match breakdown and categorical coverage.
        """
        match_result = match_skills(jd_skills, candidate_skills)

        # Categorize matched, partial, missing skills
        category_breakdown = {}
        
        all_analyzed = (
            [(s, "matched") for s in match_result["matched"]] +
            [(p["required_skill"], "partial") for p in match_result["partially_matched"]] +
            [(s, "missing") for s in match_result["missing"]]
        )

        for skill, status in all_analyzed:
            cat = get_skill_category(skill)
            if cat not in category_breakdown:
                category_breakdown[cat] = {"matched": 0, "partial": 0, "missing": 0, "total": 0}
            category_breakdown[cat][status] += 1
            category_breakdown[cat]["total"] += 1

        # Calculate category match percentages
        category_scores = {}
        for cat, data in category_breakdown.items():
            if data["total"] > 0:
                score = ((data["matched"] * 1.0 + data["partial"] * 0.5) / data["total"]) * 100
                category_scores[cat] = round(score, 1)

        return {
            "matched_skills": match_result["matched"],
            "partially_matched_skills": match_result["partially_matched"],
            "missing_skills": match_result["missing"],
            "total_required": match_result["total_required"],
            "matched_count": len(match_result["matched"]),
            "partial_count": len(match_result["partially_matched"]),
            "missing_count": len(match_result["missing"]),
            "match_percentage": match_result["match_percentage"],
            "category_breakdown": category_breakdown,
            "category_scores": category_scores
        }

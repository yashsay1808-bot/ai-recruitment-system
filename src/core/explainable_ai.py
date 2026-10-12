"""
Explainable AI (XAI) & Recommendation Engine
Provides transparent, interpretable explanations for candidate scores:
- Structured reasoning breakdown (Skills, Experience, Education, Projects, Gaps)
- Key Strengths & Growth Areas
- Categorized Recommendation status:
  - 🟢 Strongly Recommended
  - 🟢 Recommended
  - 🟡 HR Review
  - 🔴 Not Recommended
"""

from typing import Dict, List, Any


class ExplainableAI:
    """Generates human-understandable AI rationale and actionable recruiter recommendations."""

    RECOMMENDATION_TIERS = [
        (80.0, "STRONGLY_RECOMMENDED", "🟢 Strongly Recommended", "Excellent fit across technical skills, practical projects, and core requirements."),
        (65.0, "RECOMMENDED", "🟢 Recommended", "Good fit with strong fundamentals; minor skill gaps can be addressed via onboarding."),
        (50.0, "HR_REVIEW", "🟡 HR Review", "Moderate alignment; candidate meets foundational criteria but lacks key core competencies."),
        (0.0, "NOT_RECOMMENDED", "🔴 Not Recommended", "Low alignment with critical job requirements and required tech stack.")
    ]

    def generate_explanation(self, eval_result: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produces detailed explainability cards, rationale bullet points,
        and recommendation status for an evaluated candidate.
        """
        cand_data = eval_result["candidate_data"]
        breakdown = eval_result["breakdown"]
        gap = eval_result["gap_results"]
        overall_score = eval_result["overall_score"]

        # 1. Determine Recommendation Status
        status_key = "NOT_RECOMMENDED"
        status_label = "🔴 Not Recommended"
        status_desc = ""

        for threshold, key, label, desc in self.RECOMMENDATION_TIERS:
            if overall_score >= threshold:
                status_key = key
                status_label = label
                status_desc = desc
                break

        # 2. Key Strengths
        strengths: List[str] = []
        warnings: List[str] = []
        reasons: List[str] = []

        # Technical Skills Rationale
        matched_count = gap.get("matched_count", 0)
        total_req = gap.get("total_required", 0)
        if total_req > 0:
            reasons.append(f"Matched {matched_count}/{total_req} required technical skills ({gap['match_percentage']}% coverage).")
            if gap["match_percentage"] >= 75:
                top_matched = ", ".join(gap["matched_skills"][:4])
                strengths.append(f"Strong competency in primary required skills: {top_matched}.")
            elif gap["match_percentage"] < 50:
                warnings.append(f"Matches fewer than half of target skills ({matched_count}/{total_req}).")

        # Experience Rationale
        exp_years = cand_data.get("experience", {}).get("years_of_experience", 0.0)
        min_exp = jd_data.get("min_experience_years", 0.0)
        if min_exp > 0:
            if exp_years >= min_exp:
                reasons.append(f"{exp_years} years of relevant experience meets or exceeds the required {min_exp} years.")
                strengths.append(f"Sufficient industry experience ({exp_years} yrs vs {min_exp} yrs required).")
            else:
                reasons.append(f"{exp_years} years of experience is below the required {min_exp} years.")
                warnings.append(f"Experience shortfall: Candidate has {exp_years} yrs (Required: {min_exp} yrs).")
        else:
            reasons.append(f"{exp_years} years of experience detected.")

        # Education Rationale
        edu = cand_data.get("education", {})
        deg = edu.get("degree", "Degree")
        branch = edu.get("branch", "Engineering")
        reasons.append(f"{deg} in {branch} satisfies education criteria.")

        # Projects Rationale
        projects = cand_data.get("projects", [])
        if projects:
            reasons.append(f"{len(projects)} hands-on practical projects detected in resume.")
            if breakdown["projects"] >= 80:
                strengths.append("High project tech-stack alignment with target job description.")
        else:
            warnings.append("No explicit practical projects section found.")

        # Missing Skills Warnings
        missing = gap.get("missing_skills", [])
        if missing:
            top_missing = ", ".join(missing[:4])
            reasons.append(f"Identified missing competencies: {top_missing}.")
            warnings.append(f"Missing required skills: {top_missing}.")

        # Partial Matches Rationale
        partials = gap.get("partially_matched_skills", [])
        if partials:
            p_summary = ", ".join([f"{p['related_candidate_skill']} (related to {p['required_skill']})" for p in partials[:2]])
            reasons.append(f"Partial domain skills: {p_summary}.")

        # 3. Formulate Executive Summary
        cand_name = eval_result["candidate_name"]
        if status_key in ["STRONGLY_RECOMMENDED", "RECOMMENDED"]:
            exec_summary = (
                f"{cand_name} demonstrates high suitability ({overall_score}%) with strong domain "
                f"competencies in {', '.join(gap['matched_skills'][:3]) or 'core areas'}. "
                f"{'Some skills like ' + ', '.join(missing[:2]) + ' may require minor upskilling.' if missing else 'All key criteria fully satisfied.'}"
            )
        elif status_key == "HR_REVIEW":
            exec_summary = (
                f"{cand_name} scored {overall_score}% and shows potential in foundational technical areas, "
                f"but has notable gaps in {', '.join(missing[:3]) if missing else 'experience/projects'}. Suitable for secondary review or junior alignment."
            )
        else:
            exec_summary = (
                f"{cand_name} scored {overall_score}%, showing limited alignment with the core requirements "
                f"of this role. Missing {len(missing)} essential technical competencies."
            )

        return {
            "status_key": status_key,
            "status_label": status_label,
            "status_description": status_desc,
            "executive_summary": exec_summary,
            "reasons": reasons,
            "strengths": strengths,
            "warnings": warnings,
            "score_breakdown": breakdown
        }

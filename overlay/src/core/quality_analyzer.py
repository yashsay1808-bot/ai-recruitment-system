"""
Resume Quality & ATS Compatibility Analyzer
Evaluates resume formatting, section completeness, quantified metrics,
action verbs, contact hygiene, and generates actionable improvement suggestions.
"""

import re
from datetime import datetime
from typing import Dict, List, Any


class ResumeQualityAnalyzer:
    """Evaluates ATS compliance, readability, and content strength."""

    ACTION_VERBS = [
        "developed", "built", "engineered", "designed", "implemented", "optimized",
        "reduced", "increased", "accelerated", "deployed", "scaled", "architected",
        "created", "automated", "spearheaded", "integrated", "delivered", "led", "managed"
    ]

    QUANTIFIABLE_PATTERN = re.compile(
        r'(\b\d+%\b|\b\d+\s*percent\b|\$\d+|\b\d+\s*x\b|\b\d+\+?\s*(?:users|clients|requests|ms|seconds|minutes|hours|days|tb|gb|mb|queries|dollars))',
        re.IGNORECASE
    )

    def analyze(self, parsed_resume: Dict[str, Any], jd_skills: List[str] = None) -> Dict[str, Any]:
        """
        Calculates ATS quality score (0 - 100), lists strengths, weaknesses,
        and generates personalized resume improvement recommendations.
        """
        raw_text = parsed_resume.get("raw_text", "")
        sections = parsed_resume.get("sections", {})
        words = raw_text.split()
        word_count = len(words)

        score = 0.0
        good_points: List[str] = []
        improvements: List[str] = []
        suggestions: List[str] = []

        # 1. Contact Information Hygiene (Max 20 pts)
        contact_pts = 0
        if parsed_resume.get("email") and parsed_resume.get("email") != "Not Provided":
            contact_pts += 6
            good_points.append("✓ Professional email address detected.")
        else:
            improvements.append("⚠ Missing or unparseable email address.")
            suggestions.append("Add a clear email address at the top of your resume.")

        if parsed_resume.get("phone") and parsed_resume.get("phone") != "Not Provided":
            contact_pts += 6
            good_points.append("✓ Valid contact telephone number provided.")
        else:
            improvements.append("⚠ Missing contact phone number.")

        if parsed_resume.get("linkedin"):
            contact_pts += 4
            good_points.append("✓ LinkedIn profile link included.")
        else:
            improvements.append("⚠ Missing LinkedIn profile URL.")
            suggestions.append("Include a customized LinkedIn profile link in the header.")

        if parsed_resume.get("github"):
            contact_pts += 4
            good_points.append("✓ GitHub / Portfolio repository link included.")
        else:
            improvements.append("⚠ Missing GitHub repository or portfolio link.")
            suggestions.append("Add your GitHub profile or portfolio link to showcase practical code.")

        score += contact_pts

        # 2. Essential Section Structure (Max 25 pts)
        sec_pts = 0
        if sections.get("skills", "").strip() or parsed_resume.get("skills"):
            sec_pts += 7
            good_points.append("✓ Dedicated Technical Skills section present.")
        else:
            improvements.append("⚠ Missing distinct Skills section.")

        if sections.get("education", "").strip() or parsed_resume.get("education", {}).get("degree"):
            sec_pts += 6
            good_points.append("✓ Clear Academic Qualifications & Education section.")
        else:
            improvements.append("⚠ Missing Education section.")

        if sections.get("projects", "").strip() or parsed_resume.get("projects"):
            sec_pts += 6
            good_points.append("✓ Hands-on Practical Projects section detected.")
        else:
            improvements.append("⚠ Missing Projects section.")
            suggestions.append("Add 2-3 substantial technical projects highlighting technologies used.")

        if sections.get("experience", "").strip() or parsed_resume.get("experience", {}).get("years_of_experience", 0) > 0:
            sec_pts += 6
            good_points.append("✓ Work Experience / Internships section formatted.")
        else:
            # Fresher check
            if parsed_resume.get("experience", {}).get("is_fresher"):
                sec_pts += 4
            else:
                improvements.append("⚠ Experience section could be more clearly labeled.")

        score += sec_pts

        # 3. Action Verbs & Impactful Writing (Max 20 pts)
        lower_text = raw_text.lower()
        verbs_found = [v for v in self.ACTION_VERBS if re.search(rf'\b{v}\b', lower_text)]
        if len(verbs_found) >= 5:
            score += 20
            good_points.append(f"✓ Strong action verbs used throughout ({', '.join(verbs_found[:4])}).")
        elif len(verbs_found) >= 2:
            score += 12
            good_points.append("✓ Some action verbs used in bullet points.")
            suggestions.append("Use stronger active verbs like 'Architected', 'Optimized', 'Automated' to start bullet points.")
        else:
            score += 5
            improvements.append("⚠ Passive tone detected; lacks powerful action verbs.")
            suggestions.append("Revise bullet points to start with strong action verbs (e.g. Engineered, Deployed, Reduced).")

        # 4. Quantified Metrics & Business Impact (Max 20 pts)
        metric_matches = self.QUANTIFIABLE_PATTERN.findall(raw_text)
        if len(metric_matches) >= 4:
            score += 20
            good_points.append(f"✓ Excellent quantified impact and measurable results ({', '.join(metric_matches[:3])}).")
        elif len(metric_matches) >= 1:
            score += 12
            good_points.append("✓ Contains some measurable results.")
            suggestions.append("Quantify more achievements (e.g., 'Reduced query latency by 35%', 'Handled 5,000 daily requests').")
        else:
            score += 4
            improvements.append("⚠ No quantified achievements or performance numbers found.")
            suggestions.append("Add measurable outcomes (e.g., 'Improved accuracy by 15%', 'Saved 4 hours weekly with automation').")

        # 5. Length & Readability (Max 15 pts)
        if 200 <= word_count <= 800:
            score += 15
            good_points.append(f"✓ Optimal length ({word_count} words; approx 1-2 pages).")
        elif word_count < 200:
            score += 6
            improvements.append(f"⚠ Resume is too brief ({word_count} words).")
            suggestions.append("Expand on project implementations and technical responsibilities.")
        else:
            score += 8
            improvements.append(f"⚠ Resume is quite dense ({word_count} words).")
            suggestions.append("Condense descriptions into concise, high-impact bullet points.")

        # 6. Date Integrity (deduction up to 10 pts): inverted / impossible employment ranges
        inverted = 0
        this_year = datetime.now().year
        for start, end in re.findall(r'((?:19|20)\d{2})\s*(?:-|\u2013|\u2014|to)\s*((?:19|20)\d{2}|present|current)', raw_text, re.IGNORECASE):
            e_val = this_year if end.lower() in ("present", "current") else int(end)
            if int(start) > e_val or e_val > this_year + 1:
                inverted += 1
        if inverted:
            score -= min(10.0, 5.0 * inverted)
            improvements.append(f"⚠ {inverted} non-chronological or impossible date range(s) detected (start date after end date).")
            suggestions.append("List roles in reverse-chronological order and double-check every start/end date.")

        # Match with JD Suggestions
        if jd_skills:
            res_skills = parsed_resume.get("skills", [])
            missing_high_priority = [s for s in jd_skills if s not in res_skills][:3]
            if missing_high_priority:
                suggestions.append(f"Incorporate missing target keywords if experienced: {', '.join(missing_high_priority)}.")

        total_score = round(min(100.0, max(10.0, score)), 1)

        return {
            "quality_score": total_score,
            "rating": "Excellent" if total_score >= 85 else ("Good" if total_score >= 70 else ("Fair" if total_score >= 50 else "Needs Work")),
            "word_count": word_count,
            "good_points": good_points,
            "improvements": improvements,
            "suggestions": suggestions
        }

"""
Job Description (JD) Parser
Extracts structured recruitment criteria from job descriptions:
- Required & Preferred Skills
- Minimum & Target Experience in years
- Education requirements
- Key domain competencies
"""

import re
from typing import Dict, List, Any
from src.core.skill_ontology import extract_skills_from_text, normalize_skill


class JDParser:
    """Extracts structured requirements from Job Descriptions."""

    def parse(self, jd_text: str, title_hint: str = "") -> Dict[str, Any]:
        """Parses a job description text into structured evaluation criteria."""
        if not jd_text:
            return {
                "job_title": title_hint or "General Technical Role",
                "required_skills": [],
                "preferred_skills": [],
                "min_experience_years": 0.0,
                "preferred_degrees": ["B.E. / B.Tech"],
                "raw_text": ""
            }

        # 1. Extract Job Title
        job_title = title_hint
        if not job_title:
            lines = [l.strip() for l in jd_text.split('\n') if l.strip()]
            for line in lines[:3]:
                if len(line) < 60 and any(kw in line.lower() for kw in ["engineer", "developer", "scientist", "analyst", "lead", "architect", "manager"]):
                    job_title = line
                    break
        if not job_title:
            job_title = "Technical Specialist"

        # 2. Extract Skills
        all_skills = extract_skills_from_text(jd_text)

        # Distinguish between must-have and good-to-have if sections exist
        required_skills = []
        preferred_skills = []
        
        pref_pattern = re.compile(r'(?:preferred|good\s+to\s+have|plus|bonus|nice\s+to\s+have|optional)[:\s]+(.*?)(?=\n\n|\Z)', re.IGNORECASE | re.DOTALL)
        pref_match = pref_pattern.search(jd_text)
        if pref_match:
            preferred_text = pref_match.group(1)
            preferred_skills = extract_skills_from_text(preferred_text)
            required_skills = [s for s in all_skills if s not in preferred_skills]
        else:
            required_skills = all_skills

        # 3. Extract Experience Requirement
        min_exp = 0.0
        exp_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\+?\s*(?:-\s*([0-9]+)\s*)?(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?', jd_text, re.IGNORECASE)
        if exp_match:
            try:
                min_exp = float(exp_match.group(1))
            except ValueError:
                min_exp = 0.0

        # 4. Extract Preferred Degrees
        degrees = []
        if re.search(r'\b(b\.?e\.?|b\.?tech\.?|bachelor)\b', jd_text, re.IGNORECASE):
            degrees.append("B.E. / B.Tech")
        if re.search(r'\b(m\.?e\.?|m\.?tech\.?|master|m\.?s\.?)\b', jd_text, re.IGNORECASE):
            degrees.append("M.E. / M.Tech")
        if re.search(r'\b(ph\.?d\.?)\b', jd_text, re.IGNORECASE):
            degrees.append("Ph.D.")
        if not degrees:
            degrees = ["B.E. / B.Tech"]

        return {
            "job_title": job_title,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "min_experience_years": min_exp,
            "preferred_degrees": degrees,
            "raw_text": jd_text
        }

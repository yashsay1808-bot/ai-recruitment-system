"""
Optional Generative AI Client (Gemini / OpenAI API)
Enriches interview question synthesis, candidate summaries, and qualitative critiques
when an API key is provided. Operates with automatic local offline fallback.
"""

import os
import json
from typing import Dict, List, Any, Optional


class LLMClient:
    """Provides optional LLM enhancements with seamless offline fallback."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.provider = provider.lower()
        self.is_enabled = bool(self.api_key)

    def enhance_interview_questions(
        self,
        candidate_name: str,
        job_title: str,
        matched_skills: List[str],
        missing_skills: List[str],
        projects: List[Dict[str, Any]],
        fallback_questions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Uses LLM to generate highly customized interview questions if API key is present.
        Otherwise returns the built-in offline questionnaire.
        """
        if not self.is_enabled:
            return fallback_questions

        # If Gemini / OpenAI is configured
        try:
            if self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                prompt = f"""
                You are an expert technical interviewer hiring for a {job_title} role.
                Candidate: {candidate_name}
                Matched Skills: {', '.join(matched_skills)}
                Missing / Skill Gaps: {', '.join(missing_skills)}
                Projects: {json.dumps([p.get('title') for p in projects])}

                Generate a JSON object with:
                - "technical_questions": list of 3-4 objects with keys ("skill", "question", "difficulty", "eval_criteria")
                - "project_questions": list of 2-3 objects with keys ("project_title", "question", "eval_criteria")
                - "gap_probing_questions": list of 2 objects with keys ("missing_skill", "question", "eval_criteria")
                - "behavioral_questions": list of 2-3 objects with keys ("question", "eval_criteria")

                Return ONLY valid raw JSON.
                """
                response = model.generate_content(prompt)
                raw_json = response.text.strip().lstrip("```json").rstrip("```").strip()
                parsed = json.loads(raw_json)
                return parsed
        except Exception as e:
            print(f"LLM generation notice (using rich local bank): {e}")

        return fallback_questions

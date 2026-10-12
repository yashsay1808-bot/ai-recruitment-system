"""
Bias-Aware Blind Screening Anonymizer
Implements Fair AI recruitment by redacting personally identifiable information (PII)
and demographic clues (Name, Email, Phone, Address, Gender markers)
to ensure evaluation focuses exclusively on skills, projects, and merit.
"""

import re
import copy
from typing import Dict, Any, List


class BiasFilter:
    """Anonymizes candidate profiles for objective, fair recruitment screening."""

    GENDER_PRONOUNS = [
        (r'\bhe\b', 'they'),
        (r'\bshe\b', 'they'),
        (r'\bhim\b', 'them'),
        (r'\bher\b', 'them'),
        (r'\bhis\b', 'their'),
        (r'\bhers\b', 'theirs'),
        (r'\bhimself\b', 'themselves'),
        (r'\bherself\b', 'themselves'),
        (r'\bmr\b\.?', ''),
        (r'\bms\b\.?', ''),
        (r'\bmrs\b\.?', '')
    ]

    def anonymize_candidate(self, candidate_data: Dict[str, Any], candidate_index: int = 1) -> Dict[str, Any]:
        """
        Creates a blind copy of candidate data with PII masked out.
        """
        blind = copy.deepcopy(candidate_data)
        
        masked_id = f"Candidate #{candidate_index:03d}"
        real_name = blind.get("candidate_name", "Candidate")
        
        blind["candidate_name"] = masked_id
        blind["original_name_masked"] = True
        blind["email"] = "████████@candidate.id"
        blind["phone"] = "+██ ██████████"
        blind["location"] = "Location Redacted (Fair Hiring)"
        blind["linkedin"] = "https://linkedin.com/in/██████" if blind.get("linkedin") else None
        blind["github"] = "https://github.com/██████" if blind.get("github") else None
        blind["file_name"] = f"Application_{candidate_index:03d}.pdf"

        # Sanitize text
        raw_text = blind.get("raw_text", "")
        if real_name and real_name != "Candidate":
            raw_text = re.sub(re.escape(real_name), masked_id, raw_text, flags=re.IGNORECASE)

        # Neutralize gender pronouns in text
        for pat, replacement in self.GENDER_PRONOUNS:
            raw_text = re.sub(pat, replacement, raw_text, flags=re.IGNORECASE)

        blind["raw_text"] = raw_text

        return blind

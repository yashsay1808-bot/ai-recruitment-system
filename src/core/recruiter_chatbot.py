"""
AI Recruiter Assistant & Talent Copilot Core Engine
Provides natural language querying, automated headhunter intelligence,
candidate comparison, salary & market compensation estimation, risk detection,
interview question synthesis, and outreach email generation.
Supports both 100% offline rule-based NLP intent analysis and optional Gemini/OpenAI generative enhancement.
"""

import re
import json
import collections
from typing import Dict, List, Any, Optional, Tuple


class RecruiterChatbot:
    """Intelligent conversational talent intelligence assistant for HR and hiring teams."""

    SUGGESTED_PROMPTS = [
        "🏆 Who is the top ranked candidate and why?",
        "🔍 What skills are missing across the candidate pool?",
        "⚖️ Compare Rahul Nair and Aarav Sharma",
        "💰 Estimate salary and market leveling for Rahul Nair",
        "🚨 Analyze red flags and hiring risks for candidates",
        "✉️ Draft an interview invitation email for the top candidate",
        "💼 Which candidates have more than 2 years of experience?",
        "🎙️ What interview questions should I ask the top candidate?",
        "📊 Summarize the current batch screening results"
    ]

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.last_candidate_name: Optional[str] = None

    def _resolve_candidate(
        self,
        query: str,
        ranked_candidates: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Resolves target candidate from query text or context memory."""
        cleaned_query = query.lower()

        # 1. Check exact or partial name matches
        for c in ranked_candidates:
            c_name = c.get("candidate_name", "").lower()
            if not c_name:
                continue
            first_name = c_name.split()[0] if c_name else ""
            if c_name in cleaned_query or (len(first_name) >= 3 and first_name in cleaned_query):
                self.last_candidate_name = c.get("candidate_name")
                return c

        # 2. Check rank mentions (e.g. "rank 1", "#1", "top candidate")
        if any(term in cleaned_query for term in ["top candidate", "rank 1", "rank #1", "#1", "first candidate", "best candidate", "leader"]):
            if ranked_candidates:
                self.last_candidate_name = ranked_candidates[0].get("candidate_name")
                return ranked_candidates[0]

        # 3. Check rank #2, #3, etc.
        rank_match = re.search(r'(?:rank|#)\s*(\d+)', cleaned_query)
        if rank_match:
            r_num = int(rank_match.group(1))
            if 1 <= r_num <= len(ranked_candidates):
                c = ranked_candidates[r_num - 1]
                self.last_candidate_name = c.get("candidate_name")
                return c

        # 4. Fallback to context memory if pronoun used ("he", "she", "they", "this candidate", "him", "her")
        if self.last_candidate_name and any(p in cleaned_query.split() for p in ["he", "she", "his", "her", "him", "them", "they", "candidate", "their"]):
            for c in ranked_candidates:
                if c.get("candidate_name", "").lower() == self.last_candidate_name.lower():
                    return c

        # 5. Default to top candidate if only one candidate is in context
        return ranked_candidates[0] if ranked_candidates else None

    def answer_query(
        self,
        user_query: str,
        ranked_candidates: List[Dict[str, Any]],
        current_jd: Dict[str, Any],
        db=None
    ) -> str:
        """
        Processes a recruiter query and generates an insightful, structured response.
        """
        if not user_query or not user_query.strip():
            return "Please ask a question about candidates, skill gaps, market salaries, risks, or screening analytics."

        cleaned_query = user_query.lower().strip()

        # Check if candidate pool is available
        if not ranked_candidates:
            return "⚠️ No candidates have been screened in the active session yet. Please configure a Job Description and run screening in **Page 1 (Job & Upload)** first!"

        top_cand = ranked_candidates[0] if ranked_candidates else None
        job_title = current_jd.get("job_title", "Target Role")

        # ------------------ Intent 1: Salary & Market Leveling Estimator ------------------
        if any(kw in cleaned_query for kw in ["salary", "compensation", "offer amount", "pay", "ctc", "leveling", "market rate", "market value"]):
            target_c = self._resolve_candidate(cleaned_query, ranked_candidates) or top_cand
            if target_c:
                c_data = target_c.get("candidate_data", {})
                exp_yrs = c_data.get("experience", {}).get("years_of_experience", 0.0)
                overall_score = target_c.get("overall_score", 0.0)
                c_name = target_c.get("candidate_name", "Candidate")

                # Leveling Tier
                if exp_yrs < 1.5:
                    level = "Junior / Associate Engineer (L3)"
                    base_usd = (75000, 95000)
                    base_inr_lpa = (7.0, 12.0)
                elif exp_yrs < 4.0:
                    level = "Mid-Level Engineer (L4)"
                    base_usd = (105000, 135000)
                    base_inr_lpa = (14.0, 22.0)
                elif exp_yrs < 7.0:
                    level = "Senior Engineer (L5)"
                    base_usd = (145000, 185000)
                    base_inr_lpa = (25.0, 38.0)
                else:
                    level = "Staff / Principal Engineer (L6+)"
                    base_usd = (195000, 245000)
                    base_inr_lpa = (40.0, 65.0)

                # Score multiplier bonus (strong candidates command top of band)
                multiplier = 1.05 if overall_score >= 80.0 else (0.95 if overall_score < 60.0 else 1.0)
                low_usd = int(base_usd[0] * multiplier)
                high_usd = int(base_usd[1] * multiplier)
                low_inr = round(base_inr_lpa[0] * multiplier, 1)
                high_inr = round(base_inr_lpa[1] * multiplier, 1)

                resp = f"### 💰 Market Leveling & Compensation Guidance for **{c_name}**\n\n"
                resp += f"**🎯 Recommended Seniority Bracket:** `{level}`\n"
                resp += f"**Years of Experience:** `{exp_yrs} yrs` | **Overall Screening Score:** `{overall_score}%`\n\n"
                resp += "| Geography / Market | Estimated Base Salary Band | Typical Equity / Bonus |\n"
                resp += "|---|---|---|\n"
                resp += f"| **US / Remote Global** | `${low_usd:,} – ${high_usd:,} / yr` | `10% – 15% Bonus + Stock Options` |\n"
                resp += f"| **India Tech Hub** | `₹{low_inr} – ₹{high_inr} LPA` | `₹1.5L – ₹3L Performance Bonus` |\n\n"
                resp += f"💡 **Negotiation Strategy:** {c_name} scored `{overall_score}%` against **{job_title}**. "
                if overall_score >= 75.0:
                    resp += "Given their strong skill match and verified experience, offer near the **75th percentile** of the band to prevent competing counter-offers."
                else:
                    resp += "Offer around the **mid-point** of the band with performance milestone reviews scheduled at 6 months."
                return resp

        # ------------------ Intent 2: Red Flags & Risk Analysis ------------------
        if any(kw in cleaned_query for kw in ["red flag", "red flags", "risk", "risks", "concern", "weakness", "drawback", "flaws", "warning"]):
            target_c = self._resolve_candidate(cleaned_query, ranked_candidates) or top_cand
            if target_c:
                c_name = target_c.get("candidate_name", "Candidate")
                gap = target_c.get("gap_results", {})
                c_data = target_c.get("candidate_data", {})
                exp_yrs = c_data.get("experience", {}).get("years_of_experience", 0.0)
                min_req_yrs = current_jd.get("min_experience_years", 0.0)
                missing = gap.get("missing_skills", [])
                score = target_c.get("overall_score", 0.0)
                qa_score = target_c.get("breakdown", {}).get("resume_quality", 75.0)

                flags = []
                # Check 1: Missing core skills
                if missing:
                    flags.append(f"**Missing Core Competencies:** Missing `{len(missing)}` required tools ({', '.join(missing[:3])}). Will require onboarding ramp-up.")
                # Check 2: Experience shortfall
                if min_req_yrs > 0 and exp_yrs < min_req_yrs:
                    deficit = round(min_req_yrs - exp_yrs, 1)
                    flags.append(f"**Experience Deficit:** Has `{exp_yrs} yrs` vs required `{min_req_yrs} yrs` ({deficit} yrs deficit).")
                # Check 3: ATS formatting / quality
                if qa_score < 65.0:
                    flags.append(f"**Resume Polish Concern:** Low ATS quality score (`{qa_score}%`). Resume lacks quantified metric impacts.")
                # Check 4: Education alignment
                pref_degrees = current_jd.get("preferred_degrees", [])
                cand_degree = c_data.get("education", {}).get("degree", "")
                if pref_degrees and cand_degree and not any(p.lower() in cand_degree.lower() for p in pref_degrees):
                    flags.append(f"**Degree Non-Match:** Holds `{cand_degree}` which does not match preferred qualifications ({', '.join(pref_degrees)}).")

                resp = f"### 🚨 Risk & Red Flag Evaluation for **{c_name}** ({job_title})\n\n"
                if flags:
                    resp += f"We flagged **{len(flags)} potential risk areas** for recruiter review:\n\n"
                    for idx, f in enumerate(flags, 1):
                        resp += f"{idx}. ⚠️ {f}\n"
                    resp += f"\n**🛡️ Mitigation Advice:** Probe these specific points during the screening interview before issuing an on-site invitation."
                else:
                    resp += f"✅ **Clean Profile!** No significant red flags identified. {c_name} matches required experience (`{exp_yrs} yrs`) and core technical stack with `{score}%` overall fit."
                return resp

        # ------------------ Intent 3: Email Outreach & Offer Generator ------------------
        if any(kw in cleaned_query for kw in ["email", "outreach", "invite", "invitation", "draft", "offer letter", "rejection letter", "message"]):
            target_c = self._resolve_candidate(cleaned_query, ranked_candidates) or top_cand
            if target_c:
                c_name = target_c.get("candidate_name", "Candidate")
                matched = target_c.get("gap_results", {}).get("matched_skills", [])
                skills_str = ", ".join(matched[:3]) if matched else "engineering background"
                c_email = target_c.get("candidate_data", {}).get("personal_info", {}).get("email") or f"{c_name.lower().replace(' ', '.')}@email.com"

                if "reject" in cleaned_query:
                    resp = f"### ✉️ Respectful Candidate Feedback & Rejection Email\n\n"
                    resp += f"**To:** `{c_email}`\n"
                    resp += f"**Subject:** Update regarding your application for {job_title} at Enterprise\n\n"
                    resp += f"---\n\n"
                    resp += f"Dear {c_name},\n\n"
                    resp += f"Thank you for taking the time to share your background with our engineering team for the **{job_title}** position.\n\n"
                    resp += f"While we were impressed with your experience in {skills_str}, we have decided to proceed with candidates whose current skill profile more closely aligns with our immediate technical stack.\n\n"
                    resp += f"We will keep your resume in our talent network for upcoming openings. We wish you continued success in your professional journey.\n\n"
                    resp += "Warm regards,\n\n**Talent Acquisition Team**"
                    return resp
                elif "offer" in cleaned_query:
                    resp = f"### ✉️ Formal Employment Offer Letter\n\n"
                    resp += f"**To:** `{c_email}`\n"
                    resp += f"**Subject:** Offer of Employment: {job_title} at Enterprise\n\n"
                    resp += f"---\n\n"
                    resp += f"Dear {c_name},\n\n"
                    resp += f"On behalf of Enterprise, we are thrilled to offer you the position of **{job_title}**! Our team was deeply impressed with your technical expertise, project achievements, and cultural fit.\n\n"
                    resp += f"**Key Terms of Offer:**\n"
                    resp += f"- **Role:** {job_title}\n"
                    resp += f"- **Reporting To:** Engineering Director\n"
                    resp += f"- **Start Date:** [Agreed Start Date]\n"
                    resp += f"- **Compensation:** Base salary and comprehensive health, equity, and retirement benefits package as detailed in the formal agreement.\n\n"
                    resp += f"Please review the attached formal document and sign by [Deadline Date]. We look forward to building great things together!\n\n"
                    resp += "Sincerely,\n\n**Executive Hiring Committee**"
                    return resp
                else:
                    # Default: Interview Invite
                    resp = f"### ✉️ Personalized Technical Interview Invitation\n\n"
                    resp += f"**To:** `{c_email}`\n"
                    resp += f"**Subject:** Interview Invitation: {job_title} role at Enterprise\n\n"
                    resp += f"---\n\n"
                    resp += f"Hi {c_name},\n\n"
                    resp += f"Thanks for submitting your application! Our technical hiring committee reviewed your profile and was particularly impressed by your hands-on work with **{skills_str}**.\n\n"
                    resp += f"We would love to invite you to a 45-minute technical conversation to discuss your past projects, architectural decisions, and the challenges our {job_title} team is tackling.\n\n"
                    resp += f"**Next Steps:**\n"
                    resp += f"Please click our scheduling calendar below to select a time that works best for you:\n"
                    resp += f"👉 `https://calendly.com/enterprise-recruiting/{c_name.lower().replace(' ', '-')}`\n\n"
                    resp += f"Looking forward to speaking with you!\n\n"
                    resp += "Best regards,\n\n**Talent Acquisition Team**"
                    return resp

        # ------------------ Intent 4: Interview Questions Generation ------------------
        if any(kw in cleaned_query for kw in ["interview", "question", "questions", "ask", "quiz", "technical question", "probe"]):
            target_c = self._resolve_candidate(cleaned_query, ranked_candidates) or top_cand

            if target_c:
                matched_skills = target_c.get("gap_results", {}).get("matched_skills", [])
                missing_skills = target_c.get("gap_results", {}).get("missing_skills", [])
                projects = target_c.get("candidate_data", {}).get("projects", [])
                proj_title = projects[0].get("title", "Recent Project") if projects else "Production System"

                s1 = matched_skills[0] if matched_skills else "Core Architecture"
                s2 = matched_skills[1] if len(matched_skills) > 1 else "System Design"

                resp = f"### 🎙️ Structured Interview Assessment Kit for **{target_c.get('candidate_name')}** ({job_title})\n\n"
                resp += f"#### 💻 1. Core Technical Question ({s1}):\n"
                resp += f"- **Question:** *\"Can you walk us through how you design, debug, and optimize production pipelines using {s1}?\"*\n"
                resp += f"- **Evaluation Rubric:** Look for modular code structure, exception handling, and awareness of execution bottlenecks.\n\n"

                resp += f"#### 💻 2. Specialized Technical Question ({s2}):\n"
                resp += f"- **Question:** *\"How do you handle scalability, latency, concurrency, and edge cases in {s2} implementations?\"*\n"
                resp += f"- **Evaluation Rubric:** Candidate should discuss caching, asynchronous execution, and DB indexing.\n\n"

                resp += f"#### 🛠️ 3. Hands-On Project Cross-Examination ({proj_title}):\n"
                resp += f"- **Question:** *\"In your project '{proj_title}', what was the hardest trade-off you made, and what would you re-architect today?\"*\n"
                resp += f"- **Evaluation Rubric:** Assesses real ownership vs passive project participation.\n\n"

                if missing_skills:
                    resp += f"#### 🔍 4. Skill Gap Probing Question ({missing_skills[0]}):\n"
                    resp += f"- **Question:** *\"This position utilizes {missing_skills[0]}, which was not explicit on your resume. Have you had adjacent exposure, and how quickly can you ramp up?\"*\n"
                    resp += f"- **Evaluation Rubric:** High learning velocity, foundational theoretical grasp.\n\n"

                resp += "#### 🤝 5. Behavioral STAR Round:\n"
                resp += "- **Question:** *\"Describe a situation where a production service failed or requirements changed abruptly. How did you communicate and recover?\"*\n\n"
                resp += "💡 You can download the complete questionnaire kit with answer keys in **Page 5 (AI Interview Assistant)**!"
                return resp

        # ------------------ Intent 5: Candidate Comparison ------------------
        if any(kw in cleaned_query for kw in ["compare", "versus", "vs", "difference between", "better"]):
            mentioned = []
            for c in ranked_candidates:
                c_name = c.get("candidate_name", "").lower()
                first_name = c_name.split()[0] if c_name else ""
                if (c_name and c_name in cleaned_query) or (first_name and len(first_name) >= 3 and first_name in cleaned_query):
                    mentioned.append(c)

            if len(mentioned) >= 2:
                c1, c2 = mentioned[0], mentioned[1]
            elif len(ranked_candidates) >= 2:
                c1, c2 = ranked_candidates[0], ranked_candidates[1]
            else:
                return "Need at least 2 candidates to generate a comparison."

            exp1 = c1.get('candidate_data', {}).get('experience', {}).get('years_of_experience', 0)
            exp2 = c2.get('candidate_data', {}).get('experience', {}).get('years_of_experience', 0)
            diff = round(abs(c1.get('overall_score', 0) - c2.get('overall_score', 0)), 1)
            leader = c1.get('candidate_name') if c1.get('overall_score', 0) >= c2.get('overall_score', 0) else c2.get('candidate_name')

            resp = f"### ⚖️ Side-by-Side Comparison: **{c1.get('candidate_name')}** vs **{c2.get('candidate_name')}**\n\n"
            resp += "| Metric | " + f"**{c1.get('candidate_name')}**" + " | " + f"**{c2.get('candidate_name')}**" + " |\n"
            resp += "|---|---|---|\n"
            resp += f"| **Overall Match Score** | `{c1.get('overall_score')}%` | `{c2.get('overall_score')}%` |\n"
            resp += f"| **Leaderboard Rank** | `#{c1.get('rank', 1)}` | `#{c2.get('rank', 2)}` |\n"
            resp += f"| **Technical Skills Match** | `{c1.get('breakdown', {}).get('technical_skills')}%` | `{c2.get('breakdown', {}).get('technical_skills')}%` |\n"
            resp += f"| **Semantic Fit** | `{c1.get('breakdown', {}).get('semantic_jd')}%` | `{c2.get('breakdown', {}).get('semantic_jd')}%` |\n"
            resp += f"| **Years Experience** | `{exp1} yrs` | `{exp2} yrs` |\n"
            resp += f"| **Education Credentials** | `{c1.get('candidate_data', {}).get('education', {}).get('degree', 'B.E.')}` | `{c2.get('candidate_data', {}).get('education', {}).get('degree', 'B.E.')}` |\n"
            resp += f"| **ATS Resume Quality** | `{c1.get('breakdown', {}).get('resume_quality', 75)}%` | `{c2.get('breakdown', {}).get('resume_quality', 75)}%` |\n"
            resp += f"| **Recommendation** | {c1.get('explanation', {}).get('status_label', 'N/A')} | {c2.get('explanation', {}).get('status_label', 'N/A')} |\n\n"
            resp += f"💡 **Executive Takeaway:** **{leader}** leads this matchup by **{diff}%** overall. "
            if exp1 != exp2:
                resp += f"({c1.get('candidate_name')} has {exp1} yrs vs {c2.get('candidate_name')}'s {exp2} yrs experience)."
            return resp

        # ------------------ Intent 6: Missing Skills & Bottlenecks ------------------
        if any(kw in cleaned_query for kw in ["missing skill", "missing skills", "skill gap", "skill gaps", "bottleneck", "lacking", "gap", "gaps"]):
            all_missing = []
            for c in ranked_candidates:
                all_missing.extend(c.get("gap_results", {}).get("missing_skills", []))

            if all_missing:
                counts = collections.Counter(all_missing)
                resp = f"### 🔍 Skill Gap & Bottleneck Analysis for **{job_title}**\n\n"
                resp += "The most frequently missing competencies across applicant resumes are:\n\n"
                for skill, cnt in counts.most_common(6):
                    pct = round(cnt / len(ranked_candidates) * 100, 1)
                    resp += f"- ❌ **{skill}**: Missing in `{cnt}/{len(ranked_candidates)}` candidates (`{pct}%` bottleneck)\n"
                resp += "\n💡 **Recruiter Tip:** These skills represent industry talent scarcity. Consider assessing candidate adjacent knowledge or providing dedicated ramp-up training."
                return resp
            else:
                return "✓ Great news! All required technical skills are well covered across the current candidate pool."

        # ------------------ Intent 7: Experience Filtering ------------------
        if any(kw in cleaned_query for kw in ["experience", "years of exp", "fresher", "senior", "mid level"]):
            exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)', cleaned_query)
            target_yrs = float(exp_match.group(1)) if exp_match else current_jd.get("min_experience_years", 2.0)

            filtered = [
                c for c in ranked_candidates 
                if c.get("candidate_data", {}).get("experience", {}).get("years_of_experience", 0) >= target_yrs
            ]

            resp = f"### 💼 Candidates with ≥ {target_yrs} Years Experience ({len(filtered)} found)\n\n"
            if filtered:
                for c in filtered:
                    exp_val = c.get("candidate_data", {}).get("experience", {}).get("years_of_experience", 0)
                    resp += f"- **{c.get('candidate_name')}** — `{exp_val} yrs` (Score: `{c.get('overall_score')}%` | {c.get('explanation', {}).get('status_label', 'Recommended')})\n"
            else:
                resp += f"No candidates found with {target_yrs}+ years of experience."
            return resp

        # ------------------ Intent 8: Batch Summary & Analytics ------------------
        if any(kw in cleaned_query for kw in ["summary", "analytics", "batch", "overview", "stats", "statistics", "report"]):
            total = len(ranked_candidates)
            shortlisted = sum(1 for c in ranked_candidates if c.get("overall_score", 0) >= 65.0)
            review = sum(1 for c in ranked_candidates if 50.0 <= c.get("overall_score", 0) < 65.0)
            rejected = sum(1 for c in ranked_candidates if c.get("overall_score", 0) < 50.0)
            avg_score = round(sum(c.get("overall_score", 0) for c in ranked_candidates) / max(total, 1), 1)

            resp = f"### 📊 Active Batch Screening Summary for **{job_title}**\n\n"
            resp += f"- **Total Resumes Processed:** `{total}`\n"
            resp += f"- **🟢 Shortlisted (≥65%):** `{shortlisted}` ({round(shortlisted/max(total,1)*100, 1)}% of talent pool)\n"
            resp += f"- **🟡 Under Review (50–64%):** `{review}`\n"
            resp += f"- **🔴 Not Recommended (<50%):** `{rejected}`\n"
            resp += f"- **Average Match Score:** `{avg_score}%`\n\n"
            if top_cand:
                resp += f"**🏆 Current Leader:** {top_cand.get('candidate_name')} with `{top_cand.get('overall_score')}%` overall match."
            return resp

        # ------------------ Intent 9: Top Candidate / Leaderboard ------------------
        if any(kw in cleaned_query for kw in ["top candidate", "best candidate", "highest score", "who is #1", "who is ranked 1", "rank 1", "winner", "leader"]):
            if top_cand:
                self.last_candidate_name = top_cand.get("candidate_name")
                c_data = top_cand.get("candidate_data", {})
                gap = top_cand.get("gap_results", {})
                explanation = top_cand.get("explanation", {})
                b = top_cand.get("breakdown", {})

                resp = f"### 🏆 Top Ranked Candidate: **{top_cand.get('candidate_name')}** (Rank #1)\n\n"
                resp += f"- **Overall Match Score:** `{top_cand.get('overall_score')}%` ({explanation.get('status_label', 'Strongly Recommended')})\n"
                resp += f"- **Technical Skills Match:** `{b.get('technical_skills')}%`\n"
                resp += f"- **Experience:** `{c_data.get('experience', {}).get('years_of_experience', 0)} Years`\n"
                resp += f"- **Education:** `{c_data.get('education', {}).get('degree', 'B.E.')}` in `{c_data.get('education', {}).get('branch', 'Engineering')}` (CGPA: `{c_data.get('education', {}).get('cgpa', 'N/A')}`)\n\n"

                matched = gap.get("matched_skills", [])
                if matched:
                    resp += f"**✓ Key Matched Skills:** {', '.join(matched[:6])}\n\n"

                missing = gap.get("missing_skills", [])
                if missing:
                    resp += f"**⚠️ Competency Gaps:** {', '.join(missing[:4])}\n\n"
                else:
                    resp += "**✓ No critical skill gaps flagged!**\n\n"

                resp += f"**💡 AI Decision Rationale:** _{explanation.get('executive_summary', 'Strong engineering profile with verified technical alignment.')}_"
                return resp

        # ------------------ Intent 10: Multi-Skill Search / Tech Stack Query ------------------
        # E.g. "Who knows python and docker", "candidates with pytorch"
        found_matches = []
        for c in ranked_candidates:
            c_skills = [s.lower() for s in c.get("candidate_data", {}).get("skills", [])]
            matched_words = [w for w in cleaned_query.split() if len(w) >= 3 and w in c_skills]
            if matched_words:
                found_matches.append((c, matched_words))

        if found_matches:
            resp = f"### 🔍 Candidates with Matched Stack Query ({len(found_matches)} found)\n\n"
            for c, m_words in found_matches[:6]:
                skills_str = ", ".join(m_words)
                resp += f"- **{c.get('candidate_name')}** (Rank #{c.get('rank', 1)} | Overall Match: `{c.get('overall_score')}%`) — Matched: `{skills_str}`\n"
            return resp

        # Default Intelligent Assistant Fallback Response
        resp = f"### 🤖 AI Recruiter Assistant\n\n"
        resp += f"I have analyzed **{len(ranked_candidates)} candidates** for **{job_title}**.\n\n"
        resp += f"- **Top Recommendation:** **{top_cand.get('candidate_name')}** (`{top_cand.get('overall_score')}%` match)\n\n"
        resp += "**Try asking me:**\n"
        resp += "- 🏆 *'Who is the best candidate and why?'*\n"
        resp += "- ⚖️ *'Compare Rahul Nair and Aarav Sharma'* \n"
        resp += "- 💰 *'Estimate salary and leveling for Rahul Nair'* \n"
        resp += "- 🚨 *'Analyze red flags and risks for candidates'* \n"
        resp += "- ✉️ *'Draft an interview invitation email for Rahul'* \n"
        resp += "- 🔍 *'What are the common missing skills?'* \n"
        return resp

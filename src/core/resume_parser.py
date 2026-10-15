"""
Advanced Multi-Format Resume Parser & OCR Engine
Supports PDF, Scanned PDF (with OCR fallback), DOCX, and TXT files.
Extracts structured candidate information:
- Personal: Name, Email, Phone, Location, Social Profiles (LinkedIn, GitHub)
- Skills: Programming Languages, Tools, Frameworks, Cloud, Databases
- Education: Degree, Field/Branch, Institution, CGPA/Score, Graduation Year
- Experience: Total Years, Job Titles, Companies, Time Spans
- Projects: Titles, Tech Stacks, Highlights
- Certifications: Industry credentials & course certifications
"""

import os
import io
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Document format loaders
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None
    Image = None

from src.core.skill_ontology import extract_skills_from_text, normalize_skill


class ResumeParser:
    """Robust, multi-format structured parser for resumes."""

    # Common Section Header Patterns
    SECTION_PATTERNS = {
        "education": r'(?:education|academic\s+background|academic\s+qualifications|academics|qualifications)',
        "experience": r'(?:work\s+experience|professional\s+experience|experience|employment\s+history|internships?|work\s+history)',
        "skills": r'(?:technical\s+skills|skills|core\s+competencies|technologies|technical\s+expertise|tools\s+&\s+technologies|skills\s+&\s+abilities)',
        "projects": r'(?:projects|personal\s+projects|academic\s+projects|key\s+projects|notable\s+projects)',
        "certifications": r'(?:certifications?|licenses|courses|achievements|honors|awards\s+&\s+certifications|(?:technical\s+)?activities\s+&\s+certifications)',
        "summary": r'(?:summary|professional\s+summary|about\s+me|profile|objective|career\s+objective)'
    }

    DEGREE_PATTERNS = [
        (r'\b(b\.?e\.?|b\.?tech\.?|bachelor\s+of\s+engineering|bachelor\s+of\s+technology)\b', 'B.E. / B.Tech'),
        (r'\b(m\.?e\.?|m\.?tech\.?|master\s+of\s+engineering|master\s+of\s+technology)\b', 'M.E. / M.Tech'),
        (r'\b(b\.?s\.?|b\.?sc\.?|bachelor\s+of\s+science)\b', 'B.S. / B.Sc'),
        (r'\b(m\.?s\.?|m\.?sc\.?|master\s+of\s+science)\b', 'M.S. / M.Sc'),
        (r'\b(bca|bachelor\s+of\s+computer\s+applications)\b', 'BCA'),
        (r'\b(mca|master\s+of\s+computer\s+applications)\b', 'MCA'),
        (r'\b(ph\.?d\.?|doctor\s+of\s+philosophy)\b', 'Ph.D.'),
        (r'\b(mba|master\s+of\s+business\s+administration)\b', 'MBA'),
        (r'\b(diploma|associate\s+degree)\b', 'Diploma')
    ]

    BRANCH_PATTERNS = [
        (r'\b(computer\s+science|cse|cs)\b', 'Computer Science & Engineering'),
        (r'\b(information\s+science|ise|is|information\s+technology|it)\b', 'Information Science & Engineering'),
        (r'\b(data\s+science|artificial\s+intelligence|ai\s*&\s*ds|ai\s*&\s*ml)\b', 'AI & Data Science'),
        (r'\b(electronics|ece|telecommunication)\b', 'Electronics & Communication'),
        (r'\b(electrical|eee)\b', 'Electrical & Electronics'),
        (r'\b(mechanical|mech)\b', 'Mechanical Engineering'),
        (r'\b(civil)\b', 'Civil Engineering')
    ]

    JOB_TITLE_KEYWORDS = [
        "Software Engineer", "Senior Software Engineer", "Software Developer", "Full Stack Developer",
        "Frontend Developer", "Backend Developer", "Machine Learning Engineer", "Data Scientist",
        "Data Analyst", "AI Engineer", "Deep Learning Engineer", "DevOps Engineer", "Cloud Engineer",
        "NLP Engineer", "System Engineer", "QA Engineer", "Python Developer", "Java Developer",
        "Research Intern", "Software Engineering Intern", "Machine Learning Intern", "Data Science Intern",
        "Graduate Trainee", "Technical Lead", "Architect", "Product Manager"
    ]

    def __init__(self):
        pass

    def extract_text(self, file_bytes: bytes, file_name: str) -> Tuple[str, bool]:
        """
        Extracts raw text from PDF, DOCX, or TXT file bytes.
        Returns (extracted_text, is_scanned_ocr_used).
        """
        ext = file_name.lower().split(".")[-1]
        text = ""
        is_ocr = False

        if ext == "pdf":
            text, is_ocr = self._extract_from_pdf(file_bytes)
        elif ext in ["docx", "doc"]:
            text = self._extract_from_docx(file_bytes)
        elif ext in ["txt", "text"]:
            try:
                text = file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                text = str(file_bytes)
        else:
            # Fallback text decoder
            try:
                text = file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                text = str(file_bytes)

        # Clean text
        text = self._clean_text(text)
        return text, is_ocr

    def _extract_from_pdf(self, file_bytes: bytes) -> Tuple[str, bool]:
        """Extract text from PDF using PyMuPDF, with OCR fallback for scanned pages."""
        text = ""
        is_ocr = False

        if fitz is not None:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    page_text = page.get_text("text")
                    if page_text and len(page_text.strip()) > 30:
                        text += page_text + "\n"
                    else:
                        # Page might be scanned or image-based, attempt OCR fallback
                        if pytesseract and Image:
                            try:
                                pix = page.get_pixmap(dpi=200)
                                img = Image.open(io.BytesIO(pix.tobytes("png")))
                                ocr_text = pytesseract.image_to_string(img)
                                if ocr_text.strip():
                                    text += ocr_text + "\n"
                                    is_ocr = True
                            except Exception:
                                pass
            except Exception as e:
                print(f"Error reading PDF with PyMuPDF: {e}")

        # Fallback if PyMuPDF extracted minimal text
        if len(text.strip()) < 30 and pytesseract and Image and fitz:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img)
                    text += ocr_text + "\n"
                    is_ocr = True
            except Exception:
                pass

        return text, is_ocr

    def _extract_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX document."""
        text = ""
        if docx is not None:
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                        if row_text:
                            text += row_text + "\n"
            except Exception as e:
                print(f"Error reading DOCX: {e}")
        return text

    def _clean_text(self, text: str) -> str:
        """Normalize line breaks and remove redundant spaces."""
        text = text.replace('\r', '\n')
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        return text.strip()

    def segment_sections(self, text: str) -> Dict[str, str]:
        """Segments resume text into standard logical sections."""
        lines = text.split('\n')
        sections = {
            "header": "",
            "summary": "",
            "skills": "",
            "experience": "",
            "education": "",
            "projects": "",
            "certifications": "",
            "other": ""
        }
        
        current_section = "header"
        buffer: List[str] = []

        combined_pattern = "|".join(
            f"(?P<{sec}>^{pat}\\b)" for sec, pat in self.SECTION_PATTERNS.items()
        )
        regex = re.compile(combined_pattern, re.IGNORECASE)

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check if line looks like a header (short line matching header pattern)
            if len(line_str) < 50:
                match = regex.search(line_str)
                if match:
                    # Save existing buffer
                    if buffer:
                        sections[current_section] += "\n".join(buffer) + "\n"
                        buffer = []
                    # Identify which section matched
                    for sec_name, val in match.groupdict().items():
                        if val:
                            current_section = sec_name
                            break
                    continue
            
            buffer.append(line_str)

        if buffer:
            sections[current_section] += "\n".join(buffer) + "\n"

        return sections

    def extract_name(self, text: str, header_text: str) -> str:
        """Extracts candidate name with heuristics."""
        # Top 5 lines of document or header
        candidates = []
        source_lines = (header_text if header_text.strip() else text).split('\n')[:8]
        
        noise_words = {
            "resume", "curriculum", "vitae", "cv", "page", "email", "phone", "contact",
            "profile", "summary", "skills", "experience", "education", "projects", "github",
            "linkedin", "address", "developer", "engineer"
        }

        for line in source_lines:
            cleaned = line.strip()
            if not cleaned or len(cleaned) > 50 or '@' in cleaned or 'http' in cleaned or '+' in cleaned:
                continue
            
            # Strip titles/credentials
            cleaned = re.sub(r'^(mr|ms|mrs|dr)\.?\s+', '', cleaned, flags=re.IGNORECASE)
            words = cleaned.split()
            
            if 1 <= len(words) <= 4:
                # Check that words are predominantly alphabetic and not noise words
                if all(w.replace('.', '').replace('-', '').isalpha() for w in words):
                    lower_words = [w.lower() for w in words]
                    if not any(nw in lower_words for nw in noise_words):
                        return " ".join([w.capitalize() for w in words])

        return "Candidate"

    def extract_email(self, text: str) -> Optional[str]:
        """Extract primary email address."""
        match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        return match.group(0).strip() if match else None

    def extract_phone(self, text: str) -> Optional[str]:
        """Extract contact phone number."""
        # Matches patterns like:
        # +91 98450 12345, +91-9845012345, (555) 123-4567, 9845012345, +1 555-123-4567
        patterns = [
            r'(?:\+?91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}',  # Indian 10-digit (5-5 split or continuous)
            r'(?:\+?1[\-\s]?)?\(?\d{3}\)?[\-\s]?\d{3}[\-\s]?\d{4}',  # US/North America
            r'(?:\+?\d{1,3}[\-\s]?)?\(?\d{2,4}\)?[\-\s]?\d{3,4}[\-\s]?\d{3,4}'  # General international
        ]
        
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                raw = match.group(0).strip()
                digits = re.sub(r'\D', '', raw)
                if 10 <= len(digits) <= 13:
                    return raw
        return None

    def extract_location(self, text: str) -> Optional[str]:
        """Extract city/state or country location."""
        cities = [
            "Bengaluru", "Bangalore", "Hyderabad", "Pune", "Mumbai", "Delhi", "Chennai", 
            "Kolkata", "Noida", "Gurgaon", "Gurugram", "San Francisco", "New York", 
            "Seattle", "Austin", "Boston", "London", "Toronto", "Remote"
        ]
        for city in cities:
            if re.search(rf'\b{city}\b', text, re.IGNORECASE):
                return city
        return "Not Specified"

    def extract_social_links(self, text: str) -> Dict[str, Optional[str]]:
        """Extract LinkedIn, GitHub, and Portfolio URLs."""
        linkedin = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
        github = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
        
        return {
            "linkedin": linkedin.group(0) if linkedin else None,
            "github": github.group(0) if github else None
        }

    def extract_education(self, edu_text: str, full_text: str) -> Dict[str, Any]:
        """Extracts degree, major/branch, CGPA/percentage, and graduation year."""
        combined = edu_text if edu_text.strip() else full_text
        
        detected_degrees = []
        for pat, deg_name in self.DEGREE_PATTERNS:
            if re.search(pat, combined, re.IGNORECASE):
                detected_degrees.append(deg_name)
        if detected_degrees:
            degree = detected_degrees[0]
        elif re.search(r'\b(higher\s+secondary|class\s*(?:12|xii|10|x)|(?:12|10)th|hsc|ssc|high\s+school|secondary\s+school|intermediate)\b', combined, re.IGNORECASE):
            degree = "High School / Higher Secondary"
        else:
            degree = "Bachelor's (B.E./B.Tech Equivalent)"

        detected_branch = None
        for pat, branch_name in self.BRANCH_PATTERNS:
            if re.search(pat, combined, re.IGNORECASE):
                detected_branch = branch_name
                break
        if detected_branch:
            branch = detected_branch
        elif degree.startswith("High School"):
            branch = "General / Science Stream"
        else:
            branch = "Computer / Engineering Field"

        # CGPA / Percentage
        cgpa = None
        cgpa_match = re.search(r'(?:cgpa|gpa|score|percentage|grade)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:\/|\s*out of\s*)?\s*(?:10|4|100)?%?', combined, re.IGNORECASE)
        if cgpa_match:
            cgpa = cgpa_match.group(1).strip()
        else:
            # Check standalone decimals like 8.84/10 or 85.5%
            score_match = re.search(r'\b([0-9]\.[0-9]{1,2})\s*\/\s*(?:10|4)\b|\b([7-9][0-9](?:\.[0-9]+)?)\s*%\b', combined)
            if score_match:
                cgpa = score_match.group(1) or score_match.group(2)

        # Graduation Year
        grad_year = None
        years = re.findall(r'\b(20[12][0-9])\b', combined)
        if years:
            # Sort integer years and pick likely graduation
            int_years = sorted([int(y) for y in years])
            grad_year = str(int_years[-1])

        return {
            "degree": degree,
            "branch": branch,
            "cgpa": cgpa if cgpa else "N/A",
            "graduation_year": grad_year if grad_year else "N/A"
        }

    def extract_experience(self, exp_text: str, full_text: str) -> Dict[str, Any]:
        """Estimates total years of experience and detects job titles/companies."""
        combined = exp_text if exp_text.strip() else full_text
        
        # Look for explicit statements like "2.5 years of experience", "3+ years", "Fresher"
        exp_years = 0.0
        exp_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience', full_text, re.IGNORECASE)
        if exp_match:
            try:
                exp_years = float(exp_match.group(1))
            except ValueError:
                exp_years = 0.0

        # If not explicitly stated, compute from date ranges e.g. "2021 - 2023", "Jan 2022 to Present"
        if exp_years == 0.0:
            months = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
            date_ranges = re.findall(
                rf'(?:(?P<m1>{months})[a-z]*\.?\s*)?(?P<y1>\d{{4}})\s*(?:-|–|—|to)\s*(?:(?P<m2>{months})[a-z]*\.?\s*)?(?P<y2>\d{{4}}|present|current)',
                combined, re.IGNORECASE
            )
            month_no = {m: i for i, m in enumerate(months.split("|"))}
            current_year = datetime.now().year
            spans = []

            for m1, start, m2, end in date_ranges:
                try:
                    s_yr = int(start)
                    e_yr = current_year if end.lower() in ["present", "current"] else int(end)
                    # Inverted ranges (e.g. 2023 - 2019) are ignored as unreliable
                    if 1990 <= s_yr <= current_year and s_yr <= e_yr:
                        if m1 and m2 and s_yr == e_yr and end.lower() not in ["present", "current"]:
                            # Short range inside one year with both months ("Jan 2024 - Apr 2024"): count the real months
                            s_pt = s_yr + month_no[m1.lower()] / 12.0
                            e_pt = e_yr + (month_no[m2.lower()] + 1) / 12.0
                            if e_pt > s_pt:
                                spans.append((s_pt, e_pt))
                        else:
                            spans.append((s_yr, max(e_yr, s_yr + 0.5)))
                except Exception:
                    pass

            # Merge overlapping ranges so concurrent / duplicated dates are not double-counted
            total_months = 0
            merged_end = None
            merged_start = None
            for s_yr, e_yr in sorted(spans):
                if merged_end is None or s_yr > merged_end:
                    if merged_end is not None:
                        total_months += (merged_end - merged_start) * 12
                    merged_start, merged_end = s_yr, e_yr
                else:
                    merged_end = max(merged_end, e_yr)
            if merged_end is not None:
                total_months += (merged_end - merged_start) * 12

            if total_months > 0:
                exp_years = round(total_months / 12.0, 1)

        # Detect job titles
        titles_found = []
        for jt in self.JOB_TITLE_KEYWORDS:
            if re.search(rf'\b{re.escape(jt)}\b', combined, re.IGNORECASE):
                titles_found.append(jt)

        is_fresher = (exp_years < 0.8) or ("fresher" in full_text.lower())
        
        return {
            "years_of_experience": exp_years,
            "is_fresher": is_fresher,
            "detected_titles": titles_found[:5],
            "experience_level": "Fresher / Entry Level" if is_fresher else ("Mid Level (1-4 yrs)" if exp_years < 5 else "Senior (5+ yrs)")
        }

    def extract_projects(self, proj_text: str, full_text: str) -> List[Dict[str, Any]]:
        """Extracts notable project highlights and tech stacks."""
        target_text = proj_text if len(proj_text.strip()) > 40 else full_text
        projects: List[Dict[str, Any]] = []

        lines = [line.strip() for line in target_text.split('\n') if line.strip()]
        curr_proj = None
        bullets = ('•', '-', '*', '1.', '2.', '3.')
        # Resumes whose projects are written as "Title / sub-title lines / bullets": a new project starts only after
        # a finished bullet block, and wrapped bullet lines or sub-title lines belong to the current project.
        has_section = len(proj_text.strip()) > 40  # a real PROJECTS section (not the whole-resume fallback)
        block_style = has_section and any(l.startswith(bullets) for l in lines)
        in_bullets = False
        prev_line = ""

        for line in lines:
            is_bullet = line.startswith(bullets)
            if block_style and curr_proj:
                if is_bullet:
                    in_bullets = True
                else:
                    wrapped = in_bullets and (not prev_line.rstrip().endswith(('.', ':', '!', '?')) or line[:1].islower())
                    if wrapped or not in_bullets:
                        curr_proj["description"] += line + " "
                        curr_proj["skills_used"] = sorted(set(curr_proj["skills_used"] + extract_skills_from_text(line)))
                        prev_line = line
                        continue
                    in_bullets = False
            prev_line = line
            # Bullet point or header detection
            if len(line) < 70 and not is_bullet:
                skills_in_line = extract_skills_from_text(line)
                if curr_proj:
                    projects.append(curr_proj)
                curr_proj = {
                    "title": line,
                    "skills_used": skills_in_line,
                    "description": ""
                }
            elif curr_proj:
                curr_proj["description"] += line + " "
                more_skills = extract_skills_from_text(line)
                curr_proj["skills_used"] = sorted(list(set(curr_proj["skills_used"] + more_skills)))

        if curr_proj:
            projects.append(curr_proj)

        # If project list is empty or minimal, provide default extracted highlights
        if not projects:
            p_skills = extract_skills_from_text(target_text)
            if p_skills:
                projects.append({
                    "title": "Academic / Practical Implementations",
                    "skills_used": p_skills[:6],
                    "description": "Hands-on projects implementing core technical stack."
                })

        return projects[:6]

    def extract_certifications(self, cert_text: str, full_text: str) -> List[str]:
        """Extracts certifications and credentials."""
        target = cert_text if cert_text.strip() else full_text
        known_certs = [
            "AWS Certified", "AWS Solutions Architect", "Google Cloud Certified", 
            "TensorFlow Developer Certificate", "Deep Learning Specialization", 
            "Machine Learning Specialization", "Microsoft Certified: Azure", 
            "CKA (Certified Kubernetes Administrator)", "Oracle Certified Java", 
            "Scrum Master", "PMP", "CompTIA Security+"
        ]
        found = []
        for cert in known_certs:
            if re.search(rf'\b{re.escape(cert)}\b', target, re.IGNORECASE):
                found.append(cert)

        # Inline "Certifications: A, B - Issuer (2026)" lines anywhere in the resume
        for m in re.finditer(r'certifications?\s*:\s*([^|\n]+)', full_text, re.IGNORECASE):
            for part in re.split(r',\s+(?=[A-Z])', m.group(1)):
                part = part.strip(' .;')
                if 6 < len(part) < 90 and part not in found:
                    found.append(part)

        # Also extract individual lines from the certification section
        if cert_text.strip():
            for line in cert_text.split('\n'):
                line_str = line.strip().lstrip('•-*123456789. ')
                if 10 < len(line_str) < 90 and line_str not in found:
                    found.append(line_str)

        return found[:6]

    def parse(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        """
        Main entry point: Parses any supported resume file and returns a complete
        structured dictionary with all parsed entities.
        """
        raw_text, is_ocr = self.extract_text(file_bytes, file_name)
        sections = self.segment_sections(raw_text)

        name = self.extract_name(raw_text, sections["header"])
        email = self.extract_email(raw_text)
        phone = self.extract_phone(raw_text)
        location = self.extract_location(raw_text)
        socials = self.extract_social_links(raw_text)
        
        all_skills = extract_skills_from_text(raw_text)
        education = self.extract_education(sections["education"], raw_text)
        experience = self.extract_experience(sections["experience"], raw_text)
        projects = self.extract_projects(sections["projects"], raw_text)
        certifications = self.extract_certifications(sections["certifications"], raw_text)

        return {
            "file_name": file_name,
            "candidate_name": name,
            "email": email or "Not Provided",
            "phone": phone or "Not Provided",
            "location": location,
            "linkedin": socials.get("linkedin"),
            "github": socials.get("github"),
            "skills": all_skills,
            "education": education,
            "experience": experience,
            "projects": projects,
            "certifications": certifications,
            "sections": sections,
            "raw_text": raw_text,
            "is_ocr_used": is_ocr,
            "total_word_count": len(raw_text.split())
        }

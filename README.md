# 🎯 AI-Powered Intelligent Recruitment System (Phase 2 ATS)
### *Explainable Candidate Ranking, Skill Synonym Ontology, Skill Gap Analysis & AI Interview Assistance*

---

## 🌟 Overview & Academic Project Motivation
Modern recruitment involves hundreds of resumes per job opening. Traditional Phase 1 approaches only perform rudimentary keyword search or black-box text similarity (e.g., TF-IDF or raw cosine score), leading to recruiter frustration, false rejections, and zero explanation of why a candidate was ranked.

This project delivers a **production-ready Phase 2 Intelligent Recruitment System** that turns resume screening into an **explainable, multi-dimensional, and fair hiring workflow**.

```
                   JOB DESCRIPTION
                          ↓
                      JD PARSER
                          ↓
                Required & Preferred Skills
                          ↓
          ┌───────────────────────────────┐
          │                               │
          ↓                               ↓
    Resume Upload (PDF/DOCX/TXT)         OCR (Scanned PDFs)
          │                               │
          └───────────────┬───────────────┘
                          ↓
                 ADVANCED RESUME PARSER
                          ↓
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
        Skills        Experience      Education & Projects
          │               │               │
          └───────────────┼───────────────┘
                          ↓
               SKILL SYNONYM ONTOLOGY
            (1,500+ Skills, Aliases, Fuzzy)
                          ↓
               HYBRID MULTI-SCORE RANKING
       (Skills + Semantic BERT + Exp + Edu + Proj + Certs)
                          ↓
             EXPLAINABLE AI (XAI) ENGINE
                          ↓
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
      Skill Gap       Transparent      Candidate
      Analysis         Rationale       Comparison Radar
          │
          ↓
     AI INTERVIEW QUESTION GENERATOR
     (Tech + Projects + Gaps + Behavioral)
          │
          ↓
     RECRUITER ANALYTICS & DATABASE
     (SQLite History, Funnels, Email Gen)
```

---

## 🔥 Key Upgraded Features Implemented

| # | Feature | Capability Description |
|---|---|---|
| **1** | **Advanced Multi-Format Resume Parser & OCR** | Extracts candidate Name, Email, Phone, Location, Skills, Education (Degree, Branch, CGPA, Year), Experience (Years, Titles, History), Projects (Stack & Impact), and Certifications across **PDF**, **Scanned PDF (OCR)**, **DOCX**, and **TXT**. |
| **2** | **Skill Synonym & Ontology Knowledge Base** | Maps 1,500+ canonical technical skills with aliases (e.g. `ML` ↔ `Machine Learning`, `JS` ↔ `JavaScript`, `sklearn` ↔ `Scikit-Learn`, `k8s` ↔ `Kubernetes`, `FastAPI` ↔ `Flask`). |
| **3** | **Hybrid AI Multi-Score Ranking Engine** | Combines 7 weighted dimensions: 35% Skills Match, 20% Semantic JD Fit (BERT / SentenceTransformer), 15% Experience Alignment, 10% Education Credentials, 10% Project Depth, 5% Certifications, 5% ATS Resume Quality. |
| **4** | **Skill Gap Analysis** | Displays granular skill breakdown: **Matched Skills** (Green), **Partially Matched Skills** (Yellow with relationship rationale), and **Missing Skills** (Red). |
| **5** | **Explainable AI (XAI) & Rationale** | Transparent explanations: reasons why a candidate ranked high/low, key strengths, warning flags, and categorized recommendations (`Strongly Recommended`, `Recommended`, `HR Review`, `Not Recommended`). |
| **6** | **Candidate Comparison Matrix** | Side-by-side comparison of 2–4 candidates with **Plotly Radar charts**, dimensional metric comparisons, and skill overlap matrices. |
| **7** | **AI-Powered Interview Question Generator** | Automatically crafts customized Technical, Project-Specific, Gap-Probing, and Behavioral interview questionnaires with expected answers and difficulty levels. |
| **8** | **Resume ATS Quality Analyzer** | Generates a 0-100 ATS quality score, checks contact hygiene, section formatting, action verbs, quantified business impact, and gives actionable candidate resume tips. |
| **9** | **Fair & Bias-Aware Blind Screening Mode** | One-click toggle redacting names, photos, gender markers, contact details, and demographic clues for unbiased merit evaluation. |
| **10** | **Recruiter Search & Multi-Filters** | Recruiter filters by minimum score, experience range, must-have skills, education, and shortlist status. |
| **11** | **SQLite Screening History & Job Store** | Persistent SQLite database for saving multiple Job Descriptions, screening batches, past scores, and audit trails. |
| **12** | **Recruiter Analytics & Shortlist Email Gen** | Score distributions, talent pool skill frequency, gap bottlenecks, decision funnel donuts, and ready-to-send email invitation generator. |

---

## 🏗️ Project Architecture & File Organization

```
ai_recruitment_system/
├── app.py                      # Main Streamlit Interactive Application
├── run_app.py                  # Convenience launcher script
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & project guide
├── recruitment_system.db       # SQLite database (auto-generated)
│
├── src/
│   ├── core/
│   │   ├── skill_ontology.py   # Skill ontology, synonym aliases & matching
│   │   ├── resume_parser.py    # Multi-format parser (PDF, DOCX, TXT, OCR)
│   │   ├── jd_parser.py        # Job Description structured parser
│   │   ├── gap_analyzer.py     # Granular skill gap & category analyzer
│   │   ├── hybrid_ranker.py    # Multi-score weighted ranking engine
│   │   ├── explainable_ai.py   # XAI reasoning & recommendation classifier
│   │   ├── interview_generator.py # Contextual interview question synthesis
│   │   ├── quality_analyzer.py # ATS resume quality & suggestion engine
│   │   ├── bias_filter.py      # Blind recruitment PII anonymizer
│   │   ├── database.py         # SQLite persistence for jobs & sessions
│   │   └── llm_client.py       # Optional LLM integration (Gemini / OpenAI)
│   │
│   ├── ui/
│   │   ├── components.py       # CSS styling, badges, radar charts, bars
│   │   └── views/
│   │       ├── job_management.py      # Tab 1: JD setup & resume upload
│   │       ├── screening_results.py   # Tab 2: Ranked candidate leaderboard
│   │       ├── candidate_details.py   # Tab 3: Deep dive & XAI inspection
│   │       ├── candidate_comparison.py# Tab 4: Side-by-side radar matrix
│   │       ├── interview_assistant.py # Tab 5: AI interview preparation kit
│   │       └── analytics_dashboard.py # Tab 6: Recruiter charts & email gen
│   │
│   └── data/
│       └── generate_sample_resumes.py # Benchmark resume dataset generator
│
├── data/
│   └── sample_resumes/         # Pre-packaged PDF, DOCX, TXT test resumes
│       ├── Rahul_Nair_ML_Engineer.pdf
│       ├── Aarav_Sharma_Backend_Dev.docx
│       ├── Priya_Patel_Data_Analyst.pdf
│       ├── Sneha_Kulkarni_Fullstack_Dev.txt
│       ├── Vikram_Singh_Cloud_DevOps.docx
│       └── Ananya_Roy_Fresher_Engineer.pdf
│
└── tests/                      # Automated PyTest test suite
    ├── test_ontology.py
    ├── test_parser.py
    ├── test_hybrid_ranker.py
    └── test_database.py
```

---

## 🚀 Quick Start Guide

### 1. Launch the Application
In your terminal, navigate to the project folder and run:
```bash
python run_app.py
```
*Or via Streamlit directly:*
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### 2. Instant 1-Click Demo
1. Open **Tab 1 (Job & Upload)**: Select a pre-loaded template (e.g., *Machine Learning Engineer*).
2. Click **Load Built-in Benchmark Resumes** or drag and drop your own resumes.
3. Click **🚀 Run Screening & Rank Candidates** in the sidebar.
4. Explore **Tab 2 (Leaderboard)**, **Tab 3 (Candidate Deep-Dive & XAI)**, **Tab 4 (Comparison Radar)**, **Tab 5 (Interview Prep)**, and **Tab 6 (Recruiter Analytics)**!

### 3. Run Automated Tests
```bash
pytest tests/ -v
```
*All 6 test suites pass with 100% success.*

---

## 📐 Hybrid Scoring Formula

$$\text{Final Score} = \sum_{i=1}^{7} w_i \times S_i$$

Where:
- $S_{\text{skills}}$: Exact & synonym skill match score ($w_1 = 35\%$)
- $S_{\text{semantic}}$: Dense BERT / SentenceTransformer cosine similarity ($w_2 = 20\%$)
- $S_{\text{exp}}$: Experience alignment vs required minimum years ($w_3 = 15\%$)
- $S_{\text{edu}}$: Degree level, specialization & CGPA bonus ($w_4 = 10\%$)
- $S_{\text{proj}}$: Practical project depth & tech stack overlap ($w_5 = 10\%$)
- $S_{\text{cert}}$: Recognized industry certifications ($w_6 = 5\%$)
- $S_{\text{quality}}$: ATS formatting, action verbs & quantifiable metrics ($w_7 = 5\%$)

---

## 🎓 VTU Phase 1 vs Phase 2 Project Distinction

| Dimension | Phase 1 (Baseline) | Phase 2 (This System) |
|---|---|---|
| **Input Format** | Plain text / Simple PDF only | Multi-format PDF, Scanned PDF via OCR, DOCX, TXT |
| **Parsing** | Raw word tokenization | Structured entity extraction (Skills, Education, CGPA, Exp, Projects, Certs) |
| **Skill Understanding** | Exact string match only | 1,500+ Skill Ontology + Alias Expansion + Partial Relatedness |
| **Scoring** | Single Cosine / TF-IDF score | 7-Pillar Hybrid AI Multi-Score Ranking |
| **Transparency** | Black-box number (e.g. 78%) | Explainable AI (XAI) rationale, strengths, warnings, and recommendations |
| **Post-Screening** | None | Skill gap analysis, Side-by-side radar comparison, and AI Interview Question Generation |
| **Fairness** | Uncontrolled demographic bias | Bias-Aware Blind Screening Mode with PII redaction |
| **Persistence** | In-memory only | SQLite Database with historical audit sessions and email generator |

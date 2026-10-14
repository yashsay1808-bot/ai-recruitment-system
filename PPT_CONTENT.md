# PPT content: AI-Powered Intelligent Recruitment System (Phase 2 ATS)

Generated from `FINAL PPT - Recruitment.pptx` in this folder (28 slides), so it always matches the deck. Rebuild the deck with `build_pptx.py`, then regenerate this file.

**Not changed on purpose:** slides 1, 2 and 28 are the reference deck's own title, agenda and thank-you slides (the title slide and the agenda still need this team's names, title and guide).

Guide's rules followed: no generated photos; diagrams as shapes (draw.io/Canva style); implementation shown as one complete diagram, not module by module; methodology as a flow; at least 6 real papers; conclusion in sentences; future scope in 2-3 sentences.

All results come from `paper_results.json` / the report (12 resumes, offline TF-IDF mode); test counts: 49 pytest + 29 JavaScript = 78.

---

## Slide 1: Department Of Information Science And Engineering
- (picture) Picture 2
- MAJOR PROJECT PHASE II PRESENTATION
- ON
- “Bidirectional Indian Sign Language Translator Using Gesture Recognition”
- PRESENTED BY
- NIHARIKA P 1VK22IS038
- PADMAJA 1VK22IS040
- CHANDANA TN 1VK23IS401
- UNDER THE GUIDANCE OF
- MR.RAHUL J
- (picture) Picture 19
- (picture) Picture 1

## Slide 2: Introduction
- Problem Statement
- Literature Survey
- Objectives
- Methodology
- Architectural Design
- Implementation details of modules
- Data flow Diagram
- Interface Diagram
- Test case with results
- Results
- Conclusions
- References
- AGENDA
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 12
- (picture) Picture 2

## Slide 3: Introduction
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- Hiring teams receive hundreds of resumes for every opening, and screening them manually is slow, inconsistent and hard to scale.
- Most Applicant Tracking Systems (ATS) only count keyword matches, so they reward keyword stuffing and cannot tell that FastAPI and Flask are related skills.
- Automated screening is also under scrutiny for bias, and the EU AI Act treats recruitment AI as high-risk, so every decision must be explainable.
- In this project (Phase 2) we developed an explainable, bias-aware screening system that ranks candidates on seven weighted signals, hides identity during scoring and gives a reason for every verdict.
- (picture) Picture 22
- (picture) Picture 1

## Slide 4: Problem Statement
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 15
- Keyword-based ATS tools, like our Phase 1 system, only answer whether a resume contains the words of a job description. They cannot judge whether a skill claim is backed by evidence, they give no explanation when a candidate is rejected, and they can carry hidden bias from names and personal details. As a result, recruiters lose good candidates, trust inflated resumes and cannot justify their decisions. There is a need for a screening system that is accurate, explainable and bias-aware, so that hiring decisions are fair, consistent and auditable.
- (picture) Picture 2

## Slide 5: Literature Survey
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 30

| Sl.No | Title | Author | Contribution | Drawback |
|---|---|---|---|---|
| 1 | Enhancing Person-Job Fit for Talent Recruitment: An Ability-Aware Neural Network Approach | C. Qin, H. Zhu, T. Xu, et al. | A neural network that learns the abilities a job requires and matches them with the abilities shown in a resume, improving person-job fit prediction. | The learned model gives a match score without a human-readable reason and needs large amounts of historical hiring data. |
| 2 | End-to-End Resume Parsing and Finding Candidates for a Job Description Using BERT | V. Bhatia, P. Rawat, A. Kumar, R. R. Shah | Extracts structured fields from resumes with BERT and ranks candidates against a job description in one pipeline. | Produces a single similarity score, with no skill-gap breakdown and no check for bias. |

- (picture) Picture 2

## Slide 6
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 30

| Sl.No | Title | Author | Contribution | Drawback |
|---|---|---|---|---|
| 3 | Comparing BERT and Sentence-BERT for Automated Resume Screening | A. Deshmukh, A. R. Dahake | Compares BERT and Sentence-BERT embeddings for matching resumes to job descriptions. | Evaluates similarity quality only; explanation of the result and fairness are not addressed. |
| 4 | Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks | N. Reimers, I. Gurevych | Produces fast sentence embeddings that capture meaning, so "built REST services" matches "developed HTTP APIs". | A general text-similarity tool; it needs extra logic for skills, experience and fair decision-making. |
| 5 | Gender, Race, and Intersectional Bias in Resume Screening via Language Model Retrieval | K. Wilson, A. Caliskan | Audits language-model resume retrieval and shows that it can favour some names and groups over others. | An audit only; it does not propose a screening system that removes the bias. |

- (picture) Picture 1

## Slide 7
- (picture) Picture 1
- (picture) Picture 7
- (picture) Picture 6
- (picture) Picture 5
- (picture) Picture 4

| Sl.No | Title | Author | Contribution | Drawback |
|---|---|---|---|---|
| 6 | The Silicon Ceiling: Auditing GPT's Race and Gender Biases in Hiring | L. Armstrong, A. Liu, S. MacNeil, D. Metaxa | Shows that GPT-based hiring prompts can produce race- and gender-biased outcomes. | An audit only; no bias mitigation is built into a working pipeline. |
| 7 | Mitigating Bias in Algorithmic Hiring: Evaluating Claims and Practices | M. Raghavan, S. Barocas, J. Kleinberg, K. Levy | Examines the bias-mitigation claims made by hiring-algorithm vendors and evaluates them against technical and legal requirements. | An analysis of existing practice; it does not implement a screening system. |
| 8 | FA*IR: A Fair Top-k Ranking Algorithm | M. Zehlike, F. Bonchi, C. Castillo, S. Hajian, M. Megahed, R. Baeza-Yates | A re-ranking algorithm that keeps the top-k results fair to a protected group. | Needs protected attributes at ranking time and does not explain why a candidate received a score. |

- (picture) Picture 10

## Slide 8
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 22

| Sl.No | Title | Author | Contribution | Drawback |
|---|---|---|---|---|
| 9 | Improving Factuality and Reasoning in Language Models through Multiagent Debate | Y. Du, S. Li, A. Torralba, J. B. Tenenbaum, I. Mordatch | Several language-model agents debate and refine their answers, which improves reasoning and reduces errors. | Studied on general reasoning tasks, not on hiring decisions, and costs more computation. |
| 10 | A Comprehensive Survey of Artificial Intelligence Techniques for Talent Analytics | C. Qin, et al. | Surveys AI techniques used across talent analytics, such as recruitment, including matching and ranking methods. | A survey; it does not provide an implemented, explainable and bias-aware screening pipeline. |

- (picture) Picture 2
- Research gap: existing work is either accurate but a black box, or an audit of bias with no fix. None combines semantic ranking, skill-synonym understanding, blind screening and a multi-agent explanation in one system.

## Slide 9: Objectives
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- 1. To Design: an explainable screening workflow that shows why every candidate was ranked and which skills are missing.
- 2. To Implement: a hybrid ranker that combines skills, semantic fit, experience, education, projects, certifications and resume quality.
- 3. To Build: a skill-synonym ontology with skill-gap analysis that shows matched, partial and missing skills.
- 4. To Minimize: bias with a blind-screening mode that hides names and personal details before any scoring.
- 5. To Accomplish: fast, auditable hiring decisions through a four-agent review council and a FastAPI service.
- (picture) Picture 1

## Slide 10: Methodology
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- 1 Input
- Job description + resumes (PDF, DOCX, TXT, scanned)
- 2 Parsing
- Skills, experience, education, projects
- 3 Blind Screening
- Name and personal details hidden
- 4 Skill Ontology
- Synonyms and partial matches
- 5 Hybrid Ranking
- Seven weighted scores give match %
- 6 Council Review
- Four agents score and debate
- 7 Explainable Verdict
- Score, red flags, rationale
- 8 Recruiter Dashboard
- Leaderboard, compare, export
- Every stage is logged in the screening history, so each ranking can be audited later.

## Slide 11: Architectural Design
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- Presentation
- React web app
- Nexus ATS (Vercel)
- Streamlit app
- Recruiter workspace
- Recruiter dashboard
- Leaderboard, interview kit, chatbot
- Service
- FastAPI REST service
- Screening engine and accounts (Render)
- Secure sign-in
- Hashed passwords, 7-day sessions, Google verified on the server
- Intelligence engine
- Resume parser
- PDF, DOCX, TXT, OCR
- Skill ontology
- Synonyms, partial credit
- Hybrid ranker
- 7 weighted scores
- Four-agent council
- Verdict + red flags
- Interview kit
- 20+ tailored questions
- Data
- MongoDB Atlas
- Accounts, sessions, candidate pools
- SQLite history
- Screening runs, audit trail
- Job roles
- Required and preferred skills

## Slide 12: Implementation
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- Job Description
- Pasted by the recruiter
- Resume Upload
- PDF, DOCX, TXT, scanned (OCR)
- JD Parser
- Required and preferred skills
- Resume Parser
- Skills, experience, education, projects
- Blind Screening (optional)
- Names and contact details replaced by Candidate #00N
- Skill Ontology
- Synonyms, partial credit
- Hybrid Ranker
- 7 weighted scores = match %
- Verdict + Dashboard
- Skill gap, interview kit, chatbot
- Four-Agent Council
- Tech Lead, Culture, Fair Auditor, Seniority
- Input: the job description and resumes are parsed into structured profiles.
- Fairness: blind screening hides identity before any scoring.
- Scoring: the ontology feeds a ranker that blends seven signals.
- Decision: four agents score, debate and give a verdict with red flags.
- Output: leaderboard, skill gap, a 20-question interview kit and a chatbot; the engine is served through FastAPI, with accounts and candidate pools in MongoDB Atlas.

## Slide 13: Hybrid Ranking Model
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (chart) Weight (%): Skills=35.0, Semantic JD fit=20.0, Experience=15.0, Education=10.0, Projects=10.0, Certifications=5.0, Resume quality=5.0
- Match % is the weighted sum of seven scores, each from 0 to 100.
- Skills (35%): required skills are matched through the ontology; related skills get partial credit (FastAPI through Flask counts 0.5).
- Semantic fit (20%): TF-IDF and BM25 offline, Sentence-BERT when installed.
- Evidence weighting: a skill that is listed but never shown in a project or result counts for less.
- Flags: experience deficit, skill stuffing and date inconsistency lower the verdict.

## Slide 14: Four-Agent Council And Explainability
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (chart) Score: Tech Lead=88.8, Culture=78.0, Fair Auditor=98.8, Seniority=100.0, Consensus=91.4
- Tech Lead: checks skill coverage, evidence and architecture signals.
- Culture: judges stability and retention risk.
- Fair Auditor: checks that the decision is neutral and bias-free.
- Seniority and Compensation: compares experience with the role level.
- Consensus: the agents cross-examine each other, then give one verdict (Strong Hire, Lean Hire or Reject) with red flags and a debate transcript.

## Slide 15: Data Flow Diagram
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- Resume screening flow:
- The recruiter signs in and uploads the job description and the resumes.
- Each resume is parsed into skills, experience, education, projects and certifications.
- Blind screening, when switched on, hides the name and personal details.
- Every candidate is scored on seven signals using the skill ontology.
- The four-agent council reviews the scores and gives a verdict with red flags.
- Results are shown on the dashboard, and the API also saves them to the screening history.
- Recruiter signs in, uploads JD + resumes
- Resume parsing
- Blind screening (optional)
- Scoring on 7 signals
- Council verdict + flags
- Dashboard + saved history

## Slide 16: Council decision flow:
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- The scored candidate profile, anonymised when blind screening is on, is sent to the council.
- Four agents score it independently: Tech Lead, Culture, Fair Auditor and Seniority.
- The agents debate and cross-examine each other's findings.
- A consensus score and a confidence value are calculated.
- The verdict (Strong Hire, Lean Hire or Reject) is issued with red flags and a rationale.
- Low-confidence cases are marked for human review.
- Scored candidate profile
- Tech Lead
- Culture
- Fair Auditor
- Seniority
- Debate and cross-examination
- Consensus score + confidence
- Verdict + red flags
- Low confidence: human review

## Slide 17: Interface Design
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (picture) Picture 30
- (picture) Picture 31
- Sign-in (live site)
- Interview assistant: tailored question kit

## Slide 18: Test Cases With Results
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1

| Test resume | Scenario | Match % | ATS | Verdict | Red flags |
|---|---|---|---|---|---|
| Gold Standard | Strong ML engineer with evidence of results | 88.1 | 100 | STRONG HIRE | None |
| Buzzword Exaggeration | 35 listed skills, 4 months of experience, no metrics | 41.6 | 56 | REJECT | Experience Deficit, Unverified Skill Claims, Skill Stuffing |
| Lateral Partial Match | Flask developer; FastAPI credited through Flask | 61.3 | 92 | LEAN HIRE | Required skills missing |
| Corrupt ATS Format | Damaged layout and inconsistent dates | 34.0 | 23 | REJECT | No Quantified Impact, Date Inconsistency |

- Each resume was run through the live pipeline. The gold-standard candidate ranks 1 of 12 resumes, and every rejected resume is shown with the reason for the rejection.

## Slide 19: Test Cases With Results (Contd.)
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1

| Test resume | What it checks | Phase 1 keyword score | Phase 2 hybrid score | Council score |
|---|---|---|---|---|
| Gold Standard | No inflated perfect score for a strong candidate | 100.0 | 88.1 | 91.4 |
| Buzzword Exaggeration | Stuffed skills are not rewarded | 47.1 | 41.6 | 50.3 |
| Lateral Partial Match | Related skills earn partial credit | 47.1 | 61.3 | 76.0 |
| Corrupt ATS Format | Damaged resume is still scored and flagged | 0.0 | 34.0 | 38.5 |

- Fairness test: swapping a candidate's name changed no score (maximum change 0.0) in plain or blind mode.
- Ablation: without evidence weighting, two REJECT verdicts would have become LEAN HIRE.

## Slide 20: Results
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (chart) Phase 1 keyword: Gold Std=100.0, Rahul N.=88.2, Test 3=47.1, Sneha K.=41.2, Vikram S.=29.4, Kavita M.=52.9, Aarav S.=35.3, Ananya R.=35.3, Priya P.=23.5, Test 2=47.1, Test 4=0.0, Edge case=5.9
- (chart) Phase 2 hybrid: Gold Std=88.1, Rahul N.=82.3, Test 3=61.3, Sneha K.=56.0, Vikram S.=50.1, Kavita M.=47.4, Aarav S.=46.1, Ananya R.=46.1, Priya P.=45.3, Test 2=41.6, Test 4=34.0, Edge case=28.3
- 88.1%
- top match score, gold-standard resume (rank 1 of 12)
- 29.6 ms
- total time per resume: parse 18.0, rank 3.8, council 7.8
- 0.0
- score change when a candidate's name is swapped
- 0.97
- average rank correlation over 200 random weight changes

## Slide 21: Results (Contd.)
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (picture) Picture 31
- (picture) Picture 32
- (a) Leaderboard with verified evidence
- (b) Blind screening on: identities hidden

## Slide 22: Recruiter Copilot
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (picture) Picture 31
- (picture) Picture 32
- (a) Red-flag audit of the screened pool (b) Follow-up questions with clickable suggestions

## Slide 23: Speed And Robustness
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (chart) ms per resume: Parse=18.0, Rank=3.8, Council=7.8, Total=29.6
- Fast: about 30 ms per resume end to end, fully offline.
- Stable: over 200 random changes to the scoring weights, the top candidate stayed first in every run and the average rank correlation was 0.97.
- Fair: swapping names changed no score, in plain or blind mode.
- Evidence matters: removing evidence weighting turned two REJECT verdicts into LEAN HIRE.
- Different from Phase 1: rank correlation with the keyword baseline is only 0.67, so the ranking really changed.

## Slide 24: Benchmark Pool Of 50 Resumes
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- (chart) Candidates: Strong Hire=10.0, Lean Hire=10.0, Reject=30.0
- 50 synthetic resumes of different types were screened for the Senior Machine Learning Engineer role.
- Top match: 93.2%, the gold-standard Data Platform Engineer with zero red flags.
- Average match: 56.9% across the pool.
- Verdicts: 10 Strong Hire, 10 Lean Hire and 30 Reject; 30 resumes carried at least one red flag.

## Slide 25: Conclusion
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- The AI-Powered Intelligent Recruitment System shows that resume screening can be fast, explainable and fair at the same time. It ranks candidates on seven weighted signals instead of simple keyword counts, understands related skills through a skill ontology, and hides identity details through blind screening before anyone is scored.
- Every decision comes with a verdict, red flags and a reason, so recruiters can justify it. In testing, the system placed the strong candidate first and rejected resumes with inflated or badly formatted content, while processing each resume in about 30 milliseconds. Changing a candidate's name did not change any score. The system is also deployed as a multi-user web service with server-side authentication and a managed database.
- Overall, the project shows that explainable AI can make hiring more transparent, consistent and trustworthy.

## Slide 26: Future Scope
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- The deployed system can be extended with role-based access, candidate consent and data-retention controls, and a stored screening history for each account.
- A larger set of labelled real hiring data can be used to validate and tune the scoring weights, and the evidence checks can be extended to LinkedIn, portfolios and resumes in more languages.
- Email and ATS integrations and a load test would prepare it for production use.

## Slide 27: References
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- (picture) Picture 1
- [1] C. Qin et al., "Enhancing person-job fit for talent recruitment: An ability-aware neural network approach," ACM SIGIR, 2018.
- [2] V. Bhatia, P. Rawat, A. Kumar, and R. R. Shah, "End-to-end resume parsing and finding candidates for a job description using BERT," arXiv:1910.03089, 2019.
- [3] A. Deshmukh and A. R. Dahake, "Comparing BERT and Sentence-BERT for automated resume screening," IAES Int. J. Artif. Intell., vol. 14, no. 4, 2025.
- [4] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," EMNLP-IJCNLP, 2019.
- [5] K. Wilson and A. Caliskan, "Gender, race, and intersectional bias in resume screening via language model retrieval," AAAI/ACM AIES, 2024.
- [6] L. Armstrong, A. Liu, S. MacNeil, and D. Metaxa, "The silicon ceiling: Auditing GPT's race and gender biases in hiring," arXiv:2405.04412, 2024.
- [7] M. Raghavan, S. Barocas, J. Kleinberg, and K. Levy, "Mitigating bias in algorithmic hiring: Evaluating claims and practices," ACM FAT*, 2020.
- [8] M. Zehlike et al., "FA*IR: A fair top-k ranking algorithm," ACM CIKM, 2017.
- [9] Y. Du et al., "Improving factuality and reasoning in language models through multiagent debate," ICML, 2024.
- [10] C. Qin et al., "A comprehensive survey of artificial intelligence techniques for talent analytics," arXiv:2307.03195, 2023.

## Slide 28: Thank
- (picture) Picture 4
- (picture) Picture 5
- (picture) Picture 6
- (picture) Picture 7
- (picture) Picture 10
- YOU!

---

### Before you present, check these
1. Slides 1 and 2 still show the reference deck's title, team and agenda; replace them with this team's details.
2. All numbers are from the offline TF-IDF mode (no sentence-transformers installed); say "high 80s", not exactly 90.
3. The contribution and drawback lines in the literature survey are summaries; skim each paper's abstract to confirm them. Deshmukh and Dahake (2025) has not been checked against a database.
4. The live site is https://ai-recruitment-system-lemon.vercel.app (API: https://ai-recruitment-api-7blc.onrender.com); the free API tier sleeps when idle, so open /health a minute before demonstrating.
5. The 12 / 50 / 100 pool scores shown on the web dashboard were computed offline by the Python pipeline; only uploaded resumes are scored in the browser.

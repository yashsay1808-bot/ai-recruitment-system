# Viva Defense Guidebook - AI-Powered Intelligent Recruitment System (Phase 2 ATS)

Every number in this guide was produced by running the real pipeline (`python scripts/verify_test_suite.py`). If the
live screen differs by a decimal, say "scores are computed, not hard-coded" and move on.

---

## 1. The 30-second elevator pitch

> "Phase 1 was a keyword-matching ATS: it counted how many JD words appeared in a resume, so it rewarded buzzword
> stuffing and could not tell `FastAPI` from `Flask`. Phase 2 is an *explainable, auditable* decision system. A
> hybrid ranker blends seven weighted signals including dense semantic similarity; a skill ontology understands
> synonyms and partial matches; Blind Screening removes identity before anyone scores a resume; and a four-agent
> council - Tech Lead, Culture, Fair-Hiring Auditor, Compensation - debates every candidate and returns a verdict
> with red flags and a transcript. It all runs offline, and a FastAPI service exposes the same engine to other systems."

Key contrast to say out loud: **Phase 1 answers "does it contain the words?" Phase 2 answers "is the claim evidenced, is it fair,
and can I explain the decision?"**

---

## 2. The 2-minute live demo script

Setup (before she walks in): `python run_app.py`, browser on `http://localhost:8501`, click
**"Instant Login as Lead Recruiter"**. The app auto-screens the 12 resumes in `data/sample_resumes/`.

| Time | Click | What she says |
|---|---|---|
| 0:00 | **Command Center** (landing tab) | "This is the telemetry strip: 12 candidates screened live, the model status pill shows which engine is active, and the banner shows the active role - Machine Learning Engineer, 17 required skills." |
| 0:15 | Click the prompt pill **"Engineers with 2+ years in Python and PyTorch"** | "This is hybrid RAG: dense embeddings plus BM25 over resume chunks. It returns the matching evidence snippet, not just a name." |
| 0:30 | Scroll the leaderboard | "#1 is Karthik Menon, 88%, Strong Hire, zero red flags - 3 years, p95 latency 72 ms, 50,000 requests/day. Bars animate from the real score." |
| 0:45 | Click **Inspect** on Karthik, open **Council & GitHub** | "Four specialists score independently: Tech Lead 89, Culture 78, Fair Auditor 99, Seniority 100. Consensus 91, Strong Hire." |
| 1:00 | Expand **debate transcript**, press **Replay debate live** | "They cross-examine each other. Every verdict is auditable - nothing is a black box." |
| 1:15 | Scroll to the **GitHub Authenticity** widget, choose *Offline demo*, run | "Authenticity ring and exaggeration-risk meter. This mode is clearly labelled simulated so we do not depend on Wi-Fi; the scoring code is the real one. With internet, switch to Live." |
| 1:30 | Inspect **Test_Case_2** (Rohit Verma) | "35 listed skills, 4 months of experience, no metrics. 41.6% and REJECT, flagged for experience deficit and unverified/stuffed skills. Buzzwords do not survive." |
| 1:45 | Toggle **Blind screening** | "Names become Candidate #00N and the council only sees the anonymized copy - bias is removed at the data layer." |
| 1:55 | Right rail: click **Compare the top 2 candidates**, then **Export Markdown** | "The copilot answers from the screened pool, and the session exports to Markdown in one click." |

If time remains: Test_Case_3 (Flask developer) shows **partial credit** - FastAPI is credited at 0.5 through Flask, PyTorch is shown missing,
verdict LEAN_HIRE. Test_Case_4 shows an ATS format score of 23/100 and a DATE_INCONSISTENCY flag.

### Expected results of the four test resumes (verified)

| Resume | Match | ATS | Council verdict | Red flags |
|---|---|---|---|---|
| `Test_Case_1_Gold_Standard_Pass` | 88.1% (rank 1) | 100 | STRONG_HIRE (91.4) | none |
| `Test_Case_2_Buzzword_Exaggeration_Fail` | 41.6% | 56 | REJECT | EXPERIENCE_DEFICIT, UNVERIFIED_SKILL_CLAIMS, SKILL_STUFFING |
| `Test_Case_3_Lateral_Partial_Match` | 61.3% | 92 | LEAN_HIRE | REQUIRED_SKILLS_MISSING |
| `Test_Case_4_Corrupt_ATS_Format_Error` | 34.0% | 23 | REJECT | DATE_INCONSISTENCY, NO_QUANTIFIED_IMPACT |

Note: the gold candidate scores 88% (not 90%) because the offline TF-IDF fallback produces the semantic component. With
`sentence-transformers` installed (MiniLM) the semantic term changes slightly. Say "high 80s". Do not promise exactly 90.

---

## 3. The seven hardest viva questions - and winning answers

**Q1. Why dense SentenceTransformers instead of TF-IDF?**
TF-IDF is lexical: "built REST services" and "developed HTTP APIs" share no tokens, so cosine similarity is near zero. A
sentence embedding (`all-MiniLM-L6-v2`, 384-d) places both sentences close together, so it matches meaning. We keep TF-IDF as a deliberate
*fallback* so the system works offline and in the viva room, and the RAG layer fuses dense and **Okapi-BM25** scores because BM25 is
better at exact rare tokens (e.g. "PyTorch", "Kubernetes"). Honest limitation: embeddings can over-match
generic text, which is why semantic similarity is only 20% of the score and skills evidence carries more.

**Q2. How does the Skill Ontology handle synonyms without hallucinating?**
It is a deterministic dictionary, not a generative model. `normalize_skill()` maps variants ("sklearn", "Scikit Learn",
"JS", "k8s") to one canonical name; `match_skills()` returns three buckets - matched, partially matched and missing.
Partial credit comes only from an explicit `related_pairs` table (FastAPI<->Flask, etc.) and counts 0.5. Nothing is
invented: if a skill is not in the ontology or the resume, it is reported missing. Every match is traceable to a rule,
which is why we can explain it. (An LLM can hallucinate a skill; a lookup table cannot.)

**Q3. How does Blind Screening actually prevent bias?**
At the **data layer**, not the display layer. `BiasFilter.anonymize_candidate()` replaces the name with `Candidate #00N`
and redacts name occurrences, email, phone and links in the raw text *before* the council evaluates. The UI also
masks names. The Fair Hiring Auditor then checks for non-merit signals and produces a merit-only score. Be honest: this removes
direct identifiers; it cannot remove proxy bias (e.g. a college name), which is why the auditor flags it and
a human review flag is raised when confidence is low.

**Q4. Why FastAPI plus a Streamlit frontend? Why not one app?**
Separation of concerns. The core engine (`src/core`) is framework-free. Streamlit is a fast analyst UI;
FastAPI (`python run_api.py`, port 8000, `/api/v1/jobs|resumes|screenings|audits`) lets an HR system, a mobile app or a React
dashboard use the same engine, with Pydantic validation and an SQLAlchemy persistence layer (`db/`, `services/`) and auto-generated Swagger docs at
`/docs`. Streamlit would not scale to multiple clients or give us a stable contract; FastAPI does. Both share one scoring implementation, so
results never diverge.

**Q5. How does the multi-agent council reach consensus?**
Four rule-based specialists score 0-100 independently: Tech Lead (35%), Fair-Hiring Auditor merit score (25%), Culture &
Retention (20%), Seniority fit (20%). A cross-examination debate runs, then a weighted consensus is mapped to a verdict
(>=80 Strong Hire, >=68 Hire, >=55 Lean Hire, else Reject). **Gates override the average**: a high-severity red flag (large
experience deficit, <25% evidenced required skills, impossible dates) caps the verdict, so a high mean cannot hide a fatal flaw. Disagreement between
agents is reported as *dissent*, and low confidence or scores near a threshold set `human_review_required`. It is a
decision-*support* system - a human makes the final decision. The LLM is optional and only writes the narrative; the verdict stays deterministic.

**Q6. How do you detect keyword stuffing / exaggeration?**
Skills listed in a Skills block are not counted as evidence. We strip that block and check whether each required skill appears
in experience/projects text (`evid_coverage`; listed-but-unevidenced skills get half credit). Test_Case_2 lists 35 skills with 4 months of
experience and no metrics, so the evidence ratio is low and the council raises UNVERIFIED_SKILL_CLAIMS and SKILL_STUFFING. The GitHub inspector
adds an external check: claimed languages vs. actual repository language percentages.

**Q7. How was the system validated, and what are its limits?**
78 automated tests (49 with `pytest`, 29 with `npm test` in `frontend/`) cover parser, ontology, ranker, council, GitHub inspector, RAG, database,
accounts, sessions and Google sign-in (MongoDB, tested in memory), the four demo resumes with asserted outcomes, a headless boot of the UI, and the
interview kit and chatbot of the web dashboard on all 162 candidates. `scripts/verify_test_suite.py` prints the full table. Limits to state proactively: rules and
weights were chosen by us, not learned from labelled hiring outcomes; compensation bands are *indicative* planning ranges; GitHub
checks need network (offline demo is simulated and labelled); the sample set is small (12 resumes). Future work: learn weights from
recruiter feedback, calibrate on a labelled dataset, add fairness metrics (e.g. adverse-impact ratio).

---

## 4. Troubleshooting & setup cheat sheet

```bash
pip install -r requirements.txt
python run_app.py            # Streamlit UI  -> http://localhost:8501
python run_api.py            # FastAPI       -> http://localhost:8000   (Swagger: /docs)
python scripts/verify_test_suite.py   # prints the 12-resume results table
python -m pytest -q          # 49 tests
cd frontend && npm test      # 29 tests (interview kit and chatbot logic)
```

**Deployed system:** web dashboard on Vercel, FastAPI on Render, MongoDB Atlas for accounts, sessions and candidate pools (see `README.md` and `DEPLOY.md`). The report, the deck and their sources are in `docs/`.

| Symptom | Fix |
|---|---|
| Login screen appears | Click **Instant Login as Lead Recruiter** (demo user `recruiter@techcorp.com` / `password123`). |
| Port 8501 busy | `streamlit run app.py --server.port 8502` |
| "Dense embedding model notice ... TF-IDF fallback" | Expected offline. Not an error. Install `sentence-transformers` and let the first run download MiniLM *before* the viva. |
| First load slow | MiniLM download/first import. Warm it up once beforehand. |
| Results look stale after changing the JD | Press **Run Screening & Rank Candidates** in the sidebar. |
| GitHub widget cannot reach the API | Switch the radio to **Offline demo**. Live mode may also be rate-limited (60 req/h without token). |
| LLM / Gemini key missing | Leave it blank - the council and chatbot use their local deterministic engines. |
| Model pill says "API :8000 idle" | Only means the FastAPI server is not running; start `python run_api.py` if you want it green. |
| Odd sidebar page names | These are the multipage file names; use the top tabs for the demo. |
| Database error | Delete `recruitment_system_v4.db` (it is recreated on start). |

**Offline mode checklist:** no network needed for parsing, ranking, ontology, council, RAG (TF-IDF+BM25) and the chatbot. Only
live GitHub verification and optional LLM narrative use the network.

**Before the viva:** run the app once end-to-end, keep a second terminal with `python scripts/verify_test_suite.py` ready as a backup if the browser fails.

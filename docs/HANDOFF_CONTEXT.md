# Handoff: AI Recruitment System — report, PPT and research-paper context

Written 2026-10-14 from the Claude session that produced the PPT content and the project report.
Paste or attach this file in your new session so it knows what already exists.

> **Update, same day (see `CHANGES_FOR_REPORT_AND_PPT.md`):** the project was moved to the second team member's accounts and extended (MongoDB Atlas, server-side accounts, Google sign-in verified on the server, a 19-24 question interview kit, a conversational chatbot, 78 automated tests). The report and deck in this folder were updated for it. Where this file says otherwise, the update wins: the repo is now `yashsay1808-bot/ai-recruitment-system`, the live site is `https://ai-recruitment-system-lemon.vercel.app`, the API is `https://ai-recruitment-api-7blc.onrender.com`, the test count is 78 (not 31), the report has 121 pages, and the file paths in section 8 now work from this folder (`make_report.py` writes next to `source/`, `build_pptx.py` writes next to itself).

---

## 1. The project in one paragraph

**Title (as on the team's title slide):** *AI-Powered Intelligent Recruitment System: Explainable, Bias-Aware Candidate Ranking*
(The IEEE paper manuscript uses a longer title: *An Explainable Multi-Agent AI Recruitment System with Hybrid Skill Ontology, Bias-Aware Auditing, and RAG Copilot*.)

**Team (spelling taken from the title image the user sent):**
| Name | USN |
|---|---|
| MITHILA R | 1VK23IS034 |
| SNEHA | 1VK23IS052 |
| YASHASWINI R | 1VK23IS062 |

Dept. of Information Science and Engineering, Vivekananda Institute of Technology (VKIT), Bengaluru, VTU. Academic year 2026–2027. **Guide / HOD / Principal names are unknown** — placeholders `[Guide name]`, `[Designation]`, `[HOD name]`, `[Principal name]` are in the report. (The old PPT title slide still shows another team's names and guide — Niharika P, Padmaja, Chandana TN, Mr. Rahul J — and was deliberately left untouched.)

**System ("Nexus ATS"):** Phase 2 of a keyword ATS. Treats a skill as a *claim that needs evidence*. Python core + FastAPI + SQLAlchemy + Streamlit + React 19 dashboard. 31 pytest tests pass (re-run this session: `31 passed in 12.82s`).

---

## 2. Where everything is

| What | Location |
|---|---|
| Project repo (GitHub: `Ravva-78/ai-recruitment-system`, branch `main`, commit `0711e94`) | `C:\DEV\Projects\Experiments\ai_recruitment_system` |
| Live site (Vercel) | https://ai-recruitment-system-rho.vercel.app |
| **PPT (new, recruitment content)** | `C:\Users\Arjun\Downloads\FINAL PPT - Recruitment.pptx` (copy in `ppt_source/`) |
| PPT original (sign-language project, untouched) | `C:\Users\Arjun\Downloads\FINAL PPT.pptx` |
| PPT slide text (copy-paste version) | `content_notes/PPT_CONTENT.md` (also in the repo root as `PPT_CONTENT.md`, untracked) |
| PPT build script | `ppt_source/build_pptx.py` |
| **Report (.docx)** | `C:\Users\Arjun\Downloads\major_project_final_report - Recruitment.docx` (copy in this folder) |
| Report preview PDF | `major_project_final_report - Recruitment (preview).pdf` |
| Report generator source | `report_source/` (builder, ch1–ch9, diagrams, charts, refs, screenshots) |
| Template the report copies | `C:\Users\Arjun\Downloads\major_project_final_report-2.docx` (**another team's** network-intrusion-detection report — used for format only) |
| Reference deck sent by user | `C:\Users\Arjun\Downloads\FINAL PPT.pptx` (28 slides, VKIT template) |
| Guide's instructions | WhatsApp screenshot (rules below). Three `.ogg` voice notes were sent as context; **they could not be played or transcribed**, so their content is unknown to this session. |
| Research paper (IEEE manuscript) | `ai_recruitment_system\paper\main.tex` (+ `paper_results.json`, `paper/figs_work/*.png`); a compiled PDF is also in Downloads: `An_Explainable_Multi_Agent_AI_Recruitment_System_with_Hybrid_Skill_Ontology__Bias_Aware_Auditing__and_RAG_Copilot.pdf` |

---

## 3. The guide's rules (from the WhatsApp screenshot) — apply to PPT *and* report

1. **No generated photos/images** in the PPT or the report.
2. Use **Canva or draw.io** for diagrams. Do **not** show implementation module-wise; show the **complete implementation in one diagram with explanation**.
3. **Methodology** should be shown **as a flow**, not sentences.
4. **Literature survey: at least 6 papers**, none ChatGPT-generated (i.e. real, verifiable).
5. **Conclusion in sentences**; **future scope in sentences, 2–3**.

---

## 4. What was done in this session

### 4.1 Git / local folder
- Pulled `Ravva-78/ai-recruitment-system` (fast-forward `c209653 → 0711e94`). The pull deleted the two tracked `.db` files (repo stopped tracking them). Local folder now matches GitHub; `git status` shows many "modified" files that are **only CRLF line endings** (no content diffs).
- A fresh clone from GitHub asked for credentials (needs auth), so a fresh copy was made from the local repo instead: `C:\DEV\Projects\Experiments\ai-recruitment-clone2`. A half-deleted `ai-recruitment-system-clone` folder may remain and can be deleted.
- Frontend was run locally with Vite (ports 5173 and 5174). Those dev servers have since stopped.
- **Google sign-in does not show locally** because `frontend/.env` is git-ignored: it needs `VITE_GOOGLE_CLIENT_ID` (copy from Vercel → Settings → Environment Variables) and `http://localhost:5173` / `http://127.0.0.1:5173` as Authorized JavaScript origins in Google Cloud Console. On Vercel it works (button renders; "Only @gmail.com accounts are accepted").

### 4.2 PPT — `FINAL PPT - Recruitment.pptx`
Built as an edited **copy** of the reference deck (same VKIT header/footer/layouts). Slides **1, 2 and 28 are byte-identical to the original** (user asked to keep them as is — so the title slide and the agenda still describe the sign-language project; the agenda still says "Implementation details of modules"). Slides 3–27 are rewritten for the recruitment project:

| Slide | Content |
|---|---|
| 3 | Introduction |
| 4 | Problem statement |
| 5–8 | Literature survey table, **10 real papers** (all from the paper's reference list) + "Research gap" box on slide 8 |
| 9 | Objectives (To Design / Implement / Build / Minimize / Accomplish) |
| 10 | Methodology as an 8-step arrow flow |
| 11 | Architecture (4 layers) |
| 12 | Implementation = **one full-system diagram** + short explanation (guide's rule) |
| 13 | Hybrid ranking model (native weight chart) |
| 14 | Four-agent council (native score chart) |
| 15–16 | Data-flow diagrams (resume screening flow; council decision flow) |
| 17 | Interface design (real screenshots) |
| 18–19 | Test cases (tables) |
| 20–24 | Results (charts, stat cards, real screenshots, verdict doughnut) |
| 25 | Conclusion (sentences) |
| 26 | Future scope (3 sentences) |
| 27 | References (10) |

All shapes/charts are native PowerPoint objects (editable). Images are real screenshots only.
PPT literature-survey papers: Qin 2018 (person-job fit), Bhatia 2019 (BERT resume parsing), Deshmukh & Dahake 2025 *(note: in the PPT; this one was **not** verified against a database — see §7)*, Reimers & Gurevych 2019 (SBERT), Wilson & Caliskan 2024, Armstrong 2024, Raghavan 2020, Zehlike 2017 (FA*IR), Du 2024 (multi-agent debate), Qin 2023 (talent-analytics survey).

### 4.3 Report — `major_project_final_report - Recruitment.docx`
**110 pages**, A4, Times New Roman, VTU-style. ~25,000 words, 28 native Word equations, 32 tables, 29 figures, 80 references. Structure (matches the template's chapters):

- Cover · Certificate (i) · Declaration (ii) · Acknowledgement (iii) · **Abstract (iv)** · Table of Contents · List of Figures · List of Tables · List of Abbreviations (54)
- **Ch 1 Introduction** (1.1 General Overview … 1.11 Organization)
- **Ch 2 Literature Survey** (~28 papers with full author lists, Table 2.1 summary, 2.2 Research Gaps G1–G7)
- **Ch 3 Preliminaries** (Python, parsing/OCR, TF-IDF, dense embeddings, BM25 + hybrid fusion, ontology & fuzzy matching, XAI & fairness, multi-agent, metrics) — equations (3.1)–(3.15)
- **Ch 4 Requirement Specifications** (functional FR1–FR15, non-functional 4.2.1–4.2.8, hardware, software table, user requirements)
- **Ch 5 System Design** (workflow, architecture, DFD, council design, use case, sequence, DB/ER, REST table, interface)
- **Ch 6 Implementation** (technologies, **14 modules** with formulas and code listings, difficulties & strategies, pseudocode)
- **Ch 7 Testing & Evaluation** (all 31 tests listed, integration, system, UAT)
- **Ch 8 Results** (10 real dashboard screenshots + experiments RQ1–RQ5 + discussion)
- **Ch 9 Conclusion & Future Enhancement**
- **Bibliography** — 80 references, IEEE style, **all authors listed (no "et al.")**, numbered by first citation

How it was made: Python (`python-docx`) generates the file; native equations come from LaTeX → MathML → Word OMML (Office's `MML2OMML.XSL`); Word (COM) is used to render and measure page numbers in a 2-pass build, so the typed TOC/lists have correct page numbers. Diagrams are **drawn programmatically** with matplotlib (PNG, not AI-generated, but **not editable in draw.io/Canva**). Charts use the numbers in `paper_results.json`. Screenshots were captured from the real running app (local Vite server, seeded demo login, 12-resume core suite) with Playwright + Chrome.

---

## 5. Research-paper information (`paper/main.tex`, `paper_results.json`)

**Authors in the manuscript:** Mithila R, Sneha K, Yashaswini R (Dept. of Information Science and Technology, VKIT, Bengaluru).

**Abstract (core claims):** keyword ATS reward vocabulary not evidence; system treats a skill as a claim to be evidenced — 79-skill ontology (353 alias entries), seven-factor hybrid ranker, evidence-weighted coverage, data-layer blind screening, four-agent deterministic council with knock-out gates, GitHub authenticity inspector, retrieval-grounded recruiter copilot, React interface.

**Key numbers (all from `paper_results.json` / the manuscript — synthetic data):**
- 12-resume pilot, job = Machine Learning Engineer, 17 required skills, 2-year minimum.
- Latency per resume: parse 18.01 ms + rank 3.78 ms + council 7.79 ms = **29.58 ms** (~33.8 resumes/s, single thread, TF-IDF mode, Python 3.11.9).
- Kendall τ (keyword baseline vs proposed ranking) = **0.667**.
- TC1 gold standard: baseline 100.0 → proposed **88.1** (rank 1), council 91.4 STRONG_HIRE.
- TC2 buzzword (0.3 yr, 8 skills listed, 1 evidenced): baseline 47.1 (rank 5) → proposed **41.6** (rank 10), council 50.3 REJECT; evidence-weighted coverage 0.27.
- TC3 lateral (Flask for FastAPI): baseline 47.1 → proposed 61.3 (rank 3), LEAN_HIRE (76.0).
- TC4 corrupt format: baseline 0.0 → 34.0, ATS 23, REJECT (human review), confidence 32.8.
- Name-swap test (4 names × 12 resumes × standard/blind = 96 runs): max Δ = **0.0**.
- Weight sensitivity (±20 %, 200 draws): mean τ **0.969**, min 0.879; top-1 and top-3 stable 100 %; council verdicts stable (600 evaluations).
- Ablation (no evidence weighting): TC2 50.3 → 55.2 (REJECT → LEAN_HIRE); Vikram Singh also REJECT → LEAN_HIRE; gates-off changes nothing on this pool.
- Retrieval (8 queries, 12 resumes): P@3 91.7 %, R@3 100 % for BM25, dense (TF-IDF fallback) and hybrid α = 0.55 — saturated, no superiority claim.
- **100-resume benchmark** (20 strong / 45 lean / 35 reject by construction): verdicts 0 STRONG / 79 HIRE-or-LEAN / 21 REJECT; exact agreement **46/100**; strong recall 0/20; reject recall 11/35; mean consensus 71.2 / 60.1 / 62.0; 94/100 carry ≥1 flag (top flags: REQUIRED_SKILLS_MISSING 70, NO_QUANTIFIED_IMPACT 67, EXPERIENCE_DEFICIT 40, LEVEL_MISMATCH 12).
- **Adversarial probes** (before → after the new gates): 019 inverted dates HIRE 72.5 → LEAN_HIRE 73.5; 013 concurrent full-time San Jose/Bengaluru STRONG_HIRE 89.7 → LEAN_HIRE 89.0; C1 HIRE 78.6 → LEAN_HIRE 73.2; C2 no education STRONG_HIRE 92.6 → HIRE 78.6.
- 50-candidate demo pool (screenshot only, not evaluated): top match 93.2 %, avg 56.9 %, 10 Strong / 10 Lean / 30 Reject.

**Method facts (verified in the code this session):**
- Ranker weights: skills .35, semantic .20, experience .15, education .10, projects .10, certifications .05, ATS quality .05. Semantic = MiniLM cosine ×100 (clip) or `min(100, 150·cos_tfidf)`.
- Skill credit: matched 1.0, related 0.5 (**15** related pairs), fuzzy ratio > 0.88; ontology = **79 canonical skills, 353 lookup entries, 8 categories**. (README's "1,500+ skills" is **wrong**.)
- Evidence coverage: `c_ev = (|E| + 0.5(|L|−|E|)) / |R|`.
- Council: consensus `C = 0.35 tech + 0.25 merit + 0.20 culture + 0.20 level`; thresholds 80 / 68 / 55; gates (c_ev < 0.25 → REJECT, < 0.5 → cap LEAN_HIRE; ≥2 high flags → REJECT; 1 high → cap; inverted dates / missing education → cap); 9 red-flag codes; confidence = `100 − 1.2σ − penalties` clamped 20–99; human-review triggers (high bias flag, integrity < 70, confidence < 55, within 2 of a boundary).
- GitHub inspector: `0.55·language + 0.25·activity + 0.20·substance`; forks excluded; "INSUFFICIENT_PUBLIC_DATA" instead of guessing.
- Talent search: `0.55·dense + 0.45·BM25` (k1 = 1.5, b = 0.75); relevance = `(0.40·semantic + 0.60·coverage)·(0.65 + 0.35·exp_fit)`.
- API: FastAPI v4.0.0, prefix `/api/v1`, tables `jobs, resumes (SHA-256 unique), screening_sessions, screening_results, audit_logs`; SQLite locally, PostgreSQL on Render. **The REST API has no automated tests** (only the core, DB module, auth and Streamlit UI do).

**The manuscript's own limitation statements** (kept in the report): all data synthetic and written with knowledge of the rules; the temporal gates were designed after seeing failures; council is conservative at the top and permissive at the bottom; weights/thresholds are expert-chosen; blind screening removes direct identifiers only; no usability study; certifications counted not validated. Its acknowledgement line says AI-assisted tools were used for parts of code generation and drafting.

**Manuscript references** (26 entries) include Dastin 2018, Bertrand & Mullainathan 2004, Wilson & Caliskan 2024, Armstrong 2024, EU AI Act, Qin survey 2023, de Ruijt & Bhulai 2021, Qin 2018, Bhatia 2019, **Deshmukh & Dahake 2025**, SBERT, DPR, BM25, TF-IDF, RAG, Clavié & Soulié 2023, Bogen & Rieke 2018, Raghavan 2020, FA*IR, Du 2024, ChatEval, Zheng 2023 (LLM-as-judge), Hauff & Gousios 2015, scikit-learn, Kendall 1938, RFC 8018 (PBKDF2).

---

## 6. Documents the user sent, and what was done with each

| Document | Used for |
|---|---|
| `FINAL PPT.pptx` (sign-language project deck, 28 slides) | Template/format for the new PPT; slides 1, 2, 28 kept as-is |
| WhatsApp screenshot (guide's 5 rules) | Followed for both deliverables (see §3) |
| `.ogg` ×3 (older voice notes from the guide) | **Not heard** — the user said "just for context"; nothing from them is reflected |
| PPT title-slide image (title + 3 names/USNs) | Names and title on the report cover/certificate/declaration; **not applied to the PPT** (slides 1–2 kept original) |
| `major_project_final_report-2.docx` | Format template only (another team's IDS report); its own text and 25-reference list were **not** reused |

---

## 7. Open items and caveats (carry these into the next session)

1. **Placeholders** in the report: guide, designation, HOD, principal names.
2. **PPT slides 1–2 still show the old project** (by request). If wanted, the title slide needs the new title/names/guide, and the agenda wording "Implementation details of modules" should become "Implementation" to match slide 12.
3. **References:** the report's 80 entries were checked against Crossref/DataCite (75 records). Five were typed by hand and are not DOI-verified (EU AI Act, GDPR, Reuters/Dastin, Levenshtein 1966, Bogen & Rieke). Venue/pages for ~25 conference papers were added from memory — spot-check. **Deshmukh & Dahake (IAES, 2025) appears in the PPT and the manuscript but is *not* in the report's verified bibliography**, and was never database-verified. The "contribution/drawback" lines for each surveyed paper are summaries written here — check against abstracts.
4. **Diagrams are PNGs drawn by code**, not draw.io/Canva files. If the guide insists on editable draw.io/Canva sources, they need redrawing (the Mermaid text in `PPT_CONTENT.md` can be pasted into draw.io for the workflow diagram).
5. The report's **TOC and lists are typed with fixed page numbers**. After any edit, regenerate (`make_report.py`) or fix them by hand.
6. **Report vs PPT numbers must stay consistent.** Source of truth for results: `paper_results.json`; the 100-resume and adversarial tables are transcribed from `paper/main.tex` (not re-run).
7. The **UAT section** states honestly that no formal usability study with external recruiters was done.
8. Unverified: whether the hosted REST API on Render is currently deployed.
9. **Handover plan (not started):** transfer the repo to her GitHub (preferably GitHub's "Transfer ownership"), create her own Google OAuth client (new `VITE_GOOGLE_CLIENT_ID` + origins), re-import into her Vercel (root dir `frontend`), deploy `render.yaml` as a Blueprint with `CORS_ORIGINS` set to her Vercel URL, optional MongoDB Atlas later; remove her items from the user's accounts last, and treat any secret ever in a `.env` as exposed. Waiting on her reply and on her report `.docx`.
10. Deleted/untracked leftovers: `PPT_CONTENT.md` is an untracked file in the repo root; temp renders live in `C:\Users\Arjun\AppData\Local\Temp` (can be ignored).

---

## 8. How to rebuild or change things

**Report**
```
cd report_source
python make_report.py        # needs: python-docx, latex2mathml, pymupdf, matplotlib, pillow, lxml, Microsoft Word installed
```
- `make_report.py` runs a 3-pass build and writes the .docx to Downloads.
- Edit chapter text in `ch1.py … ch9.py`. Markup: `**bold**`, `*italic*`, `` `code` ``, `S~tech~` (subscript), `x^2^` (superscript), `[@bm25,@tfidf]` (citation — numbering is automatic by first citation).
- Equations: `r.eq(r"LaTeX")` then `r.where([("symbol","meaning")])`.
- Figures: `r.fig(path, caption, width_cm)`; tables: `r.table(headers, rows, caption, widths)`.
- References: `refs_db.py` (spec list) + `refs_raw.json` (fetched metadata). Re-fetch with `refs_fetch.py` (uses Crossref + DataCite).
- Diagrams: `diagrams.py`; charts/screenshot prep: `charts.py`.
- **Hard-coded paths** to change on another machine: `OUT_DOCX` in `make_report.py`; `SHOTS_SRC` and `PROJ` in `charts.py`/`ch7.py`/`ch8.py`; the banner is extracted from `Downloads\FINAL PPT.pptx`; `refs_stub.py` expects `refs_db.py` one folder up — in this folder `refs_db.py` sits next to it, so change its `sys.path` line to the current folder.

**PPT** — `ppt_source/build_pptx.py` (python-pptx) edits a copy of `FINAL PPT.pptx`; slides 1, 2, 28 untouched.

---

## 9. Tool notes for the next session
- Browser screenshots for the report used Playwright + installed Chrome at viewport 1120×760, 2× scale, against `http://127.0.0.1:5173` (the demo login is seeded when `VITE_SEED_DEMO_ACCOUNT=on`).
- PowerPoint/Word were driven through COM only for rendering and page measurement.
- This machine's Git Bash `git clone` of the GitHub URL needed credentials; the existing repo has stored credentials for `pull`.

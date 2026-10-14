# What to change in the report, the PPT and the paper

Written 2026-10-14 after the deployment and feature work in the "bring it live" session. It compares the existing documents (the report generator in `docs/report/source/ch1.py … ch9.py`, the deck builder `docs/ppt/build_pptx.py`, the IEEE manuscript `paper/main.tex`) against what the system now does.

## STATUS: applied (updated the same day)

Everything below was applied. Final numbers differ slightly from the plan: **78 automated tests = 49 pytest + 29 JavaScript** (the plan counted only pytest), because the chatbot and interview checks were moved into the repo as real tests (`frontend/tests/`, run with `npm test`). The chatbot's "Export Report (.md)" button now really downloads a Markdown file.

| Item | Result |
|---|---|
| Report (`docs/report/`) | Chapters 1, 4, 5, 6, 7, 8, 9 and the abstract rewritten in `source/ch*.py`; architecture and data-flow figures redrawn (`diagrams.py`); new screenshots (sign-in from the live site, interview kit, two chatbot views); rebuilt through Word: **121 pages (was 110), 80 references all cited**; `.docx` and PDF preview refreshed. Swept for stale statements: none left. |
| Deck (`docs/ppt/`) | Slides 11, 12, 15, 17, 22, 25, 26 updated in `build_pptx.py`, deck rebuilt and every changed slide rendered and checked. Slides 1, 2 and 28 untouched. `PPT_CONTENT.md` regenerated from the real deck (it had described an older version). |
| Paper (`paper/main.tex`) | Five small edits (architecture, workflow/authentication, copilot, limitations, conclusion). **Not compiled** (no TeX on this machine); re-compile in Overleaf. No result changed. |
| Repo docs | `README.md` (79 skills instead of 1,500+, test counts, a live-deployment section), `GUIDEBOOK.md`, `REVIEW_READY_GUIDE.md` (test counts, 79-skill ontology, a live-deployment demo section), `DEPLOY.md`. |

**Still open (needs you):** (1) **slides 1 and 2 still show another team's title, names and guide** and the agenda says "Implementation details of modules"; (2) guide, designation, HOD and principal names are placeholders in the report; (3) the `.docx` has not been opened in Word by a person; check the table of contents and the figure list once; (4) Deshmukh and Dahake (2025) is in the deck and the paper but not in the report's verified bibliography; (5) screenshots of the deployed Interview and Chatbot pages come from the stand-alone build with the demo account (the deployed site needs a sign-in), as the earlier screenshots did.

---

The sections below are the original plan, kept for the record.

---

## 0. What is new since the documents were written

| # | Change | Where it lives |
|---|---|---|
| 1 | **Live, multi-user deployment** on free tiers: React on Vercel, FastAPI on Render, **MongoDB Atlas (M0)** for data. Everything now sits in the second team member's accounts (GitHub `yashsay1808-bot/ai-recruitment-system`, her Vercel, Render, Google Cloud project, Atlas). | `render.yaml`, `DEPLOY.md` |
| 2 | **Server-side accounts and sessions** in MongoDB: sign-up, sign-in, `me`, sign-out. PBKDF2-HMAC-SHA256, 210,000 iterations, per-user salt, constant-time comparison; session tokens are random and only their SHA-256 is stored; sessions expire after 7 days (TTL index); 5 wrong passwords lock the account for 15 minutes; one generic error for "unknown email" and "wrong password". | `api/routers/auth.py`, `api/mongo.py` |
| 3 | **Google sign-in verified on the server** (`POST /auth/google`): checks signature (through Google), audience = our client ID, issuer, expiry, verified e-mail, Gmail only. Google users are stored without a password and are linked to an existing account with the same Gmail. | `api/routers/auth.py` |
| 4 | **Candidate pools served from MongoDB** (`GET /candidates?pool=…`): 12 + 50 + 100 = 162 documents, seeded at first start. | `api/routers/candidates.py`, `api/seed/*.json` |
| 5 | **Sign-in and sign-up hardening in the browser**: copy, cut, paste and drop are blocked on the e-mail and password fields (password-manager autofill and the browser's strong-password suggestion still work); after logout the form is clean (no saved-credential pre-fill, Google auto-select reset). | `frontend/src/components/AuthCard.jsx`, `context/AuthContext.jsx` |
| 6 | **Interview Assistant**: from 1 stored question per candidate to **19–24 tailored questions** (mean 20.7 over the 162 candidates), in 13 categories: resume verification, role-family architecture and system design, hands-on exercise, skill deep-dives (about 35 skills), quality and security, red-flag and GitHub-risk probes, incident forensics, behavioural and leadership (rotating, stable per candidate), motivation and logistics. Category filter chips and "Copy all". | `frontend/src/utils/interviewQuestions.js`, `App.jsx` |
| 7 | **Recruiter chatbot** rebuilt: conversation memory (pronouns, "why?", "tell me more", "the third one"), pagination ("show more"), about 20 intents, filters by verdict / years / skill / flag type / category, rankings and shortlists, three e-mail types (outreach, invitation, decline), duplicate-name disambiguation, varied wording, clickable follow-up suggestions, starter pills built from the loaded pool. | `frontend/src/utils/chatbotEngine.js`, `App.jsx` |
| 8 | **Automated tests: 31 → 49** (pytest). The 18 new ones are in `tests/test_mongo_api.py` (accounts, sessions, lockout, Google token rules, candidate pools, error cases). | `tests/test_mongo_api.py` |
| 9 | Data finding: in the **100-resume pool, 50 names are used twice** (two different people, different roles). The 12 and 50 pools have unique names. | `api/seed/benchmark100.json` |

The ranking engine, the council, the ontology and all evaluation numbers (29.58 ms, τ = 0.667, 88.1, 41.6, name-swap Δ = 0.0, …) did **not** change. Do not touch Chapter 3 or the results tables.

---

## 1. Three accuracy checks before you edit anything

These are places where the documents could say more than the system does. Decide the wording first.

1. **Two implementations of the chatbot and of the interview generator exist.** The report's Module 11 and Module 12 describe the **Python** versions (Streamlit side). The new features above are in the **JavaScript** versions used by the deployed React dashboard. Say which one you describe. Suggested: keep Modules 11 and 12 as the Python design and add a short subsection under Module 14 for the web-dashboard versions.
2. **"The conversation can be exported as a Markdown report"** (Module 12). In the React dashboard the *Export Report (.md)* button currently only shows a confirmation message and does not create a file. Either say the export belongs to the Streamlit app, or let me implement the real export (about 20 lines).
3. **"Run Screening Engine" in the web dashboard for the 12 / 50 / 100 pools** shows staged progress messages, but the scores come from pre-computed pool data (bundled or from MongoDB). The Python pipeline produced them offline. Only uploaded resumes are scored in the browser by the browser-side scorer. Chapter 8 and slide 12 / 17 should not imply that the pool scores are computed live in the browser.
4. **The new chatbot and interview generator were checked with a scripted run (160 conversation checks over all 162 candidates, a 19–24 questions-per-candidate check), but that script is not in the repository.** It sits in a temporary folder. So Chapter 7 can honestly say "checked", not "covered by the automated suite", unless we add it to `tests/` (see §5).

---

## 2. Report (`docs/report/source/chN.py`)

### Front matter and Chapter 1
| File : line | Now says | Change to |
|---|---|---|
| `ch1.py:99` and `ch9.py:8` | "A suite of 31 automated tests … all of which pass." | "49 automated tests … cover … the authentication flow and the MongoDB-backed account and candidate API." (also say the 31 → 49 growth in 7.1 if you like) |
| `ch1.py:95` | "FastAPI service, a SQLAlchemy data model with an Alembic migration, a Streamlit application and a React dashboard." | add "a MongoDB Atlas document store for accounts, sessions and candidate pools". |
| `ch1.py:31` (objective on the interface) | lists chatbot, interview generator, REST API | append: "with server-side authentication and Google sign-in". |
| `ch1.py:53` | "Interfaces and persistence: the React dashboard, Streamlit, FastAPI and the SQLAlchemy data model" | add "a MongoDB document store" and the live deployment. |
| Abstract (page iv) | lists the Python core, FastAPI, Streamlit, React | add one sentence: "The system is deployed as a multi-user web service with server-side authentication (PBKDF2, expiring sessions, Google sign-in) and a managed MongoDB database." |

### Chapter 4: requirements
| File : line | Now says | Change to |
|---|---|---|
| `ch4.py:25` FR15 | "The system shall require sign-in before the workspace is shown." | keep, and add **FR16** "The system shall store accounts and sessions on the server and lock an account after five failed sign-ins", **FR17** "The system shall verify Google sign-in on the server and accept Gmail accounts only", **FR18** "The system shall serve the candidate pools from the database", **FR19** "The interview assistant shall produce a tailored kit of at least 15 questions per candidate", **FR20** "The chatbot shall resolve follow-up questions from the conversation". |
| `ch4.py:82` | "Passwords stored by the stand-alone web interface … PBKDF2 … 200,000 iterations" | "Passwords shall be stored as salted PBKDF2-HMAC-SHA256 digests (210,000 iterations on the server, 200,000 in the stand-alone browser mode); session tokens shall be stored only as SHA-256 hashes and expire after 7 days; repeated failed sign-ins shall lock the account for 15 minutes." |
| `ch4.py:84` | Google restricted to Gmail; client id is the only value in the browser | add "and the Google token shall be verified on the server against the client ID, issuer, expiry and verified-e-mail claim". |
| `ch4.py` (non-functional, security) | no input-handling requirement | add: "Copy, cut and paste shall be blocked on the e-mail and password fields, while password-manager autofill remains possible, and the form shall not be pre-filled after logout." |
| `ch4.py:70` | "either SQLite or PostgreSQL" | "SQLite, PostgreSQL or MongoDB (the deployed configuration uses MongoDB Atlas)". |
| `ch4.py:115` | "Hosting: Vercel, Render for the API **and database**, Streamlit Community Cloud" | "Vercel for the web interface, Render for the API, **MongoDB Atlas (free M0 tier) for the database**, Streamlit Community Cloud …". |
| `ch4.py:122` software table | SQLAlchemy / Alembic / psycopg row | add a row: **PyMongo 4.6+ (`pymongo[srv]`)**, "Accounts, sessions, candidate pools"; add **mongomock** (tests only). |
| `ch4.py:103` | network "only for GitHub, LLM, Google sign-in, deployed site" | add "the MongoDB Atlas cluster". |

### Chapter 5: system design
| Place | Change |
|---|---|
| 5.1.1 architecture text and **Figure 5.1 / 5.4 (architecture, DFD)** | The diagrams are PNGs drawn by `diagrams.py`. Redraw the deployment view: *Browser (React, Vercel) → FastAPI (Render) → MongoDB Atlas*; Google Identity Services → browser → FastAPI (token verification). Show that pool scores are pre-computed and stored. |
| `ch5.py:22` paragraph on the stand-alone mode | Keep, and add: "In the deployed configuration the web interface is connected to the API through `VITE_API_BASE_URL`, `VITE_AUTH_PROVIDER` and `VITE_CANDIDATES_PROVIDER`, and accounts, sessions and the candidate pools are served by the API." |
| **5.4 Database Design** (`ch5.py:43-45`) | Currently describes only the five relational tables. Add **5.4.2 "Document Store (MongoDB)"**: collections `users` (unique `email`; fields name, company, role, salt, hash, iterations, failedLogins, lockedUntil, googleId, picture, createdAt), `sessions` (unique `tokenHash`, TTL index on `expiresAt`, `userId`), `candidates` (unique `(pool, id)`, `_order`). Add a small table of collections, keys and indexes. Add one sentence: the legacy relational routes use an ephemeral SQLite file on Render, because the free PostgreSQL instance was removed. |
| **5.4.1 REST table** (`ch5.py:48-59`, 10 rows) | Add rows (no `/api/v1` prefix): `POST /auth/signup` (create an account), `POST /auth/signin` (verify the password, return a session token), `POST /auth/google` (verify a Google ID token, return a session token), `GET /auth/me` (current user), `POST /auth/signout` (end the session), `GET /candidates?pool=` (candidate pool: core12, benchmark50 or benchmark100). The table grows from 10 rows to 16 rows; do not quote a total endpoint count, because several existing rows group more than one endpoint. |
| **5.5 Interface Design** (`ch5.py:62-63`) | One sentence on the sign-in card: paste/copy blocked on credential fields, autofill allowed, clean after logout. Figure 5.8 (`signin_crop.jpg`) can stay, but retake it from the deployed site (it now shows the Google button). |
| Sequence diagram 5.3 | Optional: add a short authentication sequence (sign-in → hash check → session token → `me`). |

### Chapter 6: implementation
| Place | Change |
|---|---|
| `ch6.py:21` technologies | "SQLAlchemy, Alembic, SQLite and PostgreSQL: … production database" → "… SQLite for local use; **MongoDB Atlas with PyMongo** for accounts, sessions and candidate pools in the deployed system". |
| `ch6.py:24` | "Google Identity Services: optional sign-in with Google, restricted to Gmail accounts." → add "the ID token is verified on the server". |
| `ch6.py:26` | "Vercel and Render: hosting of the web interface and of the API with its database" → "Vercel (web interface), Render (API) and MongoDB Atlas (database)". |
| `ch6.py:28` | "stored through SQLAlchemy and presented through React or Streamlit" → add "or MongoDB". |
| **Module 11** (`ch6.py:223`) | Keep the Python description. Add a paragraph on the web-dashboard version: role-family banks (ML, DevOps, data, backend, full-stack, BI, AI safety and a general fallback), about 35 skill deep-dives, probes generated from the candidate's red-flag codes, GitHub risk and ATS score, rotating behavioural questions chosen by a hash of the candidate ID so the kit is stable, 19–24 questions per candidate, filter chips and copy-all. |
| **Module 12** (`ch6.py:227`) | Keep the Python description. Add the web-dashboard engine: word-boundary intent detection, conversation memory (context stored on each answer and replayed as history), pronoun and ordinal resolution, pagination, duplicate-name clarification, 3 e-mail types, deterministic wording variation, follow-up suggestions; answers use only the loaded pool, so nothing is invented. Remove or correct "exported as a Markdown report" (see §1.2). |
| **Module 13** (`ch6.py:231`) | Keep the relational part. Add the **account service**: PBKDF2 (210,000 iterations, 16-byte salt), generic credential error and dummy hash work for unknown e-mails, lockout, session tokens (random, SHA-256 stored, 7-day TTL), Google verification steps, idempotent seeding of the three candidate pools. Replace "PostgreSQL in deployment". |
| **Module 14** (`ch6.py:235`) | "stored in the stand-alone configuration as … 200,000 iterations" → add "in the connected configuration the accounts are created on the server"; "the application … ships a browser-side scorer … so that it runs fully offline; with environment variables it can instead call the API" → "…the deployed site calls the API". Add the sign-in hardening sentence. "The dashboard is deployed on Vercel, and the API and its database on Render." → "…the API on Render and the data in MongoDB Atlas". |
| **6.3 Deployment constraints** (`ch6.py:257-259`) | Now false: "a free PostgreSQL instance is time-limited". Replace with: the free API sleeps after about 15 minutes (the first request takes up to about 50 s); Atlas M0 offers 512 MB and requires network access from `0.0.0.0/0` because the host has no fixed address; the legacy relational routes use an ephemeral SQLite file; secrets live in environment variables. Add two new difficulties: **(a) account security** (credential enumeration, brute force → generic error, dummy hash, lockout) and **(b) duplicate candidate names** (50 names occur twice in the 100-pool → the chatbot asks which person is meant and accepts a rank number). |

### Chapter 7: testing
| Place | Change |
|---|---|
| `ch7.py:14` | list of tested areas | add "the MongoDB-backed account service, Google token verification and candidate-pool API". |
| Unit-test table (rows 1–31, `ch7.py:18-41`) | Add rows 32 onward for `tests/test_mongo_api.py` (18 tests): sign-up → sign-in → `me` → sign-out lifecycle; sign-up rules (non-Gmail 422, short password 422, bad role 422, duplicate e-mail 409, e-mail case-insensitive); generic 401 for unknown e-mail and wrong password; lockout after five failures even with the right password; `me` requires a valid token; candidate pools return 12 / 50 / 100 documents and an unknown pool returns 400; seeding is idempotent (162 documents); 503 when the database is not configured; Google: creates a user and session, links to an existing password account, Google-only accounts cannot sign in with a password; token verification rejects wrong audience, issuer, expiry, unverified e-mail (401) and non-Gmail (403); bad token → 401, Google outage → 502; Google not configured → 503. |
| per-file table (`ch7.py:57-59`) | add `test_mongo_api.py … 18 … Passed`; total 31 → **49**. |
| 7.2 Integration, 7.3 System, 7.4 UAT | Add: **system tests of the live deployment** (sign-up and sign-in on the deployed site, candidates load from the database, CORS works from the Vercel origin, health endpoint) and **front-end behaviour checks** (paste/copy/cut blocked on credential fields; programmatic autofill accepted; form clean after logout; interview kit shows 19–24 questions; chatbot follow-ups). Label the last group "scripted checks" unless you add them to `tests/` (§5). UAT statement stays: no formal usability study. |

### Chapter 8: results
| Place | Change |
|---|---|
| Interview Assistant figure (`interview.jpg`) | **Retake**: the page now shows the question count, filter chips, coloured category badges and 20 questions. Update the caption and one paragraph: 19–24 questions per candidate, mean 20.7 (162 candidates). |
| Chatbot figures (`chat_flags.jpg`, `chat_compare.jpg`, `ch8.py:63-64`) | **Retake** with a conversation that shows follow-up chips and a "why?" follow-up. Add a short worked example: *Tell me about X → why? → should I hire her? → interview questions for her*. |
| Sign-in figure | Retake from the deployed site. |
| New short result (optional): "Deployment verification" | health endpoint 200, candidate pools of 12 / 50 / 100 served, CORS allowed only for the web origin, unknown login → 401. No performance numbers have been measured for the live service. |
| Do **not** change | latency, τ, name-swap, ablation, retrieval, 100-resume and adversarial tables. |

### Chapter 9
- `ch9.py:8` conclusion: update the system description ("…a React web interface that **has been deployed on a managed cloud stack with server-side accounts**") and the test count (49).
- `ch9.py:21` future enhancement "API tests and a managed database…MongoDB Atlas": **partly done.** Rewrite: "Automated tests for the legacy REST endpoints, persistence of screening runs and recruiter decisions per account in the managed database (accounts, sessions and candidate pools are already stored in MongoDB Atlas), and delivery of interview invitations by e-mail."
- `ch9.py:22` "deployment as a multi-user cloud platform": now partly done. Keep the remaining parts: role-based access, candidate notice and consent, data-retention limits, fairness audits, a usability study.
- Add one limitation sentence: the deployed free tiers sleep when idle and are not designed for production load.

### Bibliography
- Keep the 80 references. Optional additions for the new material, **each to be verified before use** (the guide wants real, checkable sources): RFC 8018 (PBKDF2, already in the manuscript), the OWASP Password Storage Cheat Sheet, Google's documentation on verifying ID tokens, the MongoDB documentation on TTL indexes. Do not add anything you have not opened.
- Still open from the handoff: Deshmukh & Dahake (2025) is in the PPT and the manuscript but not in the report's verified list.

### Other documents in the repo
`README.md`, `GUIDEBOOK.md` and `REVIEW_READY_GUIDE.md` have not been read for this task. They very likely repeat the old deployment (Render Postgres), the 31-test count and "1,500+ skills" (the ontology has 79 skills). `DEPLOY.md` was already updated.

---

## 3. PPT (`docs/ppt/build_pptx.py`, deck `FINAL PPT - Recruitment.pptx`)

Slides 1, 2 and 28 stay as they are, as agreed. Slides 3–10 and the literature survey are unchanged.

| Slide | Now | Change |
|---|---|---|
| **11 Architecture** (`build_pptx.py:378-386`) | Presentation: React (Vercel), Streamlit, dashboard. Service: FastAPI (Render), **Sign-in: "Email and password, Google (Gmail only)"**. Data: **"SQLite history"**, resume pools, job roles. | Service → add "Server-verified sign-in (PBKDF2, 7-day sessions, Google token check)". Data → **"MongoDB Atlas: accounts, sessions, candidate pools"** and keep "SQLite history" only if the legacy screening history is still mentioned (say "legacy"). Intelligence → "Interview questions: 20+ tailored per candidate". |
| **12 Implementation** (single diagram, `:419`, `:435`) | "Verdict + Dashboard … interview questions, **SQLite history**" | Change the last box to "Dashboard, interview kit, chatbot" and the storage mention to MongoDB. Redraw the one full-system diagram to include Browser → FastAPI → MongoDB. Keep it **one** diagram (guide's rule). |
| **13–14** ranking / council | no change | – |
| **15 Data-flow diagram** (`:528`, `:534`) | "Results are saved to the SQLite history … Dashboard + SQLite history" | "Accounts, sessions and candidate pools are stored in MongoDB Atlas" and keep the saved-history wording only for what is really saved. |
| **16 Council DFD** | no change | – |
| **17 Interface design** (screenshots, `:582`) | `fig_login_home.png` from the old site | Replace with fresh screenshots from the deployed site. **The live address changed**: it is now `https://ai-recruitment-system-lemon.vercel.app` (the deck notes still mention `…-rho.vercel.app`). Add the new Interview Assistant (filter chips) screenshot. |
| **18–19 Test cases** | four test resumes | no change; if a test-count line exists, 31 → 49. |
| **20–24 Results** | latency, τ, charts; slide 22 is the copilot (`:701`) | Retake the copilot screenshot (`fig_copilot_audit.png`) showing a follow-up. Add a small stat card **"49 automated tests"** if the deck lists counts. Do not change numbers from `paper_results.json`. |
| **25 Conclusion** (sentences) | ends with "…the project proves that explainable AI can make hiring more transparent and trustworthy." | Insert one sentence: "The system is also deployed as a multi-user web service with server-side authentication and a managed database." |
| **26 Future scope** (2–3 sentences) | "…deployed as a full multi-user cloud platform with ATS and email integrations." | Replace: "The deployed system can be extended with role-based access, candidate consent and retention controls, stored screening history per account, and e-mail and ATS integrations. Live GitHub and LinkedIn checks, multilingual resumes and validation on real hiring data remain open." |
| **27 References** | 10 papers | no change. |

Guide's rules still hold: no generated images (use real screenshots), draw.io/Canva for diagrams, methodology as a flow, conclusion and future scope in sentences.

---

## 4. IEEE manuscript (`paper/main.tex`)

The scientific content and every result table stay. Small, safe edits:
1. **§System Architecture → Modular architecture**: one sentence on the deployment layer (React on Vercel, FastAPI on Render, MongoDB Atlas) and server-side authentication.
2. **§Progressive-disclosure recruiter workflow**: the interview kit now has 19–24 questions per candidate, generated from the red flags, the GitHub risk and the missing skills of that candidate.
3. **§Retrieval-grounded recruiter copilot**: conversation memory and pagination; answers still come only from retrieved candidate evidence.
4. **§Limitations**: add "the deployment uses free-tier services and was not load-tested; the 100-resume benchmark reuses 50 candidate names for different profiles".
5. **§Future work**: "managed database" is partly delivered.
6. Keep the acknowledgement line about AI-assisted tools, and mention the new work falls under it.

---

## 5. Things I can do next (pick any)

1. **Apply the report edits** in `ch1.py … ch9.py` (text and tables only). Rebuilding the `.docx` needs `make_report.py`, Microsoft Word and Python libraries (`python-docx`, `latex2mathml`, `pymupdf`, `matplotlib`, `pillow`, `lxml`), and the hard-coded Downloads paths in the scripts must be repointed to this folder first (see `HANDOFF_CONTEXT.md` §8).
2. **Apply the deck edits** in `build_pptx.py`; it needs `python-pptx` and the original `FINAL PPT.pptx` in Downloads.
3. **Retake the screenshots** (sign-in, interview, chatbot, deployment) from the deployed site with Playwright.
4. **Put the chatbot and interview checks into the repo** as `tests/` (Node's built-in test runner, no new dependency) so Chapter 7 can claim them as automated.
5. **Make "Export Report (.md)" real** in the chatbot page.
6. **Update `README.md`, `GUIDEBOOK.md`, `REVIEW_READY_GUIDE.md`** to match.

Hard-coded numbers to keep consistent everywhere: tests **49**; REST table rows **16** (was 10); interview kit **19–24 per candidate (mean 20.7)**; pools **12 / 50 / 100 = 162**; ontology **79 skills** (not 1,500+); live address `https://ai-recruitment-system-lemon.vercel.app`; API `https://ai-recruitment-api-7blc.onrender.com`.

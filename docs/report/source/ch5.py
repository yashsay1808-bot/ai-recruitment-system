"""Chapter 5: System Design"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "fig")
SHOT = os.path.join(HERE, "shots")


def build(r):
    r.chapter("System Design")
    r.p("System design defines the architecture, the components, the interfaces and the data of the system, and the way in which they interact to satisfy the specified requirements. It gives a structured representation of the proposed system and explains how its modules work together. This chapter presents the high-level design (workflow, architecture and data flow), the design of the four-agent council, the use-case diagram, the sequence diagram, the database design and the interface design of the AI-Powered Intelligent Recruitment System.")

    r.h1("5.1", "High-Level Design")
    r.p("The high-level design describes the overall workflow of the system, from the choice of a role by the recruiter to the decision on a candidate. The recruiter selects one of the pre-configured roles or pastes a job description, which the job-description parser converts into required skills, preferred skills, a minimum number of years of experience and preferred degrees. The recruiter then uploads resumes or loads a ready-made pool. Each resume is parsed into structured fields; scanned pages are sent to OCR.")
    r.p("If blind screening is enabled, the parsed profile is anonymised: the name is replaced by a neutral identifier such as *Candidate #001*, contact details, location and profile links are masked, and gendered words are neutralised. Only this anonymised copy is passed on. The skill ontology then normalises the skills and classifies each required skill as matched, partially matched or missing. The hybrid ranker computes seven scores and their weighted sum, and the four-agent council reviews every candidate, applies the knock-out gates and issues a verdict with red flags, a confidence value and, where needed, a request for human review. The explanations, the skill-gap analysis, the interview questions and the leaderboard are generated from these results and the screening history is saved. The recruiter reviews the shortlist and records a decision. The complete flow is shown in Figure 5.1.")
    r.fig(os.path.join(FIG, "fig_5_1_workflow.png"), "System workflow diagram of the AI-Powered Intelligent Recruitment System.", 7.6)
    r.p("Figure 5.1 shows the sequence of stages from the selection of a role to the recorded decision, and the optional anonymisation branch.")

    r.h2("5.1.1", "System Architecture")
    r.p("The system follows a layered architecture. The presentation layer consists of the React web application (Nexus ATS) and the Streamlit workspace. The service layer is a FastAPI REST service that exposes jobs, resumes, screenings and audit logs, and that orchestrates the parsing, ranking, explanation and anonymisation components through service classes. The intelligence engine is a framework-free Python library in which every scoring algorithm is implemented: the resume parser, the skill ontology, the hybrid ranker, the council, the talent search, the GitHub inspector and the interview generator. The data layer comprises a relational database (SQLite for local use) for jobs, resumes, screening sessions and the audit log, a MongoDB Atlas document store for the user accounts, the sessions and the candidate pools of the deployed system, and the role definitions. The layers are shown in Figure 5.2.", keep=True)
    r.fig(os.path.join(FIG, "fig_5_2_architecture.png"), "System architecture of the AI-Powered Intelligent Recruitment System.", 14.0)
    r.p("The React application can run in a stand-alone mode with bundled sample candidates, so that the system can be demonstrated without any server, or it can be connected to the API through environment variables. Its data layer is organised as replaceable service modules for authentication, candidates, GitHub and e-mail, which are selected by configuration, so that a persistent store or an external service can be attached without changing the components. In the deployed configuration the application is connected to the API through three configuration values (the API address, the authentication provider and the candidate provider): accounts and sessions are then created and checked by the API, and the candidate pools are read from the database.")

    r.h2("5.1.2", "Data Flow Diagram")
    r.p("The data flow of the system is shown in Figure 5.3 as a level-1 diagram. The recruiter supplies a job description and resumes to the parsing process (1.0), which reads the job roles from the data store D1 and the resumes from D2. The parsed profiles pass to the optional anonymisation process (2.0), whose output, the blind profiles, enters the skill-matching and ranking process (3.0). The ranked scores go to the council review process (4.0), which writes the screening history to D3 and returns the verdict, red flags and explanations to the recruiter. Before any of these processes can be used, the recruiter signs in, and the accounts and sessions are read from and written to the data store D4. In the deployed system D2 and D4 are collections of the MongoDB database.", keep=True)
    r.fig(os.path.join(FIG, "fig_5_7_dfd.png"), "Level-1 data flow diagram of the system.", 13.5)

    r.h2("5.1.3", "Design of the Four-Agent Council")
    r.p("The council evaluates a candidate in rounds. In the first round the Tech Lead, the Culture and Retention agent and the Seniority and Compensation agent score the candidate independently from a common set of features. An optional enrichment step may let a language model improve the text of these scorecards, but it can move a score by at most 10 points. In the second round the Fair-Hiring Auditor reviews everything that has been written so far, including any model-written text, scans it for biased language, and computes a merit-only score. In the third round the agents cross-examine each other in a deterministic, data-driven transcript. Finally an executive consensus is synthesised: a weighted score, a verdict, red flags, confidence and review triggers. The sequence is shown in Figure 5.4, and the formulas are given in Chapter 6.", keep=True)
    r.fig(os.path.join(FIG, "fig_5_6_council.png"), "Orchestration of the four-agent council.", 13.5)

    r.h1("5.2", "Use-Case Diagram")
    r.p("A use-case diagram represents the interaction between the actors of a system and the functions that the system provides. The primary actor of the system is the recruiter, who signs up, signs in with a password or a Google account, selects or creates a role, loads resumes, runs the screening engine and reviews the results. The review includes the leaderboard, the candidate dossier with the council debate, the side-by-side comparison, the interview questions, the analytics page and the chatbot. The recruiter can also turn blind screening on and off and can record a shortlist or reject decision. The GitHub service and the language-model provider are optional external actors that support the inspection of a dossier and the answers of the copilot. The use cases are shown in Figure 5.5.", keep=True)
    r.fig(os.path.join(FIG, "fig_5_3_usecase.png"), "Use-case diagram of the system.", 13.0)
    r.p("Figure 5.5 shows that every function is initiated by the recruiter; the external actors are optional and the system remains usable without them.")

    r.h1("5.3", "Sequence Diagram")
    r.p("A sequence diagram shows the order in which the components interact to complete an operation. In the screening sequence the recruiter chooses a role and uploads resumes through the web interface. The interface asks the resume parser to parse every file and receives structured profiles. It then asks the ranker, which uses the ontology, to score and rank the profiles, and receives the ranked list with the score breakdown. For each candidate that the recruiter opens, the interface asks the council to evaluate the candidate, and receives the verdict, the flags and the confidence. The session and the results are saved in the database. The recruiter reviews the leaderboard and the dossier and records a decision, which is stored together with an audit-log entry. The sequence is shown in Figure 5.6.", keep=True)
    r.fig(os.path.join(FIG, "fig_5_4_sequence.png"), "Sequence diagram of a screening session.", 13.5)
    r.p("The diagram is a conceptual representation. Actual function calls and communication paths may differ between the Streamlit application, the React interface and the API, but the order of the stages is the same.")

    r.h1("5.4", "Database Design")
    r.p("The system uses two stores. The screening data of the REST service is stored in a relational schema that is defined with SQLAlchemy and created by an Alembic migration, and the user accounts, the sessions and the candidate pools of the deployed system are stored in a MongoDB document store (Section 5.4.2). Five tables are used. The *jobs* table stores the role definition: title, department, minimum experience, the required and preferred skills and the preferred degrees as JSON lists, and the description text. The *resumes* table stores the file name, the SHA-256 hash of the file, which is unique and is used to reject duplicates, the raw text, the parsed data as JSON and the main contact fields. The *screening_sessions* table represents one batch run of a job and stores the recruiter, the weights that were used and a time stamp. The *screening_results* table stores, for each candidate of a session, the overall score, the rank, the score breakdown, the skill-gap result and the candidate data as JSON, and the decision (shortlist or reject) with its time stamp. The *audit_logs* table is an append-only record of actions with the actor and a JSON description of the details. Figure 5.7 shows the entities and their relationships.", keep=True)
    r.fig(os.path.join(FIG, "fig_5_5_er.png"), "Entity-relationship diagram of the database.", 12.5)
    r.p("A job has many screening sessions, a session contains many results, and a resume can be scored in many results, which allows the same candidate to be screened for several jobs. Deleting a job deletes its sessions and results through cascading rules, while deleting a resume leaves the results in place with the resume reference set to null.")
    r.h2("5.4.1", "REST Interface")
    r.p(f"The service is versioned with the prefix /api/v1 and is documented automatically at /docs; the account endpoints (/auth) and the candidate endpoint (/candidates) are mounted without the version prefix, because the web interface calls them directly. {r.ref_next_tab()} lists the endpoints.", keep=True)
    r.table(["Method", "Endpoint", "Purpose"], [
        ["POST", "/api/v1/jobs", "Create a job with required and preferred skills"],
        ["GET", "/api/v1/jobs, /api/v1/jobs/{job_id}", "List jobs or read one job"],
        ["PATCH, DELETE", "/api/v1/jobs/{job_id}", "Update or delete a job"],
        ["POST", "/api/v1/resumes/upload", "Upload a resume, parse it and reject duplicates by SHA-256"],
        ["GET", "/api/v1/resumes, /api/v1/resumes/{resume_id}", "List resumes or read one resume"],
        ["POST", "/api/v1/screenings/run", "Run a screening of selected resumes against a job, optionally in blind mode"],
        ["GET", "/api/v1/screenings, /api/v1/screenings/{session_id}", "List sessions or read a session with its ranked results"],
        ["PATCH", "/api/v1/screenings/results/{result_id}/decision", "Record a shortlist or reject decision"],
        ["GET, POST", "/api/v1/audits", "Read or write the audit log"],
        ["POST", "/auth/signup", "Create an account (Gmail address, name, company, role and password)"],
        ["POST", "/auth/signin", "Check the password and return a session token"],
        ["POST", "/auth/google", "Verify a Google ID token on the server and return a session token"],
        ["GET", "/auth/me", "Return the signed-in user"],
        ["POST", "/auth/signout", "End the session"],
        ["GET", "/candidates?pool=", "Return the candidate pool core12, benchmark50 or benchmark100"],
        ["GET", "/health, /", "Health check and service information"],
    ], "REST Endpoints of the Service", [1.0, 3.0, 3.0], size=10, align=["center", "left", "left"])

    r.h2("5.4.2", "Document Store (MongoDB)")
    r.p(f"The accounts, the sessions and the candidate pools of the deployed system are stored in a MongoDB Atlas database, which was chosen because these records are independent documents with a flexible structure and because the free tier is persistent. The database holds three collections, which are created together with their indexes when the API starts. {r.ref_next_tab()} lists them.", keep=True)
    r.table(["Collection", "Content", "Keys and indexes"], [
        ["users", "name, e-mail (lower case), company, role, password salt, hash and iteration count, failed-sign-in counter, lock-until time, Google identifier and picture, creation time", "e-mail is unique; an account created with Google has no password hash"],
        ["sessions", "SHA-256 digest of the session token, user reference, creation time and expiry time", "token digest is unique; a time-to-live index removes a session when it expires (seven days)"],
        ["candidates", "one document per candidate with scores, verdict, skills, red flags, GitHub summary and council scorecards, the pool name and its order", "the pair (pool, candidate id) is unique; pools are core12 (12), benchmark50 (50) and benchmark100 (100)"],
    ], "Collections of the MongoDB Document Store", [1.4, 3.4, 2.4], size=10, align=["left", "left", "left"])
    r.p("When the API starts it creates the indexes and fills any candidate pool that is still empty from the bundled seed files, so that a restart never duplicates data. If the database address is not configured, the account and candidate endpoints answer with a service-unavailable error and the rest of the API keeps working.")

    r.h2("5.4.3", "Authentication and Sessions")
    r.p("The authentication design protects the accounts against the usual attacks on a sign-in form. It is implemented by the account endpoints of the API and is summarised below.", keep=True)
    r.bullets([
        "**Sign-up:** the API checks the name, the e-mail address (Gmail only), the company, the role and the password length (at least eight characters), stores the e-mail in lower case, and rejects a second account with the same address.",
        "**Password storage:** the password is hashed with PBKDF2-HMAC-SHA256 using 210,000 iterations and a random 16-byte salt, and is compared in constant time.",
        "**Sign-in:** an unknown e-mail address and a wrong password produce the same message, and a hash is computed in both cases so that the response time does not reveal which addresses exist. After five wrong passwords the account is locked for 15 minutes.",
        "**Sessions:** a successful sign-in returns a random token. Only its SHA-256 digest is stored, so a copy of the database cannot be used to sign in, and the session expires after seven days or at sign-out.",
        "**Google sign-in:** the browser obtains a Google ID token and the API verifies it with Google: the audience must be the client identifier of the project, the issuer must be Google, the token must not have expired, and the e-mail must be verified and must end with gmail.com. A new user is stored without a password; if the same address already has a password account, the Google identity is linked to it.",
        "**Interface protection:** the credential fields of the forms block copy, cut, paste and drop but accept the autofill and the strong-password suggestion of a password manager, and the sign-in form starts empty after a logout.",
    ])

    r.h1("5.5", "Interface Design")
    r.p("The interface design describes how the recruiter interacts with the system. The web interface is organised as a left navigation with seven pages (Job Management, Screening Leaderboard, Candidate DeepDive, Candidate Comparison, Interview Assistant, Recruiter Analytics and Recruiter Chatbot), a top bar with a search field, the blind-screening switch and the signed-in user, and a content area. Access is controlled by a single sign-in and sign-up card, shown in Figure 5.8. The card accepts a Gmail address and a password or a Google account; its credential fields block copy and paste but accept the autofill of a password manager, and it is empty again after a logout.")
    r.fig(os.path.join(SHOT, "signin_crop.jpg"), "Sign-in card of the web interface.", 6.5, frame=True)
    r.p("The home page follows the principle of progressive disclosure: it is organised as three guided steps, an active-role summary with the full competency editor behind a disclosure control, candidate intake by upload or by one-click benchmark pools, and a launchpad for the next actions. All controls of a flat layout remain available, but their visibility is staged so that a new user is not overwhelmed. Figure 5.9 shows the workspace.")
    r.fig(os.path.join(SHOT, "jobs_top.jpg"), "Workspace of the web interface: active role and candidate intake.", 14.0, frame=True)
    r.p("The leaderboard presents the telemetry of the run (candidates screened, top match, model backend and active role), a search bar for natural-language questions with prompt shortcuts, and ranked candidate cards with a score bar, an evidence excerpt, matched and missing skills, the number of red flags and the verdict. Cards can be switched to a compact table. The dossier of a candidate shows the four council scorecards, the estimated level and the compensation band, and a replayable debate; it is shown in Chapter 8.")
    r.p("The interview assistant shows a kit of about twenty questions for the selected candidate, each with a category badge and a note on what the interviewer should look for. The kit can be filtered by category and copied as text. The recruiter chatbot keeps the context of the conversation, so that a question such as *why?* or *should I hire her?* refers to the candidate that was discussed last, shows long lists five at a time, and offers clickable follow-up questions below each answer. The whole conversation can be exported as a Markdown file.")
    r.p("The interface distinguishes between a detected inconsistency, a red flag and a verdict, and displays each of them separately, so that a recruiter can see which fact led to which decision.")

    r.h3("Summary")
    r.p("This chapter presented the design of the system. The workflow described the processing of a screening from the choice of a role to the decision. The architecture identified the presentation, service, intelligence and data layers. The data flow, the council orchestration, the use-case diagram and the sequence diagram described the behaviour of the system, and the database design, the document store, the authentication design and the REST interface described its persistent data, its accounts and its programmatic access. The interface design described the user experience. Together, these designs form the structural basis for the implementation presented in the next chapter.", indent=False)

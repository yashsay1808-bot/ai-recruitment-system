"""Chapter 4: Requirement Specifications"""


def build(r):
    r.chapter("Requirement Specifications")
    r.p("This chapter describes the functional and non-functional requirements of the AI-Powered Intelligent Recruitment System. It also specifies the hardware, software and user requirements that are necessary for the development and operation of the system. The requirements were derived from the weaknesses of the Phase 1 keyword ATS, from the gaps identified in the literature survey, and from the needs of a recruiter who must be able to explain every decision.")

    r.h1("4.1", "Functional Requirements")
    r.p("The functional requirements of the proposed system are summarised in the following table and described below.", keep=True)
    r.table(["ID", "Functional requirement"], [
        ["FR1", "The system shall accept resumes in PDF, DOCX and plain-text formats, and shall use OCR for scanned PDF pages."],
        ["FR2", "The system shall extract name, e-mail, phone, location, profile links, skills, education, experience, projects and certifications from a resume."],
        ["FR3", "The system shall parse a job description into required skills, preferred skills, minimum experience and preferred degrees, and shall allow a recruiter to select a pre-configured role or create a custom role."],
        ["FR4", "The system shall normalise skills through an ontology of canonical skills and aliases, and shall report matched, partially matched and missing skills for every candidate."],
        ["FR5", "The system shall compute a seven-factor hybrid score and shall rank all candidates of a pool in descending order of score."],
        ["FR6", "The system shall discount skills that are listed but not evidenced in experience or projects, and shall report the unevidenced-skill ratio."],
        ["FR7", "The system shall provide a blind-screening mode that removes names, contact details, locations, profile links and gendered words before any agent evaluates a resume."],
        ["FR8", "The system shall evaluate every candidate with four agents (Tech Lead, Culture and Retention, Fair-Hiring Auditor, Seniority and Compensation) and shall return a verdict, a confidence value, red flags, dissent and human-review triggers."],
        ["FR9", "The system shall record the cross-examination between the agents and allow it to be replayed."],
        ["FR10", "The system shall verify programming languages claimed on a resume against public GitHub repositories when a profile is available, and shall report insufficient data instead of guessing."],
        ["FR11", "The system shall answer natural-language questions about the candidate pool with evidence snippets, and shall generate outreach drafts and comparisons."],
        ["FR12", "The system shall generate technical, project-specific, gap-probing and behavioural interview questions with evaluation criteria."],
        ["FR13", "The system shall provide a leaderboard, candidate dossier, side-by-side comparison, analytics page and report export."],
        ["FR14", "The system shall expose jobs, resumes, screenings and audit logs through a REST API and shall persist screening sessions with a recruiter decision."],
        ["FR15", "The system shall require sign-in before the workspace is shown."],
        ["FR16", "The system shall store user accounts and sessions on the server, shall lock an account for 15 minutes after five failed sign-ins, and shall not reveal whether an e-mail address is registered."],
        ["FR17", "The system shall verify a Google sign-in token on the server (audience, issuer, expiry and verified e-mail) and shall accept Gmail accounts only."],
        ["FR18", "The system shall serve the candidate pools of 12, 50 and 100 resumes from a database."],
        ["FR19", "The interview assistant shall prepare a tailored kit of at least 15 questions for every candidate, drawn from the role family, the matched skills, the red flags and the GitHub risk of the candidate."],
        ["FR20", "The chatbot shall resolve follow-up questions from the conversation, shall page long lists, and shall ask which candidate is meant when a name is ambiguous."],
    ], "Functional Requirements", [0.6, 5.6], size=10.5, align=["center", "left"])
    r.p("In addition to the requirements listed in the table, the following behaviours are required:", keep=True)
    r.bullets([
        "A skill that is only present in the skills list of a resume must receive half credit in the evidence-weighted coverage.",
        "A related skill (for example Flask for FastAPI) must receive half credit and must be reported as a partial match with the reason.",
        "An inverted or future date range must be excluded from the experience total and reported as an inconsistency.",
        "Two full-time on-site roles that overlap by six months or more in different countries must raise a high-severity red flag.",
        "A verdict must be capped or changed by the knock-out gates when the evidence-weighted coverage is low, when high-severity red flags are present or when education is missing.",
        "The system must distinguish between a detected inconsistency, a red flag and a verdict, and show each separately.",
        "The system must handle the failure of an optional component (embedding model, language model, network) without terminating the screening.",
    ])

    r.h1("4.2", "Non-Functional Requirements")
    r.p("The non-functional requirements describe the quality attributes and operational characteristics expected from the system.")
    r.h2("4.2.1", "Usability")
    r.bullets([
        "The recruiter workflow shall be organised as three guided steps (choose a role, load candidates, review results), with advanced controls hidden until requested.",
        "Every score shall be accompanied by a breakdown, and every verdict by its reasons.",
        "Matched, partial and missing skills shall be visually distinguished.",
        "The interface shall remain usable on laptop screens and shall provide understandable messages when an operation fails.",
    ])
    r.h2("4.2.2", "Reliability")
    r.bullets([
        "The system shall continue to screen the remaining resumes when one resume cannot be parsed.",
        "Failure of the dense embedding model shall fall back to TF-IDF, failure of the language-model service shall fall back to rule-based text, and failure of the GitHub service shall produce a structured report without raising an error.",
        "A duplicate resume shall be detected through its SHA-256 hash and shall not be stored twice.",
        "The decision logic shall be deterministic, so that the same inputs always produce the same outputs.",
    ])
    r.h2("4.2.3", "Performance")
    r.bullets([
        "A complete screening (parsing, ranking and council review) should take less than 100 milliseconds per resume on a laptop CPU in the offline configuration. The measured value is about 30 milliseconds.",
        "The leaderboard and the dossier shall be shown without noticeable delay after the screening has finished.",
        "The search index shall be built once per resume pool and cached by a content fingerprint, so that repeated queries are fast.",
    ])
    r.h2("4.2.4", "Design Constraints")
    r.bullets([
        "The scoring core shall be written in Python and shall be independent of any user interface.",
        "Weights, thresholds and gates shall be configurable and shall not be learned from data in the current version.",
        "The system shall run without network access; online services are optional.",
        "The free-tier hosting limits (for example 512 MB of memory for the API service) shall be respected by providing a lean dependency set in which the dense model is optional.",
    ])
    r.h2("4.2.5", "Portability")
    r.bullets([
        "The Python core shall run on Windows and Linux with Python 3.11.",
        "The web interface shall run in a modern browser; the API shall run on any host that supports Python and either SQLite or PostgreSQL, and, for accounts and candidate pools, MongoDB.",
        "Configuration shall be provided through environment variables so that the same code can be run locally and in deployment.",
    ])
    r.h2("4.2.6", "Maintainability")
    r.bullets([
        "The source code shall be divided into modules for parsing, ontology, ranking, council, inspection, search and interface.",
        "Each module shall be testable independently, and an automated test suite shall be run before any release.",
        "Database changes shall be managed by migration scripts.",
        "The front-end data layer shall be organised as replaceable service modules selected by configuration.",
    ])
    r.h2("4.2.7", "Security and Privacy")
    r.bullets([
        "Passwords shall be stored as salted PBKDF2-HMAC-SHA256 digests and not as plain text: with 210,000 iterations and a random 16-byte salt on the server, and with 200,000 iterations in the stand-alone browser mode.",
        "Session tokens shall be random, only their SHA-256 digest shall be stored, and a session shall expire after seven days.",
        "An account shall be locked for 15 minutes after five wrong passwords, and the system shall give the same error for an unknown e-mail address and for a wrong password.",
        "Copy, cut, paste and drop shall be blocked on the e-mail and password fields of the sign-in and sign-up forms, while the autofill and the strong-password suggestion of a password manager remain possible, and the sign-in form shall not be pre-filled after logout.",
        "No demo account and no self-service administrator account shall exist in a production configuration.",
        "Sign-in with Google shall be restricted to Gmail accounts and shall be verified on the server; the Google client identifier is the only value needed in the browser, and the client secret is not used.",
        "Personal data shall be redacted before any text is sent to an optional language-model service.",
        "Secrets such as API keys shall be read from environment variables and shall not be committed to the repository.",
    ])
    r.h2("4.2.8", "Fairness and Explainability")
    r.bullets([
        "Name, gender, age, nationality, location, institution prestige and employment gaps shall not enter any score.",
        "The score shall be invariant to a change of name, and this shall be verified by a test.",
        "Every automated verdict shall be explainable and shall be open to human review.",
    ])

    r.h1("4.3", "Hardware Requirements")
    r.p("The minimum recommended hardware for developing and running the system is listed below.", keep=True)
    r.bullets([
        "**Processor:** dual-core processor or higher; the evaluation was carried out on a laptop CPU in a single process.",
        "**Memory (RAM):** 4 GB minimum; 8 GB or more is recommended when the dense embedding model is installed.",
        "**Storage:** at least 5 GB of free space for the source code, the dependencies, the sample resume pools and the optional model files.",
        "**Display:** a standard monitor or laptop display of at least 1366 by 768 pixels.",
        "**Input devices:** keyboard and mouse or touch-pad.",
        "**Network:** not required for the offline configuration; an internet connection is needed only for the optional GitHub inspector, the language-model service, the Google sign-in, the managed database and the deployed web site.",
    ])
    r.p("The actual hardware requirements depend on the size of the resume pool and on whether the optional sentence-embedding model is installed.")

    r.h1("4.4", "Software Requirements")
    r.p("The software required to develop and run the system is summarised below and in the following table.", keep=True)
    r.bullets([
        "**Operating system:** Windows 10 or later, or Ubuntu Linux.",
        "**Programming languages:** Python 3.11 for the core and the API; JavaScript (JSX) for the web interface.",
        "**Web browser:** a modern browser such as Google Chrome or Microsoft Edge.",
        "**Code editor:** Visual Studio Code or another suitable editor.",
        "**Version control:** Git, with the source code hosted in a GitHub repository.",
        "**Hosting services (optional):** Vercel for the web interface, Render for the API, MongoDB Atlas (free M0 tier) for the database, and Streamlit Community Cloud for the Streamlit application.",
    ])
    r.table(["Component", "Package / version", "Purpose"], [
        ["Machine learning", "scikit-learn 1.3 or later, NumPy 1.24 or later, pandas 2.0 or later", "TF-IDF, cosine similarity, array and table processing"],
        ["Dense embeddings (optional)", "sentence-transformers 2.2 or later (all-MiniLM-L6-v2)", "Semantic similarity between resume and job description"],
        ["Document parsing", "PyMuPDF 1.23 or later, python-docx 1.0 or later, pytesseract 0.3.10 or later, Pillow 10 or later", "Extract text from PDF and DOCX, OCR for scanned pages"],
        ["Web API", "FastAPI 0.110 or later, Uvicorn 0.27 or later, pydantic-settings 2.2 or later", "REST service with automatic documentation"],
        ["Database", "SQLAlchemy 2.0.25 or later, Alembic 1.13 or later, psycopg 3.1 or later", "Persistence, migrations, PostgreSQL driver"],
        ["Document database", "MongoDB Atlas (M0), PyMongo 4.6 or later (pymongo[srv])", "Accounts, sessions and candidate pools in the deployed system"],
        ["Streamlit application", "Streamlit 1.30 or later, Plotly 5.18 or later", "Alternative recruiter workspace and charts"],
        ["Language model (optional)", "google-generativeai 0.4 or later (REST fallback)", "Narrative enrichment of agent output"],
        ["Web interface", "React 19, Vite, Tailwind CSS 4, lucide-react, pdfjs-dist, mammoth", "Dashboard, in-browser PDF and DOCX text extraction"],
        ["Testing", "pytest 7.4 or later, mongomock, Node.js built-in test runner", "Automated tests for the Python core and the API, and for the logic of the web interface"],
    ], "Software Components and Dependencies", [1.3, 2.7, 2.3], size=10, align=["left", "left", "left"])
    r.p("The availability of these packages must be verified before the system is run. The lean API requirements file omits the dense embedding model, so that the service fits in the memory of a free-tier host.")

    r.h1("4.5", "User Requirements")
    r.p("The user requirements describe the basic operations and information that a recruiter expects from the system.")
    r.h2("4.5.1", "Screening Workflow")
    r.bullets([
        "The recruiter should be able to sign up, to sign in with a Gmail address and a password or with a Google account, and to see the three-step workspace.",
        "The recruiter should be able to select one of the eight pre-configured roles or create a custom role and edit its competencies.",
        "The recruiter should be able to upload resumes or load a ready-made pool of 12, 50 or 100 resumes, and to start the screening engine with one action.",
        "The recruiter should be able to see the ranked candidates, the score breakdown, the verdict and the red flags.",
    ])
    r.h2("4.5.2", "Review and Decision")
    r.bullets([
        "The recruiter should be able to open a candidate dossier, read the scorecards of the four agents and replay the debate.",
        "The recruiter should be able to compare two candidates side by side and to ask the chatbot questions about the pool.",
        "The recruiter should be able to turn blind screening on or off and to export a report of the session.",
        "The recruiter should be able to record a shortlist or reject decision, which is stored with a time stamp.",
    ])
    r.h2("4.5.3", "Configuration, Logs and Error Information")
    r.bullets([
        "The recruiter should be able to adjust the weights of the ranker through the configuration of the service.",
        "The recruiter should be able to review the screening history and the audit log of recruiter actions.",
        "The system should give meaningful error messages when a file cannot be read, and should distinguish between a missing optional component and a failure of the core.",
    ])
    r.p("Summary. This chapter specified the functional, non-functional, hardware, software and user requirements of the system. They are the basis for the design presented in the next chapter.", indent=False)

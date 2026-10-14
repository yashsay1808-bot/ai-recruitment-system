"""Chapter 7: Testing and Evaluation"""
import json

PROJ = r"C:\DEV\Projects\Experiments\ai_recruitment_system"
RES = json.load(open(PROJ + r"\paper_results.json"))
ROWS = {x["file"]: x for x in RES["rows"]}


def build(r):
    r.chapter("Testing and Evaluation")
    r.p("Software testing is an important phase in the development of the AI-Powered Intelligent Recruitment System. It verifies that the implemented components behave as specified, finds defects, and validates that the modules work correctly together. For a screening system, testing has an additional purpose: it must show that the decisions follow the documented rules, that the system does not depend on protected attributes, and that it reports its limits instead of hiding them. The automated suite consists of 78 tests: 49 written with the pytest framework for the Python core, the API and the Streamlit interface, and 29 written with the Node.js test runner for the interview generator and the chatbot of the web interface. In the final run on the development machine all 49 Python tests passed in 16.25 seconds and all 29 JavaScript tests passed in 0.3 seconds.")

    r.h1("7.1", "Unit Testing")
    r.p("Unit testing is the process of testing individual components or functions of the software independently. The objective is to verify that each module performs its intended function. In this project, unit tests cover the resume parser, the skill ontology, the hybrid ranker and the explanation module, the council, the GitHub inspector, the talent search, the chatbot, the database and the authentication flow. The MongoDB-backed account and candidate API and the verification of Google sign-in tokens are covered by tests 32 to 40, and the interview generator and the chatbot of the web interface by tests 41 to 49. The test cases and their results are listed in Table 7.1.", keep=True)
    rows = [
        ["1", "Resume parser: parse a sample resume given as text (name, e-mail, phone, location, links, skills, education, experience, projects)", "Fields are extracted; B.E. is mapped to B.E. / B.Tech; experience of at least 1.5 years; at least one project", "Passed"],
        ["2", "Ontology: normalise aliases such as python 3, ml, sklearn, nlp, js, react.js, k8s, aws, dbms", "Each alias maps to its canonical skill name", "Passed"],
        ["3", "Ontology: extract skills from free text with abbreviations and tool names", "Python, Machine Learning, NLP, Scikit-Learn, PyTorch, Docker and AWS are found", "Passed"],
        ["4", "Ontology: match required skills of a job with a resume that has Flask instead of FastAPI", "Matched, missing (AWS) and partial (FastAPI via Flask) skills are reported; match above 60 percent", "Passed"],
        ["5", "Hybrid ranker and explanation: score a strong candidate and explain the score", "Overall score at least 75; skill score at least 80; experience score at least 85; a recommended tier with strengths and reasons", "Passed"],
        ["6", "Council: shape of the output for one candidate", "Four scorecards with scores from 0 to 100; verdict is one of four values; reasoning is present; mode is local", "Passed"],
        ["7", "Council: protected attributes in a resume", "Date of birth or age is reported by the auditor but is not used in scoring", "Passed"],
        ["8", "Council: candidate with missing required skills", "The verdict is REJECT", "Passed"],
        ["9", "Council: levelling and compensation bands", "Level is one of L3 to L6; minimum of the band is lower than the maximum (USD and INR)", "Passed"],
        ["10", "Council: biased text from a language model", "Age and gender categories are flagged; the score change is bounded at 10 points; human review is requested; personal data is redacted from the prompt", "Passed"],
        ["11", "Council: failure of the language-model service", "The council falls back silently; the error is recorded; a verdict is still produced", "Passed"],
        ["12", "GitHub inspector: extract user names from text and parsed data", "octocat and bob are found; feature pages are ignored; absent links give none", "Passed"],
        ["13", "GitHub inspector: verified claims", "Status ok; authenticity score at least 80; verdict VERIFIED; activity within six months", "Passed"],
        ["14", "GitHub inspector: exaggerated claims and forked repositories", "Go and Rust are unverified (Go exists only in a fork); risk is HIGH; score at most 50", "Passed"],
        ["15", "GitHub inspector: failures", "user_not_found, rate_limited (no score, retry time given) and no_github_found are returned without exceptions", "Passed"],
        ["16", "Talent search: query plan", "Minimum years 3.0; competencies distributed systems, Docker, microservices, AWS and deployment are extracted", "Passed"],
        ["17", "Talent search: ranking and explanation", "The best candidate is first with no missing competency; snippets carry Markdown and HTML highlights; scores are ordered", "Passed"],
        ["18", "Talent search: experience filter and irrelevant queries", "Strict mode keeps only the qualified candidate; an unrelated, empty or blank query returns nothing", "Passed"],
        ["19", "Talent search: index cache", "Building the index twice for the same pool returns the cached index", "Passed"],
        ["20", "Chatbot: top candidate, comparison, missing skills, experience and interview questions", "Each answer contains the expected names, scores and terms", "Passed"],
        ["21", "Database: recruiter registration, authentication, jobs and screening sessions", "Invalid key and duplicate e-mail are rejected; password check works; audit logs are written; job and session are stored", "Passed"],
        ["22", "Authentication: new accounts use PBKDF2", "The stored hash starts with pbkdf2; correct password is accepted and a wrong one rejected", "Passed"],
        ["23", "Authentication: legacy accounts", "An account with an old SHA-256 digest can still sign in", "Passed"],
        ["24", "Authentication: no seeded demo account and no self-service administrator", "The old demo credentials are rejected; a new user gets the standard clearance level", "Passed"],
        ["25", "Interface: signed-out user", "Only the sign-in form is shown; no tabs; no session user", "Passed"],
        ["26", "Interface: sign-up flow", "After sign-up the user returns to sign-in, is not signed in automatically, then signs in and sees the tabs", "Passed"],
        ["27", "Demo suite: gold-standard resume", "Rank 1, match of at least 85 percent, STRONG_HIRE, no flags", "Passed"],
        ["28", "Demo suite: buzzword resume", "Match below 45 percent, REJECT, UNVERIFIED_SKILL_CLAIMS and an experience flag", "Passed"],
        ["29", "Demo suite: lateral partial match", "LEAN_HIRE; FastAPI is a partial match; PyTorch is reported as missing", "Passed"],
        ["30", "Demo suite: corrupt resume", "ATS score below 35 and DATE_INCONSISTENCY flag", "Passed"],
        ["31", "Interface smoke test: the application boots with the new tabs", "No exception; all expected tabs exist; ranked candidates are present in the session", "Passed"],
        ["32", "Accounts (MongoDB): sign-up, sign-in, current user and sign-out", "Sign-up returns 201 without a password hash; sign-in returns a token; the token identifies the user; after sign-out the token is rejected", "Passed"],
        ["33", "Accounts: sign-up rules", "A non-Gmail address, a short password and an unknown role are rejected with 422; a duplicate address, in any letter case, with 409", "Passed"],
        ["34", "Accounts: wrong password and lockout", "An unknown address and a wrong password give the same 401 message; after five wrong passwords the account is locked (429), even for the right password", "Passed"],
        ["35", "Accounts: missing or invalid session token", "The current-user endpoint answers 401 without a token and with an invalid token", "Passed"],
        ["36", "Candidate pools served from the database", "The pools return 12, 50 and 100 candidates without internal fields; the default pool starts with CAN-001; an unknown pool gives 400", "Passed"],
        ["37", "Database start-up: seeding", "Running the start-up routine twice leaves exactly 162 candidate documents", "Passed"],
        ["38", "Database not configured", "The candidate endpoint answers 503 instead of failing", "Passed"],
        ["39", "Google sign-in: users and sessions", "A new user and a session are created without a password; a second sign-in reuses the user; an existing password account is linked and its password still works; a Google-only account cannot sign in with a password", "Passed"],
        ["40", "Google sign-in: verification of the ID token", "A wrong audience, a wrong issuer, an expired token and an unverified e-mail give 401; a non-Gmail address gives 403; a rejected token gives 401 and an unreachable Google gives 502; a missing client identifier gives 503", "Passed"],
        ["41", "Interview kit (web interface): size", "Each of the 162 candidates of the three pools gets 15 to 30 questions; the mean is between 19 and 24", "Passed"],
        ["42", "Interview kit: quality", "No repeated question or identifier, no broken text and a valid badge for every question; the kit is the same on every run; the question stored with the candidate is kept", "Passed"],
        ["43", "Interview kit: tailoring", "A skill-stuffed resume gets a verification question about its listed skills and a high-risk GitHub profile a GitHub question; DevOps and machine-learning profiles get different questions; missing data raises no error", "Passed"],
        ["44", "Chatbot (web interface): basics", "Greeting, help and pool statistics work; the text-only function still works; an empty query and an empty pool are handled", "Passed"],
        ["45", "Chatbot: conversation memory", "Why?, pronouns and interview questions for him refer to the candidate just discussed; pool-wide questions are not hijacked by it; a skill question is answered for the candidate in focus; lists are paged and a repeated request moves on; the third item of a list is resolved; a repeated profile request gives a different answer", "Passed"],
        ["46", "Chatbot: duplicate names (100-resume pool)", "The chatbot asks which person is meant, shows rank numbers and distinguishable choices, accepts a rank number or the first one, and asks before comparing an ambiguous name", "Passed"],
        ["47", "Chatbot: questions about the pool", "Comparison, filters by skill, years, verdict, freshers, flags and GitHub risk, rankings, shortlists, the role, the compensation band and score definitions are answered", "Passed"],
        ["48", "Chatbot: e-mail drafts", "Outreach, interview invitation and decline drafts are produced; the decline draft contains no internal scores or flags; a missing name is asked for", "Passed"],
        ["49", "Chatbot: fallback and robustness", "An unknown question gets an honest answer and varying suggestions; candidates with missing fields never print undefined; the core pool of 12 works", "Passed"],
    ]
    r.table(["Sl. No.", "Test description", "Expected result", "Actual result"], rows, "Unit and Component Test Cases", [0.55, 3.4, 3.4, 0.8], size=9.5, align=["center", "left", "left", "center"])
    r.p(f"{r.ref_next_tab()} summarises the number of tests of each test file.", keep=True)
    r.table(["Test file", "Area covered", "Tests", "Result"], [
        ["test_parser.py", "Resume parser", "1", "Passed"],
        ["test_ontology.py", "Skill ontology and matching", "3", "Passed"],
        ["test_hybrid_ranker.py", "Hybrid ranker and explanation", "1", "Passed"],
        ["test_agentic_council.py", "Four-agent council", "6", "Passed"],
        ["test_github_inspector.py", "GitHub authenticity inspector", "4", "Passed"],
        ["test_talent_rag.py", "Hybrid talent search", "4", "Passed"],
        ["test_chatbot.py", "Recruiter chatbot", "1", "Passed"],
        ["test_database.py", "Recruitment database", "1", "Passed"],
        ["test_auth_flow.py", "Authentication and sign-in flow", "5", "Passed"],
        ["test_demo_suite.py", "Four demonstration resumes end to end", "4", "Passed"],
        ["test_ui_smoke.py", "Application start-up", "1", "Passed"],
        ["test_mongo_api.py", "Accounts, sessions, Google sign-in and candidate pools (MongoDB)", "18", "Passed"],
        ["interview.test.mjs", "Interview kit of the web interface", "8", "Passed"],
        ["chatbot.test.mjs", "Chatbot of the web interface", "21", "Passed"],
        ["Total", "", "78", "78 passed"],
    ], "Summary of the Automated Test Run", [2.2, 2.6, 0.7, 1.5], size=10, align=["left", "left", "center", "center"])
    r.p("The 49 Python tests ran in 16.25 seconds and the 29 JavaScript tests in 0.3 seconds. The account tests use an in-memory MongoDB, and the Google tests replace the call to Google with a simulated answer, so that no network access and no secret is needed.")

    r.h2("7.1.1", "Objectives of Unit Testing")
    r.p("The main objectives of unit testing are:", indent=False, keep=True)
    r.bullets([
        "verify the correctness of individual functions and classes;",
        "make sure that each component works independently of the user interface;",
        "find errors in parsing, matching and scoring logic early;",
        "verify the handling of missing, invalid or unusual input, such as an empty query or a failed external service;",
        "validate that fairness-related behaviour (flags for protected attributes, redaction of personal data) works as specified; and",
        "improve the reliability and maintainability of the system through repeatable regression tests.",
    ])

    r.h2("7.1.2", "Detailed Explanation of Test Case 1")
    r.p("The resume parser is the entry point of the pipeline. If it extracts a field incorrectly, every later score is affected, so Test Case 1 verifies the parser with a complete sample resume. The sample contains a header with name and contact details, a professional summary, a skills section, an education section with a CGPA, a work experience section with a date range that ends with *Present*, and a project section.")
    r.p("**Objective:** verify that the parser separates the sections of a resume and extracts the required fields correctly.", indent=False)
    r.p("The test case involves the following steps:", indent=False, keep=True)
    r.numbered([
        "Prepare the sample resume as a text document.",
        "Pass the bytes of the document and its file name to the parser.",
        "Check the name, e-mail address, telephone number and location.",
        "Check that the skills include Python and Machine Learning after normalisation.",
        "Check that the degree is mapped to B.E. / B.Tech.",
        "Check that the years of experience computed from the date range are at least 1.5.",
        "Check that at least one project is detected.",
    ])
    r.p("**Expected result:** the parser returns the name *Rahul Nair*, the e-mail *rahul.nair@email.com*, a telephone number containing 98450, the location Bengaluru, the normalised skills, the degree B.E. / B.Tech, an experience of at least 1.5 years and at least one project. **Actual result:** all conditions were satisfied and the test passed.", indent=False)

    r.h1("7.2", "Integration Testing")
    r.p("Integration testing verifies the interaction between modules of the system. It ensures that the modules communicate correctly and that information flows through the pipeline as intended. The following aspects are considered:", keep=True)
    r.bullets([
        "**Parser and ontology:** skills extracted from the text of a resume are normalised to canonical names and are matched against the required skills of a job (tests 1 to 4).",
        "**Ontology, ranker and explanation:** the match percentage of the ontology feeds the technical score of the ranker, and the breakdown of the ranker feeds the explanation module (test 5).",
        "**Features and agents:** the common feature builder passes the same evidence-weighted coverage, timeline and term counts to the four agents, and the auditor reads the text written by the others (tests 6 to 11).",
        "**Council and verdict gates:** missing required skills, red flags, inverted dates and missing education change the verdict as specified (tests 8, 27 to 30).",
        "**GitHub report and Tech Lead:** the report of the inspector is picked up by the Tech Lead agent as additional evidence of repository maturity, while failures of the inspector do not stop the council (tests 12 to 15).",
        "**Search and chatbot:** the chunk index of the talent search is reused by the queries of the chatbot, and the chatbot composes its answers from the ranked results (tests 16 to 20).",
        "**Authentication and interface:** the sign-in and sign-up flow controls which tabs are visible, and the interface boots with the ranked candidates in its session (tests 22 to 26 and 31).",
        "**Accounts and database:** the account endpoints, the session store and the seeding of the candidate pools work together on a MongoDB database (tests 32 to 38), and the Google endpoint combines the check of the token with the user store (tests 39 and 40).",
        "**Interview generator, chatbot and pool data:** the logic of the web interface is exercised on the real files of all three candidate pools (tests 41 to 49).",
    ])
    r.p("The account and candidate endpoints of the API are covered by automated tests (tests 32 to 40). The relational endpoints for jobs, resumes, screenings and audit logs are exercised manually through the automatically generated documentation page; automated tests for them have not yet been written, and they are listed among the future enhancements.")

    r.h1("7.3", "System Testing")
    r.p("System testing evaluates the integrated system to verify whether the implemented functionality works together as expected. It focuses on the complete screening of a pool of resumes, the correctness of the verdicts, the explanation of the decisions and the behaviour of the interface. Four purpose-written resumes (the demonstration suite) are used to probe specific behaviours of the complete pipeline. Each is run against the Machine Learning Engineer role with 17 required skills and a two-year minimum. Table 7.3 shows the results.", keep=True)
    tc = {k: ROWS[v] for k, v in {"TC1": "Test_Case_1_Gold_Standard_Pass.txt", "TC2": "Test_Case_2_Buzzword_Exaggeration_Fail.txt", "TC3": "Test_Case_3_Lateral_Partial_Match.txt", "TC4": "Test_Case_4_Corrupt_ATS_Format_Error.txt"}.items()}

    def fl(x):
        names = [f.replace("_", " ").title() for f in x["flags"]]
        return ", ".join(names) if names else "None"
    r.table(["Test resume", "Behaviour probed", "Match (%)", "ATS", "Council C", "Verdict", "Red flags"], [
        ["TC1 Gold standard", "Strong candidate with evidence", f"{tc['TC1']['proposed']:.1f}", f"{tc['TC1']['ats']:.0f}", f"{tc['TC1']['council']:.1f}", "STRONG_HIRE", fl(tc["TC1"])],
        ["TC2 Buzzword exaggeration", "35 listed skills, 4 months of experience, no metrics", f"{tc['TC2']['proposed']:.1f}", f"{tc['TC2']['ats']:.0f}", f"{tc['TC2']['council']:.1f}", "REJECT", fl(tc["TC2"])],
        ["TC3 Lateral partial match", "Flask developer for a FastAPI and PyTorch role", f"{tc['TC3']['proposed']:.1f}", f"{tc['TC3']['ats']:.0f}", f"{tc['TC3']['council']:.1f}", "LEAN_HIRE", fl(tc["TC3"])],
        ["TC4 Corrupt format", "Damaged layout and inconsistent dates", f"{tc['TC4']['proposed']:.1f}", f"{tc['TC4']['ats']:.0f}", f"{tc['TC4']['council']:.1f}", "REJECT", fl(tc["TC4"])],
    ], "System Test Results of the Demonstration Resumes", [1.2, 1.5, 0.65, 0.5, 0.7, 1.3, 1.75], size=9, align=["left", "left", "center", "center", "center", "center", "left"])
    r.p("The following aspects are considered during system testing:", keep=True)
    r.bullets([
        "**Ranking:** the gold-standard resume must rank first and receive STRONG_HIRE without flags.",
        "**Keyword stuffing:** the buzzword resume must be rejected, with the flags for the experience deficit and the unverified claims.",
        "**Related skills:** the lateral resume must receive partial credit for FastAPI through Flask, report PyTorch as missing and receive LEAN_HIRE.",
        "**Uncertainty:** the corrupt resume must have a low ATS score, an inconsistency flag and a request for human review instead of a confident verdict.",
        "**Interface:** the application must start with all tabs and a ranked pool.",
    ])
    r.p("System testing was performed in a controlled environment with the offline TF-IDF configuration. The results are produced by running the real pipeline and are not hard-coded; the scores can differ by a small amount when the dense model is installed.")
    r.p("The deployed system was also checked end to end, partly by hand and partly with a few requests. The health endpoint of the API answers 200 and reports the database as connected; the three candidate pools return 12, 50 and 100 candidates; a request from the origin of the web site receives the cross-origin permission header; a login with an unknown address receives the generic 401 message; the built web site contains the address of the API and the Google client identifier; and a sign-up and a sign-in were carried out on the live site by the team, after which the new accounts were visible in the users collection of the database. No load test was made.")
    r.p("The sign-in and sign-up forms were checked in a browser against the built application. Scripted paste, copy and cut events were blocked on the four credential fields, and a real keyboard copy and paste left the password field empty. The sign-in fields unlock when they are clicked, a value that is filled programmatically, as a password manager does, is accepted, and the sign-up password field keeps the new-password hint that triggers the strong-password suggestion. The Interview Assistant page shows the filter chips and about twenty questions for a candidate, and the chatbot page shows follow-up suggestions, answers a follow-up question about the candidate discussed last, and scrolls to the newest message.")

    r.h1("7.4", "User Acceptance Testing")
    r.p("User acceptance testing evaluates whether the system satisfies the requirements from the point of view of its intended user, a recruiter. It focuses on the clarity of the interface, the usefulness of the explanations and the correctness of the results. For this system, the acceptance checks were carried out by the project team with the demonstration script of the project, which walks through the sign-in, the loading of a pool, the leaderboard, the dossier with the debate, the blind-screening switch, the comparison, the interview kit, the chatbot and the export of a report. The following activities were checked:", keep=True)
    r.bullets([
        "**Workflow:** a new user can reach the leaderboard in three steps without instructions.",
        "**Leaderboard:** the ranking, the score bars, the evidence lines, the skill chips and the number of flags are understandable.",
        "**Dossier:** the four scorecards, the level and the compensation band, and the replayable debate explain why a verdict was given.",
        "**Blind mode:** names become neutral identifiers throughout the interface when blind screening is switched on.",
        "**Interview kit:** the questions are specific to the selected candidate, are grouped in categories and can be filtered by category.",
        "**Chatbot:** a follow-up question such as why? refers to the candidate discussed last, a long list can be continued with show more, and a conversation can be exported as a Markdown file.",
        "**Error handling:** a missing optional component or a failed external call produces a clear message and does not stop the screening.",
    ])
    r.p("A formal usability study with external recruiters has not been conducted, and whether the views help recruiters to decide better or faster remains future work. The system is considered acceptable for demonstration because the implemented functions operate as intended, the displayed information is understandable and the results of the performed tests satisfy the defined criteria.")
    r.p("Summary. This chapter described the testing of the system. The 78 automated tests, spread over fourteen test files (twelve Python files and two JavaScript files), all passed, the integration of the modules was verified through the shared pipeline, and the system tests confirmed the intended behaviour on four probing resumes and on the deployed service. The experimental evaluation on the resume pools is presented in the next chapter.", indent=False)

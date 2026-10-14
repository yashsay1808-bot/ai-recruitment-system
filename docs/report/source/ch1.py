"""Chapter 1: Introduction"""


def build(r):
    r.chapter("Introduction")
    r.p("Recruitment is one of the most information-intensive activities of an organisation. A single advertised vacancy can attract hundreds of applications, and every application must be read, interpreted and compared against the requirements of the role before a shortlist can be prepared. Automated screening software, usually called an Applicant Tracking System (ATS), has therefore become the first gatekeeper in many hiring pipelines [@black,@upadhyay,@vanesch]. Studies of artificial intelligence in human-resources management stress both the efficiency gains and the managerial challenges of such tools [@tambe], and research on automated interviews shows that candidates accept automated decisions less readily when the stakes are high [@langer]. Because the screening stage decides which people are never seen by a human recruiter, the way it ranks candidates has direct consequences for the people applying and for the organisations hiring.")
    r.p("Most commercial and academic screening tools rank candidates by lexical overlap with the job description. Such a keyword approach is fast and easy to implement, but it rewards vocabulary rather than evidence: a resume that lists every fashionable tool can outrank one that demonstrates fewer tools with measurable results. At the other end of the spectrum, learned screeners based on neural networks and large language models can capture meaning [@qin_pjf,@bhatia,@sbert], yet they are opaque and have been shown to inherit demographic bias from their training data [@dastin,@wilson,@armstrong]. Regulation is moving in the same direction: the European Union Artificial Intelligence Act places systems that filter or evaluate job applicants among high-risk applications, which brings obligations of transparency and human oversight [@euaiact].")
    r.p("The AI-Powered Intelligent Recruitment System developed in this project, referred to in the rest of this report as the system or Nexus ATS, is the second phase of a university recruitment project. The first phase was a keyword-matching ATS. The second phase replaces the keyword score with an explainable, evidence-based and bias-aware decision process. It parses resumes, normalises skills through an auditable skill ontology, scores each candidate on seven weighted signals, optionally hides identity before any scoring takes place, and lets a council of four specialised software agents review every candidate and return a verdict together with the reasons, the red flags and the points on which the agents disagree.")

    r.h1("1.1", "General Overview")
    r.p("Hiring is a decision made under limited information. A resume is a self-reported document, and the claims it makes (skills, years of experience, projects, certifications) are not verified at the screening stage. A recruiter reading a resume quickly looks for supporting evidence: where was the skill used, for how long, and with what result? A keyword-based ATS cannot do this. It can only count how many words of the job description also occur in the resume. As a consequence it cannot tell that FastAPI and Flask are closely related, it cannot tell a skill that was demonstrated in a project from a skill that was merely listed, and it cannot notice that the dates of a resume are impossible.")
    r.p("The system presented in this report treats a skill as a **claim that needs evidence**. A required skill that appears in the experience or project text of a resume earns full credit; a skill that appears only in the skills list earns half credit. This simple rule, described in detail in Chapter 3 and Chapter 6, is the basis of the evidence-weighted coverage that drives both the ranking and the final verdict. It allows the system to separate a genuine candidate from a keyword-stuffed one, which a plain keyword score cannot do.")
    r.p("The system is implemented in Python for the scoring core and in React for the recruiter interface. The Python core contains the resume parser (with an optical character recognition fallback for scanned documents), the job-description parser, the skill ontology, the skill-gap analyser, the hybrid ranker, the resume quality analyser, the explainable-AI module, the blind-screening filter, the four-agent council, the GitHub authenticity inspector, the hybrid talent-search engine and the interview-question generator. The same core is exposed through a FastAPI web service backed by a relational database, and through a Streamlit application. In the deployed system the web interface calls the API, which stores user accounts, sessions and the candidate pools in a MongoDB Atlas database. The React interface, deployed as a web site, offers a guided workflow for the recruiter: choose a role, load candidates, run the screening engine and review the results on a leaderboard, a candidate dossier, a side-by-side comparison, an interview assistant, an analytics page and a recruiter chatbot.")
    r.p("Two design principles guided the whole project. The first is explainability: every number shown to the recruiter can be traced to a rule, and every verdict is accompanied by the features that produced it. The second is graceful degradation: the system runs completely offline, using TF-IDF vectors when the dense language model is not installed and rule-based text when no language-model service is configured, so that results remain reproducible and the system can be demonstrated without network access.")

    r.h1("1.2", "Problem Statement")
    r.p("Keyword-based applicant tracking systems rank candidates by counting how many words of a job description appear in a resume. This approach has three weaknesses. First, it rewards keyword stuffing and cannot distinguish a skill that is demonstrated in a project from one that is only listed. Second, it cannot reason about related skills, so a candidate who knows Flask is scored as having no knowledge of FastAPI. Third, it produces a single number with no explanation, so a rejected candidate and the recruiter who rejected him or her have no way of knowing why the decision was taken.")
    r.p("Learned screening models address the first two weaknesses but introduce a new one. Studies of resume screening with embedding models and large language models have found that the same resume receives different scores when only the name of the candidate is changed [@wilson,@armstrong], which echoes the classical field experiments on labour-market discrimination [@bertrand]. A screening tool that cannot explain its ranking, cannot demonstrate that it ignores protected attributes and cannot hand uncertain cases to a person is therefore both ethically and legally fragile [@euaiact,@gdpr].")
    r.p("The problem addressed by this project is the design and implementation of a recruitment screening system that (i) ranks candidates by evidence rather than by vocabulary, (ii) understands related skills and synonyms, (iii) is invariant to the name and contact details of the candidate, (iv) explains every score and verdict, (v) reports its own uncertainty and routes doubtful cases to a human reviewer, and (vi) runs without network access so that its behaviour can be reproduced and tested.")
    r.p("The system must also keep the roles of its components separate. Detecting that a resume mentions a skill, crediting a related skill, discounting an unevidenced claim, flagging an inconsistent date and issuing a hiring verdict are different operations, and each of them must be visible to the recruiter on its own rather than being merged into one opaque score.")

    r.h1("1.3", "Objectives")
    r.p("The main objectives of the project are:", indent=False, keep=True)
    r.numbered([
        "To extract structured information (contact details, skills, education, experience, projects and certifications) from resumes in PDF, DOCX and plain-text formats, with an OCR fallback for scanned documents.",
        "To build an auditable skill ontology with alias normalisation, fuzzy matching and partial credit for related skills, and to report matched, partially matched and missing skills for every candidate.",
        "To implement a seven-factor hybrid ranking engine that combines skill match, semantic similarity, experience, education, projects, certifications and resume quality into one explainable score.",
        "To treat skills as claims and to discount skills that are listed but not demonstrated, through an evidence-weighted skill coverage measure.",
        "To implement bias-aware blind screening that removes names, contact details, locations, profile links and gendered words before any agent evaluates a resume, and to verify name invariance through a counterfactual name-swap test.",
        "To implement a four-agent council (Tech Lead, Culture and Retention, Fair-Hiring Auditor, and Seniority and Compensation) that produces a consensus verdict with knock-out gates, red flags, confidence, dissent and human-review triggers.",
        "To provide a recruiter interface with a leaderboard, candidate dossier, comparison matrix, interview-question generator, analytics page and a retrieval-grounded recruiter chatbot, and a REST API with server-side authentication and Google sign-in for integration.",
        "To evaluate the system on synthetic resume pools, to measure its processing time, and to state the limitations of the evaluation honestly.",
    ])

    r.h1("1.4", "Scope")
    r.p("The AI-Powered Intelligent Recruitment System covers the complete screening stage of a hiring pipeline: from the moment a recruiter selects a role and loads resumes to the moment a ranked, explained shortlist is available for human review. The scope includes resume and job-description parsing, skill normalisation and matching, multi-signal scoring, bias-aware anonymisation, multi-agent review, GitHub-based verification of claimed programming languages, natural-language search over the candidate pool, interview-question generation, a recruiter dashboard and a REST service with a persistent screening history, user accounts and a managed document database.")
    r.p("The system is designed for technical roles. The skill ontology contains 79 canonical skills grouped into eight categories (programming languages, artificial intelligence and machine learning, web and backend frameworks, data science and analytics, cloud and DevOps, databases and storage, frontend technologies and software engineering) and eight role families are pre-configured: machine learning engineer, cloud DevOps and site-reliability lead, full-stack AI engineer, data-platform engineer, backend architect, AI-safety auditor, business-intelligence analyst and Python backend developer. A recruiter can also create a custom role by editing the competency list.")
    r.p("The system is a decision-support tool. It does not decide to hire or reject a candidate on its own: it ranks, explains and flags, and a person takes the decision. The project is an engineering prototype evaluated on synthetic data. Evaluation on real applicant pools with recruiter judgements as ground truth, large-scale multi-user deployment, validation of certificates with their issuers and measurement of group-fairness metrics on demographically labelled data are outside the scope of the current implementation and are listed as future enhancements in Chapter 9.")

    r.h1("1.5", "Motivation")
    r.p("The motivation for this project comes from three observations. The first is practical. Recruiters receive far more applications than they can read, and the first filter decides who is read at all. A filter that rewards keyword stuffing penalises honest candidates, and a filter that cannot explain itself leaves the recruiter unable to defend a decision. The second observation is ethical. It has been documented that an AI recruiting tool built at a large technology company was abandoned after it penalised resumes associated with women [@dastin], that identical resumes with different names receive different numbers of call-backs [@bertrand], and that the same pattern appears in modern language-model screeners [@wilson,@armstrong]. A system that treats fairness as a design requirement rather than as an afterthought is therefore needed. The third observation is regulatory: recruitment systems are classified as high-risk under the European Union Artificial Intelligence Act, and personal data in resumes is protected by data-protection law [@euaiact,@gdpr].")
    r.p("The project also offers an opportunity to combine several areas of computer science in a single working system: natural-language processing for parsing and semantic similarity, information retrieval for talent search, rule-based reasoning for the skill ontology and the red-flag gates, multi-agent evaluation for the council, web engineering for the dashboard and API, and software testing for the verification of the whole pipeline. Developing these components as separate, testable modules also gives the team practical experience of the engineering practices expected of a production system.")

    r.h1("1.6", "Methodology")
    r.p("The development of the system followed an iterative, module-by-module process. Each stage produced a tested component before the next stage was started. The main stages are described below, and the end-to-end workflow is shown later in Figure 5.1.", keep=True)
    r.bullets([
        "**Requirement analysis:** the weaknesses of the Phase 1 keyword ATS were analysed and converted into functional and non-functional requirements (Chapter 4).",
        "**Literature survey:** research on person-job fit, semantic retrieval, algorithmic hiring bias, explainable AI and multi-agent evaluation was reviewed to identify the gaps that the system should address (Chapter 2).",
        "**Data preparation:** a pilot pool of twelve resumes (eight resumes shipped with the project and four purpose-written test cases), a 50-candidate demonstration pool and a 100-resume multi-role synthetic benchmark were prepared. All resumes are synthetic.",
        "**Parsing and ontology:** the resume parser, the job-description parser and the skill ontology with alias normalisation, fuzzy matching and related-skill rules were implemented.",
        "**Scoring and explanation:** the seven-factor hybrid ranker, the skill-gap analyser, the ATS quality analyser and the explainable-AI module were implemented.",
        "**Fairness and review:** the blind-screening filter, the four-agent council with consensus, gates and red flags, and the GitHub authenticity inspector were implemented.",
        "**Interfaces and persistence:** the React dashboard, the Streamlit application, the FastAPI service and the SQLAlchemy data model were developed, and for the deployed system a MongoDB store for accounts, sessions and candidate pools with server-side authentication was added.",
        "**Verification and evaluation:** a suite of 78 automated tests (49 on the Python side and 29 on the web-interface side) was written, and experiments on processing time, ranking agreement with the keyword baseline, evidence ablation, name invariance, weight sensitivity, retrieval quality and adversarial resumes were run (Chapters 7 and 8).",
    ])

    r.h1("1.7", "Applications")
    r.p("Although the prototype was built for technical roles, the approach applies wherever a large number of documents must be compared against a written set of requirements and the decision has to be explained. The main applications are listed below.", keep=True)
    r.bullets([
        "**Corporate recruitment:** shortlisting candidates for engineering, data and analytics vacancies with an explanation for every ranking position.",
        "**Campus placement:** ranking student resumes against the requirements of visiting companies, with skill-gap reports that tell students what to learn.",
        "**Recruitment agencies:** searching a large pool of stored resumes with natural-language questions and receiving evidence snippets rather than names only.",
        "**Fair-hiring audits:** running the same pool in standard and blind modes and comparing the outcomes, which supports internal audits of screening practice.",
        "**Resume improvement:** the ATS quality analyser produces actionable suggestions that a candidate can use to improve a resume.",
        "**Interview preparation:** the interview assistant generates about twenty tailored technical, system-design, gap-probing, red-flag and behavioural questions per candidate, each with a note on what to look for, for the interview panel.",
    ])

    r.h1("1.8", "Advantages")
    r.bullets([
        "**Evidence-based ranking:** a skill that is demonstrated counts for more than a skill that is only listed, which separates genuine candidates from keyword-stuffed ones.",
        "**Explainability:** every score, verdict and red flag comes with a stated reason, and the cross-examination between the agents is stored and can be replayed.",
        "**Fairness by design:** blind screening removes direct identifiers before any agent sees the resume, an auditor agent can reduce the weight of a biased evaluator, and name invariance is tested explicitly.",
        "**Uncertainty handling:** the council reports a confidence value, lists dissenting agents and requests human review for borderline or poorly documented cases instead of issuing a confident verdict.",
        "**Offline operation:** all scoring components run locally without network access; dense embeddings, language-model narratives and the GitHub inspector are optional and degrade gracefully.",
        "**Speed:** a complete screening takes about 30 milliseconds per resume on a laptop CPU in the offline configuration.",
        "**Modularity:** the scoring core is independent of the user interface, so the same algorithms serve the React dashboard, the Streamlit application and the REST API.",
        "**Reproducibility:** the decision logic is deterministic, and the thresholds and weights are configurable.",
    ])

    r.h1("1.9", "Limitations")
    r.bullets([
        "All evaluation resumes are synthetic and were written with knowledge of the system's rules. The results therefore demonstrate consistency and mechanism, not accuracy on real hiring outcomes.",
        "The weights, thresholds and gates are chosen by the developers and are not learned from recruiter decisions. They were found to be stable under random changes of 20 percent, but they have not been calibrated against real data.",
        "The skill ontology contains 79 skills. Specialised vocabularies outside these skills are not recognised except through the free-text fallback.",
        "A skill is considered evidenced when it appears outside the skills block of the resume. This is a proxy for demonstrated experience and can be defeated by an adversary who repeats skills in several places.",
        "Blind screening removes direct identifiers. Proxy variables such as the name of an institution or a location are flagged but not corrected, and no group-fairness metric was computed because the pools carry no demographic labels.",
        "Certifications are counted but are not validated against the issuing body.",
        "The GitHub inspector can only judge public repositories. A missing or thin public profile is reported as insufficient data and is not treated as evidence of dishonesty.",
        "Compensation bands produced by the seniority agent are indicative planning ranges and are not market data.",
        "The deployed system runs on free cloud tiers that sleep when idle (the first request after a pause can take about 50 seconds) and it has not been load-tested.",
        "The 100-resume benchmark reuses 50 candidate names for different profiles, so a name alone does not identify a candidate in that pool; the chatbot asks which person is meant.",
    ])

    r.h1("1.10", "Project Outcomes")
    r.p("The project produced a working recruitment screening system with the following outcomes.", keep=True)
    r.bullets([
        "A Python core library of about ten thousand lines containing every scoring algorithm, together with a FastAPI service, a SQLAlchemy data model with an Alembic migration, a Streamlit application and a React dashboard, with a MongoDB document store for accounts, sessions and candidate pools.",
        "An auditable skill ontology of 79 canonical skills with 353 alias entries, eight categories and fifteen related-skill pairs.",
        "A seven-factor ranker and a four-agent council that rank twelve pilot resumes in about 30 milliseconds each and place the strong test candidate first with a score of 88.1 percent, while rejecting the keyword-stuffed test resume that a keyword baseline scores at 47.1 percent.",
        "Name invariance: the score and the verdict did not change in 96 name-substitution runs, and conclusions were stable under random changes of the weights (mean Kendall rank correlation 0.969 over 200 draws).",
        "A suite of 78 automated tests (49 in Python and 29 in JavaScript) covering the parser, the ontology, the ranker, the council, the GitHub inspector, the talent search, the chatbot and the interview generator of the web interface, the database, the authentication flow, the MongoDB-backed account and candidate API and the verification of Google sign-in tokens, all of which pass.",
        "A live deployment on free cloud tiers (the web interface on Vercel, the API on Render and the data in MongoDB Atlas) with server-side accounts, sessions and Google sign-in, so that the system can be demonstrated and evaluated by other users.",
    ])

    r.h1("1.11", "Organization of the Report")
    r.p("The remainder of this report is organised as follows.", keep=True)
    r.bullets([
        "**Chapter 2: Literature Survey** reviews research on person-job fit, resume parsing, semantic and hybrid retrieval, algorithmic hiring bias, explainable AI and multi-agent evaluation, and identifies the research gaps.",
        "**Chapter 3: Preliminaries** presents the concepts and techniques on which the system is built, including TF-IDF, BM25, dense sentence embeddings, fuzzy matching, fairness and explainability, and rank-correlation metrics, with their formulas.",
        "**Chapter 4: Requirement Specifications** lists the functional, non-functional, hardware, software and user requirements.",
        "**Chapter 5: System Design** presents the workflow, architecture, data-flow, use-case, sequence and database designs and the interface design.",
        "**Chapter 6: Implementation** describes the technologies used, the implementation of each module with its formulas, and the difficulties met during development.",
        "**Chapter 7: Testing and Evaluation** describes unit, integration, system and user-acceptance testing with the test cases and their results.",
        "**Chapter 8: Results** presents screenshots of the running system and the experimental results.",
        "**Chapter 9: Conclusion and Future Enhancements** summarises the work and proposes directions for future improvement.",
    ])

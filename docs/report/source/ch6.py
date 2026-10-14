"""Chapter 6: Implementation"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "fig")


def build(r):
    r.chapter("Implementation")
    r.p("This chapter describes the technologies, the modules and the procedures involved in the implementation of the AI-Powered Intelligent Recruitment System. The system is implemented in Python for the scoring core and the API and in JavaScript for the web interface. Every module of the core is described with the formulas that it computes and with short excerpts of the source code. The chapter also discusses the difficulties met during development and the strategies used to overcome them, and ends with pseudocode of the overall screening pipeline.")

    r.h1("6.1", "Overview of Technologies Used")
    r.p("The system combines programming languages, libraries and hosting services. Each technology supports a particular responsibility, including document parsing, text analysis, ranking, persistence and presentation.")
    r.h2("6.1.1", "Technologies Used")
    r.numbered([
        "**Python 3.11:** the primary language of the core library. It implements the parser, ontology, ranker, council, inspector, search and generator, and the API.",
        "**scikit-learn, NumPy and pandas:** scikit-learn provides the TF-IDF vectoriser and cosine similarity [@sklearn]; NumPy holds score arrays and the BM25 index; pandas supports tabular analytics [@pandas].",
        "**sentence-transformers (optional):** loads the compact model all-MiniLM-L6-v2 to compute 384-dimensional embeddings [@sbert,@minilm,@hftransformers]. When it is not installed, the system falls back to TF-IDF.",
        "**PyMuPDF, python-docx and pytesseract:** extract text from PDF and DOCX files and perform OCR on scanned pages [@tesseract].",
        "**FastAPI, Uvicorn and Pydantic:** implement the REST API with automatic documentation, request validation and typed schemas [@fielding].",
        "**SQLAlchemy, Alembic and SQLite:** the object-relational model, schema migrations and the local database.",
        "**MongoDB Atlas and PyMongo:** the managed document database that stores the accounts, the sessions and the candidate pools of the deployed system.",
        "**Streamlit and Plotly:** the first recruiter workspace and its interactive charts.",
        "**React 19, Vite and Tailwind CSS 4:** the web interface (Nexus ATS). The libraries pdfjs-dist and mammoth extract text from PDF and DOCX files inside the browser, and lucide-react provides the icons.",
        "**Google Identity Services:** optional sign-in with Google, restricted to Gmail accounts; the ID token is verified on the server.",
        "**pytest:** the automated test suite.",
        "**Git, GitHub, Vercel, Render and MongoDB Atlas:** version control and the hosting of the web interface, of the API and of the database.",
    ])
    r.p("These technologies are used together to build the screening pipeline: documents are parsed in Python, scored by the ranker and the council, stored through SQLAlchemy or MongoDB and presented through React or Streamlit.")

    r.h1("6.2", "Implementation Details of Modules")
    r.p("The system is divided into modules with a single responsibility each. The modules are described in the order in which they are used in a screening.")

    # ------------------------------------------------------------------ Module 1
    r.h3("Module 1: Resume Parser")
    r.p("The resume parser converts a file into a structured profile. For PDF files, PyMuPDF reads the text layer page by page. If the text of a page is shorter than 30 characters, the page is regarded as scanned, rendered at 200 dots per inch and passed to Tesseract OCR; a document that yields almost no text at all is processed entirely by OCR. DOCX files are read with python-docx, and plain text files are decoded directly. The text is then cleaned and segmented into sections by header patterns.")
    r.p("The parser extracts the following information:", keep=True)
    r.bullets([
        "name, e-mail address, telephone number, location, and LinkedIn and GitHub links;",
        "education: degree, branch, institution, CGPA or marks and year;",
        "experience: total years (the union of valid month intervals, Equation 3.1), detected job titles and the timeline of roles;",
        "projects: title, description and the skills used; and",
        "certifications and the list of skills, normalised through the ontology.",
    ])
    r.p("Dates are read at month resolution. A role with an end date before its start date, or with a start date in the future, is excluded from the experience total and recorded as an inconsistency. Valid overlapping roles are merged so that the same month is never counted twice. The parser returns a dictionary that contains these fields together with the cleaned raw text and the sections, which is the input of every later module.")

    # ------------------------------------------------------------------ Module 2
    r.h3("Module 2: Job-Description Parser")
    r.p("The job-description parser converts the text of a vacancy into evaluation criteria. The job title is taken from a hint or from one of the first lines that contains a role word such as *engineer*, *developer* or *analyst*. All skills of the text are extracted by phrase-boundary matching against the ontology. If the text contains a section introduced by words such as *preferred*, *good to have* or *nice to have*, the skills of this section become preferred skills and the others become required skills. The minimum experience is read from patterns such as *3+ years*, and the preferred degrees from patterns such as *B.E.*, *M.Tech* or *Ph.D.*. The pre-configured roles of the interface use the same structure, with 17 required skills for the machine-learning role used in the evaluation.")

    # ------------------------------------------------------------------ Module 3
    r.h3("Module 3: Skill Ontology and Skill-Gap Analyser")
    r.p("The ontology holds 79 canonical skills in eight categories, with 353 entries in its alias lookup table (canonical names and aliases). Every skill is stored with its aliases and its category. At start-up, one regular expression per alias is compiled, with the longest aliases first, so that *machine learning* is found before *learning*. Short aliases of up to three characters, such as *C*, *Go* or *ML*, use strict boundaries so that they are not found inside other words. The function that matches the required skills of a job with the skills of a candidate is shown in Listing 6.1.")
    r.code('''def match_skills(jd_skills, resume_skills):
    norm_jd = [normalize_skill(s) or s.strip() for s in jd_skills]
    set_resume = {normalize_skill(s) or s.strip() for s in resume_skills}
    matched, partially_matched, missing = [], [], []
    for req_skill in norm_jd:
        if req_skill in set_resume:
            matched.append(req_skill)
        else:
            for res_skill in set_resume:
                if (req_skill, res_skill) in related_pairs or \\
                   (res_skill, req_skill) in related_pairs:
                    partially_matched.append({
                        "required_skill": req_skill,
                        "related_candidate_skill": res_skill})
                    break
            else:
                missing.append(req_skill)
    raw = (len(matched) * 1.0 + len(partially_matched) * 0.5) / len(norm_jd)
    match_percentage = round(min(1.0, raw) * 100, 1)''', "Core of the skill matcher (abridged from skill_ontology.py)")
    r.p("The result of the matcher feeds the skill-gap analyser, which groups the skills by category and computes a coverage percentage for each category with the same credit rule (1.0 for a match, 0.5 for a partial match). The category scores are displayed in the dossier of a candidate, so that the recruiter can see, for instance, that a candidate is strong in programming languages but weak in cloud and DevOps.")

    # ------------------------------------------------------------------ Module 4
    r.h3("Module 4: Hybrid Ranker")
    r.p("The hybrid ranker computes seven scores in the range 0 to 100 and combines them as a weighted sum. If a user supplies custom weights, they are renormalised so that their sum is one.")
    r.eq(r"S=\frac{\sum_{i=1}^{7} w_i\,s_i}{\sum_{i=1}^{7} w_i},\qquad w=(0.35,\;0.20,\;0.15,\;0.10,\;0.10,\;0.05,\;0.05)")
    r.where([("s~1~", "technical skill score S~tech~ (the partial-credit match percentage, w = 0.35);"), ("s~2~", "semantic job-description score S~sem~ (w = 0.20);"), ("s~3~", "experience score S~exp~ (w = 0.15);"), ("s~4~", "education score S~edu~ (w = 0.10);"), ("s~5~", "project score S~proj~ (w = 0.10);"), ("s~6~", "certification score S~cert~ (w = 0.05);"), ("s~7~", "resume quality score S~ats~ (w = 0.05).")])
    r.p("**Semantic score.** When the dense model is available, the score is the cosine similarity of the embeddings of the resume and the job description, multiplied by 100 and limited to the range 0 to 100. When it is not available, the TF-IDF cosine similarity is used, with unigrams and bigrams, English stop words and at most 3000 features. TF-IDF cosine values of two documents usually lie between 0.3 and 0.7, so the value is multiplied by 150 to bring it to a comparable scale:", indent=False)
    r.eq(r"S_{\mathrm{sem}}=\min\bigl(100,\;\max(0,\;100\cdot\cos_{\mathrm{dense}})\bigr)\quad\text{or}\quad S_{\mathrm{sem}}=\min\bigl(100,\;150\cdot\cos_{\mathrm{tfidf}}\bigr)")
    r.p("**Experience score.** The score compares the years of experience y with the minimum y~min~ of the job. When the minimum is met, the score is 85 plus 5 points for every surplus year, up to 15 points; otherwise it is proportional to the shortfall, with a floor of 25. If the job states no minimum, a fixed value is used:", indent=False)
    r.eq(r"S_{\mathrm{exp}}=\begin{cases}\min\bigl(100,\;85+5\,(y-y_{\min})\bigr), & y\ge y_{\min}>0\\ \max\bigl(25,\;80\,y/y_{\min}\bigr), & 0<y<y_{\min}\\ 90\text{ if }y>0\text{, otherwise }80, & y_{\min}=0\end{cases}")
    r.p("**Education score.** A base score is assigned from the highest parsed degree and is increased by a bonus for a related branch and for a high CGPA, with the sum limited to 100 (Table 6.1).", indent=False)
    r.table(["Item", "Condition", "Points"], [
        ["Base score", "Ph.D.", "100"],
        ["", "Master's degree (M.E., M.Tech, M.S.)", "95"],
        ["", "Bachelor's degree (B.E., B.Tech)", "88"],
        ["", "BCA or MCA", "85"],
        ["", "Secondary school", "45"],
        ["", "Other or unrecognised", "75"],
        ["Bonus", "Related branch (computer, information, AI, data science, electronics)", "+5"],
        ["", "CGPA of 8.5 or more (or 85 percent or more)", "+7"],
        ["", "CGPA of 7.5 or more (or 75 percent or more)", "+3"],
    ], "Education Score Components", [1.2, 4.0, 1.0], size=10.5, align=["left", "left", "center"])
    r.p("**Project and certification scores.** The project score rewards the number of projects, with up to 60 points, and the share of the required skills that are used in the projects, with up to 40 points. A candidate without projects receives 40. The certification score depends on the number of certifications and is 40 when there is none:", indent=False)
    r.eq(r"S_{\mathrm{proj}}=\min\Bigl(100,\;\max\bigl(20,\;\min(60,\,30+15\,n_p)+40\,a\bigr)\Bigr),\qquad S_{\mathrm{cert}}=\min(100,\;60+15\,n_c)")
    r.where([("n~p~", "number of projects;"), ("a", "share of the required skills that appear in the skills used by the projects;"), ("n~c~", "number of certifications.")])
    r.p("Certifications are counted and not validated against an issuer, which is a limitation. The implementation of the weighted sum is shown in Listing 6.2.")
    r.code('''w = self.weights
total_weight = sum(w.values())
norm_w = {k: v / total_weight for k, v in w.items()}

overall_score = (
    skill_score    * norm_w["technical_skills"] +
    semantic_score * norm_w["semantic_jd"] +
    exp_score      * norm_w["experience"] +
    edu_score      * norm_w["education"] +
    proj_score     * norm_w["projects"] +
    cert_score     * norm_w["certifications"] +
    quality_score  * norm_w["resume_quality"]
)
overall_score = round(max(0.0, min(100.0, overall_score)), 1)''', "Weighted sum of the seven scores (hybrid_ranker.py)")

    # ------------------------------------------------------------------ Module 5
    r.h3("Module 5: Resume Quality and ATS Analyser")
    r.p("The quality analyser measures how well a resume can be read by an automated system and how convincing its content is. It returns a score from 10 to 100, a rating (Excellent for 85 or more, Good for 70 or more, Fair for 50 or more, otherwise Needs Work), lists of good points and improvements, and personalised suggestions. The score is the sum of the components of Table 6.2, from which up to 10 points are deducted for impossible or non-chronological date ranges.")
    r.table(["Component", "Maximum", "How points are given"], [
        ["Contact hygiene", "20", "E-mail 6, telephone 6, LinkedIn link 4, GitHub or portfolio link 4"],
        ["Section structure", "25", "Skills 7, education 6, projects 6, experience 6 (4 for a fresher)"],
        ["Action verbs", "20", "20 for five or more verbs such as built, deployed or optimised; 12 for two to four; otherwise 5"],
        ["Quantified impact", "20", "20 for four or more measurable results (percentages, users, latency); 12 for one to three; otherwise 4"],
        ["Length and readability", "15", "15 for 200 to 800 words; 8 if longer; 6 if shorter"],
        ["Date integrity", "-10", "5 points deducted for every inverted or impossible date range, at most 10"],
    ], "Components of the Resume Quality Score", [1.5, 0.8, 4.0], size=10, align=["left", "center", "left"])

    # ------------------------------------------------------------------ Module 6
    r.h3("Module 6: Explainable-AI Module")
    r.p("The explanation module turns the numbers of the ranker into a statement that a recruiter can read. It assigns one of four recommendation tiers by the overall score: *Strongly Recommended* for 80 or more, *Recommended* for 65 or more, *HR Review* for 50 or more and *Not Recommended* below 50. It then lists the reasons (for example, the number of required skills matched and the coverage percentage, the years of experience against the requirement, the number of projects), the strengths (for instance, strong competency in the primary skills when coverage is 75 percent or more), the warnings (for instance, missing required skills or an experience shortfall) and an executive summary. Partially matched skills are explained by naming the related skill of the candidate.")

    # ------------------------------------------------------------------ Module 7
    r.h3("Module 7: Blind-Screening Filter")
    r.p("The blind-screening filter creates an anonymised copy of a profile. The name is replaced by a neutral identifier of the form *Candidate #001*; the e-mail address, the telephone number, the location and the profile links are replaced by masks; every occurrence of the real name in the text is replaced by the identifier; and gendered pronouns and honorifics are neutralised (for example *he* and *she* become *they*, and *Mr.* and *Ms.* are removed). The council receives only this copy, so the removal takes place at the data layer before any score is computed. Direct identifiers are removed; proxy variables such as the name of an institution are not removed but are reported by the auditor. Listing 6.3 shows the core of the filter.")
    r.code('''blind = copy.deepcopy(candidate_data)
masked_id = f"Candidate #{candidate_index:03d}"
blind["candidate_name"] = masked_id
blind["email"] = "████@candidate.id"
blind["phone"] = "+██ ████"
blind["location"] = "Location Redacted (Fair Hiring)"
raw_text = re.sub(re.escape(real_name), masked_id, raw_text, flags=re.IGNORECASE)
for pattern, replacement in GENDER_PRONOUNS:      # he/she -> they, mr/ms -> ''
    raw_text = re.sub(pattern, replacement, raw_text, flags=re.IGNORECASE)''', "Core of the blind-screening filter (abridged from bias_filter.py)")

    # ------------------------------------------------------------------ Module 8
    r.h3("Module 8: Four-Agent Council")
    r.p("The council is the decision module of the system. A common feature builder first reads the candidate profile and the job description and computes the quantities on which all agents rely: the evidence-weighted coverage c~ev~ of Equation 3.10, the unevidenced-skill ratio, a month-aware timeline of roles, the number of quantified results, and the number of architecture, craftsmanship, scope and deployment terms. A resume skill counts as evidenced when its alias occurs in the text after the skills block has been removed.")
    r.p("**Tech Lead agent.** The agent estimates technical depth as a weighted sum of six normalised signals:", indent=False)
    r.eq(r"a_{\mathrm{tech}}=100\,\bigl(0.40\,c_{\mathrm{ev}}+0.20\,d+0.10\,k+0.10\,i+0.10\,m+0.10\,b\bigr)")
    r.where([("c~ev~", "evidence-weighted required-skill coverage (0.65 if the job has no parsed skills);"), ("d", "architecture depth, min(1, n~arch~/6);"), ("k", "craftsmanship, min(1, n~craft~/4);"), ("i", "quantified impact, min(1, n~impact~/3);"), ("m", "repository maturity, 0.5 min(1, n~rich~/3) + 0.5 min(1, n~shipped~/2), where n~rich~ counts projects with a description of at least 80 characters and n~shipped~ counts projects that mention deployment; when a GitHub report exists, m is replaced by 0.7 m + 0.3 g/100 with g the authenticity score;"), ("b", "breadth of tools, min(1, n~skills~/12).")])
    r.p("The agent also raises concerns, for example when more than 25 skills are listed (keyword stuffing) or when 60 percent or more of the listed skills have no supporting evidence.")
    r.p("**Culture and Retention agent.** The agent looks at the career timeline. It starts from 68 points and applies the adjustments of Table 6.3. Employment gaps are reported but never lower the score, because gaps have many legitimate causes. If no dated full-time role is found, the score is a neutral 62 with low confidence, and if only one full-time role exists, the score is capped at 78 because progression cannot be assessed.", indent=False)
    r.table(["Signal", "Adjustment"], [
        ["Average tenure of 30 months or more", "+14"],
        ["Average tenure of 18 to 29 months", "+8"],
        ["Average tenure below 12 months", "-12"],
        ["Each completed role shorter than 10 months", "-8 (at most -24)"],
        ["Each step up in title", "+9 (at most +18)"],
        ["Each move to a lower title band", "-4"],
        ["Current role of 24 months or more", "+4"],
        ["No title progression over four or more years with two or more roles", "-3"],
    ], "Adjustments of the Culture and Retention Agent", [4.5, 1.8], size=10.5, align=["left", "center"])
    r.p("**Fair-Hiring Auditor.** The auditor first scans the text written by the other agents for biased language and records a flag with a severity for every match. It then computes a merit-only score from job-related evidence, which has three parts:", indent=False)
    r.eq(r"a_{\mathrm{merit}}=50\,\bigl(0.8\,c_{\mathrm{ev}}+0.2\,c_{\mathrm{pref}}\bigr)+25\,\min\!\Bigl(1,\tfrac{y}{y_{\min}}\Bigr)+25\,\bigl(0.5\,\min(1,\tfrac{n_{\mathrm{impact}}}{3})+0.5\,\min(1,\tfrac{n_{\mathrm{proj}}}{3})\bigr)")
    r.where([("c~pref~", "coverage of the preferred skills;"), ("y, y~min~", "years of experience of the candidate and minimum required;"), ("n~impact~", "number of quantified results;"), ("n~proj~", "number of projects with a description of at least 60 characters.")])
    r.p("If the mean score of the Tech Lead and the Culture agent differs from the merit score by more than 18 points, a *merit divergence* flag is raised, because a gap of this size suggests that non-merit factors may be influencing the subjective scores. The integrity of the evaluation is then rated:", indent=False)
    r.eq(r"I=\max\bigl(0,\;100-\sum_{f}\pi(f)\bigr),\qquad \pi(\text{high})=25,\;\pi(\text{medium})=12,\;\pi(\text{low})=5")
    r.p("An agent that was flagged with high or medium severity is called *neutralised*, and its weight in the consensus is halved. Protected attributes that are visible in the resume (for example date of birth or marital status) are reported, with advice to redact them, but are never used in scoring.")
    r.p("**Seniority and Compensation agent.** The agent estimates a level from L3 to L6 from the full-time experience: below 2 years is L3, below 5 years is L4, below 9 years is L5, and 9 years or more is L6. The level is raised by one band when there are at least four scope signals (for example *led*, *architected*, *mentored*) and a lead-level title, lowered by one band when the tenure is long but the ownership signals are weak, and capped at L5 unless both org-level scope and a lead or staff title are present. The target level of the job is derived from its title (principal or staff is L6, senior or lead is L5, junior or associate is L3) or from the required years. The level-fit score depends on the difference d between the estimated level and the target level:", indent=False)
    r.eq(r"a_{\mathrm{level}}=f(d),\qquad f(0)=100,\;f(+1)=82,\;f(+2)=60,\;f(+3)=40,\;f(-1)=70,\;f(-2)=42,\;f(-3)=20")
    r.p("An indicative compensation band is attached to every level (for example L4 has 120,000 to 175,000 US dollars and 14 to 28 lakh rupees per annum). The suggested position in the band is p = 0.25 + 0.45 c + 0.30 min(1, n~scope~/6), limited to the range 0 to 1, where c is the skill coverage. The bands are indicative planning values and must be calibrated before any offer is made.")
    r.p("**Cross-examination and consensus.** After the scorecards, the agents cross-examine each other in a deterministic transcript that is generated from the data and is shown in the interface as a replayable debate. The executive consensus is the weighted sum of the four scores:", indent=False)
    r.eq(r"C=0.35\,a_{\mathrm{tech}}+0.25\,a_{\mathrm{merit}}+0.20\,a_{\mathrm{culture}}+0.20\,a_{\mathrm{level}}")
    r.p("with the weights of neutralised agents halved and renormalised. The consensus is mapped to a verdict: STRONG_HIRE for C of 80 or more, HIRE for 68 or more, LEAN_HIRE for 55 or more, and REJECT otherwise. Knock-out gates are then applied, because a high average must not hide a fatal flaw. They are shown in Figure 6.1 and in Listing 6.4.", indent=False, keep=True)
    r.fig(os.path.join(FIG, "fig_6_1_gating.png"), "Verdict thresholds and knock-out gates of the council.", 13.0)
    r.code('''# Knock-out gates on required skills (least subjective part of the decision)
if f.required:
    if f.evid_coverage < 0.25:
        verdict = Verdict.REJECT
    elif f.evid_coverage < 0.5 and verdict in (Verdict.STRONG_HIRE, Verdict.HIRE):
        verdict = Verdict.LEAN_HIRE
red_flags = self._red_flags(f, tech, culture, audit, seniority)
high = [x for x in red_flags if x["severity"] == "high"]
if len(high) >= 2 and verdict != Verdict.REJECT:
    verdict = Verdict.REJECT
elif len(high) == 1 and verdict in (Verdict.STRONG_HIRE, Verdict.HIRE):
    verdict = Verdict.LEAN_HIRE
if f.inverted_dates and verdict in (Verdict.STRONG_HIRE, Verdict.HIRE):
    verdict = Verdict.LEAN_HIRE
if not f.has_education and verdict in (Verdict.STRONG_HIRE, Verdict.HIRE):
    verdict = Verdict.LEAN_HIRE''', "Knock-out gates applied to the verdict (abridged from agentic_council.py)")
    r.p("Nine red-flag codes, each with a severity and a detail text, make the risks individually explainable (Table 6.4).", keep=True)
    r.table(["Red-flag code", "Severity", "Raised when"], [
        ["EXPERIENCE_DEFICIT", "medium / high", "years of experience are below 60 percent (medium) or 35 percent (high) of the minimum"],
        ["UNVERIFIED_SKILL_CLAIMS", "high / medium", "60 percent or more of 10 or more listed skills are never used in experience or projects, or hype skills are listed without evidence"],
        ["SKILL_STUFFING", "medium", "25 or more skills are listed"],
        ["NO_QUANTIFIED_IMPACT", "medium", "one year or more of experience and no measurable result"],
        ["DATE_INCONSISTENCY", "medium", "a date range ends before it starts or lies in the future"],
        ["CONCURRENT_EMPLOYMENT_CONFLICT", "high", "two full-time on-site roles overlap by six months or more in different countries"],
        ["MISSING_EDUCATION", "medium", "no academic credential is found"],
        ["REQUIRED_SKILLS_MISSING", "medium", "coverage is below 50 percent or four or more required skills are missing"],
        ["LEVEL_MISMATCH", "medium", "the estimated level differs from the target level by two or more levels"],
    ], "Red-Flag Codes of the Council", [2.4, 1.0, 3.8], size=9.5, align=["left", "center", "left"])
    r.p("The overlap used by the concurrency rule is measured in months on the month index:", indent=False)
    r.eq(r"o_{ij}=\max\bigl(0,\;\min(e_i,e_j)-\max(s_i,s_j)\bigr),\qquad o_{ij}\ge 6\ \text{months and different countries}\ \Rightarrow\ \text{high-severity flag}")
    r.p("Finally, the council reports its own uncertainty. The confidence starts from 100 and is reduced by 1.2 times the standard deviation of the four agent scores, and by fixed penalties for missing information:", indent=False)
    r.eq(r"\text{conf}=\min\bigl(99,\;\max(20,\;100-1.2\,\sigma-\textstyle\sum\text{penalties})\bigr)")
    r.p("The penalties are 8 for a missing timeline, 15 for no parsed skills, 15 for inverted dates, 10 for missing education, 20 for a concurrent-employment conflict, 10 for fewer than 150 words and 5 for a job without parsed required skills. An agent whose score differs from the consensus by more than 20 points is reported as dissenting. A human review is requested when the auditor raises a high-severity flag, when the integrity score is below 70, when the confidence is below 55, or when the consensus lies within 2 points of a verdict boundary. The council is therefore a decision-support device and not an autonomous decision-maker.")

    # ------------------------------------------------------------------ Module 9
    r.h3("Module 9: GitHub Authenticity Inspector")
    r.p("The inspector validates the programming languages that a resume claims against the public GitHub footprint of the candidate. It finds the handle in the parsed data or in patterns such as *github.com/user* in the text, and queries the public REST interface (user, repositories, languages per repository and public events) with the standard library only. A token is used when it is configured, and rate limits are handled: a short wait is honoured, and a longer limit returns a structured *rate limited* report instead of raising an error. Results are cached for 15 minutes. Forked repositories are excluded from the language evidence because forked code is not authored work. Each claimed language is classified as verified, weak or unverified, and the authenticity score combines the language, activity and repository-substance scores:")
    r.eq(r"A=0.55\,s_{\mathrm{lang}}+0.25\,s_{\mathrm{act}}+0.20\,s_{\mathrm{sub}},\qquad s_{\mathrm{sub}}=0.25\,s_{\mathrm{stars}}+0.10\,s_{\mathrm{forks}}+0.30\,s_{\mathrm{mat}}+0.15\,s_{\mathrm{orig}}+0.20\,s_{\mathrm{age}}")
    r.p("If no language is claimed, the score is (0.25 s~act~ + 0.20 s~sub~)/0.45. When there is nothing public to judge, the verdict is *insufficient public data* and no score is given, because the absence of a public profile is not evidence of dishonesty. The report is used by the Tech Lead agent as additional evidence of repository maturity. The idea of using repository evidence is related to earlier work that matched developer profiles with job advertisements [@hauff], but here it audits resume claims.")

    # ------------------------------------------------------------------ Module 10
    r.h3("Module 10: Hybrid Talent Search")
    r.p("The talent search answers natural-language questions about the resume pool, for example *Engineers with 2+ years in Python and PyTorch*. Every resume is divided into chunks tagged with their section (skills, experience, projects, summary, education or certifications). A query plan extracts the experience requirement and the competencies of the query and expands the concepts with synonyms. Each chunk is scored by the fusion of Equation 3.7 with alpha = 0.55 and with BM25 parameters k~1~ = 1.5 and b = 0.75. The sparse index uses an inverted index, and the BM25 score is scaled by a fraction of its theoretical maximum so that it lies between 0 and 1. The fused chunk score is multiplied by a section factor (1.0 for skills, experience and projects, 0.85 for the summary and 0.7 for education). The candidate-level scores are:")
    r.eq(r"\mathrm{sem}=0.6\,h_{\mathrm{best}}+0.4\,h_{\mathrm{top3}},\qquad \mathrm{rel}=\bigl(0.40\,\mathrm{sem}+0.60\,\mathrm{cov}\bigr)\bigl(0.65+0.35\,\min(1,\,y/y_q)\bigr)")
    r.where([("h~best~, h~top3~", "the best fused chunk score of the candidate and the mean of its best three chunk scores;"), ("cov", "competency coverage, the weighted sum of the strength of the evidence found for each competency divided by the total weight (a competency proved in experience or projects has strength 1.0, in the skills list 0.7, and by related terms only 0.25 to 0.45);"), ("y, y~q~", "years of experience of the candidate and the experience required by the query.")])
    r.p("Every result carries matched, partial and missing competencies with the section that proves each one, and highlighted evidence snippets. The index is cached by a content fingerprint, so repeated queries on the same pool are fast.")

    # ------------------------------------------------------------------ Module 11
    r.h3("Module 11: Interview-Question Generator")
    r.p("The interview generator prepares a questionnaire for the panel from the profile of the candidate. It draws technical questions from a knowledge bank of skill-specific questions for the matched skills; project-specific questions from the technologies used in the projects of the candidate; probing questions for the missing skills (for instance, how quickly the candidate could learn the skill); questions suited to the level of experience (fresher or experienced); and behavioural questions. Every question has a difficulty (easy, medium or hard) and a statement of what the interviewer should look for in the answer. The questions of the council about gaps and red flags are appended as interview focus points.")
    r.p("The web dashboard contains its own version of the generator, which builds a larger kit for the selected candidate. The kit starts with the verification question that is stored with the candidate and a follow-up on the same evidence. It adds an architecture question and, for the role family of the candidate (machine learning, DevOps and reliability, data platform, backend, full-stack, business intelligence or AI safety), two system-design questions, a hands-on debugging exercise and two questions on quality and security. Up to three deep-dive questions are chosen for the matched skills from a bank of about thirty-five skills, with a generic template for the other skills, and a gap question or a mastery question follows, depending on whether skills are missing. Further questions are generated from the audit findings of this candidate: the red flags (an experience deficit, unverified or stuffed skills, missing quantified impact, inconsistent dates, missing required skills), a medium or high GitHub risk and a low ATS score. The kit ends with incident forensics, three behavioural questions and one leadership question, which are chosen from a rotating bank by a hash of the candidate identifier so that the kit is stable for a candidate but differs between candidates, and two questions on motivation and logistics. On the 162 candidates of the three pools the kit contains between 19 and 24 questions, 20.7 on average, compared with the single stored question per candidate before. The page offers filter chips by category and a button that copies the whole kit.")

    # ------------------------------------------------------------------ Module 12
    r.h3("Module 12: Recruiter Chatbot")
    r.p("The recruiter chatbot lets the recruiter ask questions about the screened pool in words. It supports prompts such as the number of candidates, which candidates have the required skills, who has red flags and why, a comparison of two named candidates, an outreach e-mail for a named candidate and the compensation band. The answers are composed from retrieved and scored evidence (the leaderboard, the council output and the talent-search results) and not from free text generation, in line with the principle of retrieval-grounded generation [@rag]. In the default configuration the text of the answers is template-based and needs no language model. The conversation can be exported as a Markdown report.")
    r.p("The web dashboard contains its own chatbot engine, which answers only from the loaded pool and the active role and keeps the context of the conversation. Intents are recognised with whole-word patterns that are tried in a fixed order of specificity, so that a question about salary is not mistaken for a request for the top candidates. The engine understands questions about a single candidate (profile, the reason for the verdict, whether to hire, skills, GitHub, salary and interview questions), comparisons, filters by verdict, years of experience, skill, flag type and category, rankings and shortlists, the role and the compensation band, the meaning of the scores, and three kinds of e-mail draft (outreach, interview invitation and decline). Every answer carries a small context record with the intent, the candidates discussed and the list that was shown, and the earlier messages are passed back with the next question. This lets the engine resolve pronouns, the first, second or third item of the last list, and the instruction *show more*. Lists are shown five at a time, and asking for the same list again moves on to the next page. A name that belongs to two candidates, as in the 100-resume pool, is answered with a question that shows the rank numbers, and the wording varies deterministically so that the same question does not always receive the same sentence. Clickable follow-up questions are offered below the last answer. Candidates with missing fields, such as uploaded resumes, are shown with *n/a* instead of an error.")

    # ------------------------------------------------------------------ Module 13
    r.h3("Module 13: REST API and Persistence")
    r.p("The FastAPI application of version 4.0.0 creates the database tables at start-up, adds a processing-time header to every response and configures cross-origin access from the list of allowed origins. The routers for jobs, resumes, screenings and audits delegate to service classes. The resume service computes the SHA-256 hash of an uploaded file and returns the stored resume if the hash is already known, so a duplicate is never stored twice. The screening service loads the job and the selected resumes, applies the blind-screening filter when requested, scores every candidate with the hybrid ranker and the quality analyser, produces the explanation, ranks the candidates, stores the session and its results, and writes an audit-log entry. A later request records the decision of the recruiter on a result together with a time stamp. The relational database is SQLite when no other URL is configured (a PostgreSQL URL is also supported), and the schema is created by an Alembic migration; on the deployed host the relational routes use a temporary SQLite file.")
    r.p("The same application contains the account service of the deployed system. Its routers for authentication and candidates use a MongoDB database through PyMongo. The service hashes passwords with PBKDF2-HMAC-SHA256 (210,000 iterations and a random 16-byte salt) and compares the digests in constant time. For an unknown e-mail address it still performs a hash computation, so that the response time does not reveal which addresses are registered, and it returns the same message for an unknown address and for a wrong password. A counter of failed sign-ins locks the account for 15 minutes after five failures. A successful sign-in creates a random 32-byte token; only the SHA-256 digest of the token is stored in the sessions collection, together with an expiry time that a time-to-live index uses to delete sessions after seven days. Sign-in with Google sends the ID token to the endpoint /auth/google, which asks Google to validate it and then checks the audience, the issuer, the expiry, the verified-e-mail claim and the gmail.com domain before the user is created or linked. The candidate endpoint returns a pool from the candidates collection, and the start-up routine fills empty pools from the bundled seed files.")

    # ------------------------------------------------------------------ Module 14
    r.h3("Module 14: Web Dashboard")
    r.p("The web dashboard is a single-page React 19 application built with Vite and styled with Tailwind CSS. After a sign-in, the recruiter sees the three-step workspace and, after the screening, the seven pages of the navigation. The sign-in card supports e-mail and password accounts, which are stored in the stand-alone configuration as per-user salted PBKDF2-HMAC-SHA256 digests with 200,000 iterations in the browser and are created and checked by the API in the connected configuration, and an optional Google button that is restricted to Gmail accounts and verified by the API. The credential fields block copy, cut and paste but accept the autofill and the strong-password suggestion of a password manager, they are not pre-filled after a logout, and the application asks Google to forget the previously selected account at sign-out. The application extracts text from PDF and DOCX files in the browser and ships a browser-side scorer and a bundled set of sample candidates, so that it runs fully offline; with environment variables it can instead call the API. The Streamlit application provides the same pages for local use. The dashboard is deployed on Vercel, the API on Render and the data in MongoDB Atlas, and the deployed site uses the connected configuration. The logic of the interview generator and of the chatbot is covered by 29 tests, which run with the Node.js test runner on all 162 candidates.")

    r.h1("6.3", "Difficulties Encountered and Strategies Used to Tackle Them")
    r.p("During the development of the system, several technical considerations affected the design. They are described below with the strategy that was adopted.")
    r.h3("Dates that defeat text similarity")
    r.p("A stress test with adversarial resumes showed that an inverted date range, such as *Jul 2026 to Jan 2024*, and two overlapping full-time jobs in different countries were not detected by the first version of the pipeline, because similarity scoring treats a date as an ordinary token. The inverted-date resume was scored on a shorter history and still received a hire verdict, and the concurrent-employment resume received a strong-hire verdict without any flag.")
    r.p("**Strategy:** the parser was extended with month-aware timeline parsing, and the council received explicit gates for inverted dates, concurrent full-time employment and missing education. The gates cap the verdict instead of changing the weighted average, so a high mean cannot hide a fatal flaw. The probe is a regression case study and not a held-out detection rate.")
    r.h3("Keyword stuffing")
    r.p("A resume that lists many fashionable tools without any evidence obtained the same keyword score as a genuine candidate with four years of experience (47.1 percent in both cases).")
    r.p("**Strategy:** evidence-weighted coverage (Equation 3.10) was introduced, together with an unevidenced-skill ratio and the red flags *UNVERIFIED_SKILL_CLAIMS* and *SKILL_STUFFING*. The ablation of Chapter 8 shows that this mechanism changes two verdicts.")
    r.h3("Optional dependencies and offline operation")
    r.p("Dense embeddings, language-model narratives and the GitHub service all need libraries, model files or a network connection that may not be present on a demonstration machine or on a free hosting tier.")
    r.p("**Strategy:** every optional component has a deterministic local fallback (TF-IDF for embeddings, rule-based text for the narrative, a structured report for GitHub failures), and the interface reports which backend is active. The lean requirements file of the API omits the dense model, so the service fits in 512 MB of memory.")
    r.h3("Rate limits and unreliable external services")
    r.p("The public GitHub interface limits the number of requests, and events are only available for the last 90 days.")
    r.p("**Strategy:** the inspector honours short waits, returns structured rate-limited or partial reports, caches responses for 15 minutes, excludes forks, and reports insufficient data instead of a guessed score. Its behaviour was verified with a simulated transport in the automated tests.")
    r.h3("Bias that is hidden inside optional components")
    r.p("The deterministic components do not use the name of the candidate, so the name-swap test shows no change. This does not prove that dense embeddings or a language model would be invariant, because audits show bias exactly in those components [@wilson,@armstrong].")
    r.p("**Strategy:** blind screening removes identifiers at the data layer before any optional component sees the text, and an auditor agent scans the text of other agents for biased language. Testing with dense embeddings and a language model remains future work.")
    r.h3("Calibration of verdicts")
    r.p("On a 100-resume synthetic benchmark the council never issued a strong-hire verdict and rejected only 11 of 35 reject profiles, which shows that the thresholds are conservative at the top and permissive at the bottom.")
    r.p("**Strategy:** the limitation is reported openly, and the decisions are routed to human review when the consensus is close to a threshold. Recalibration against recruiter decisions is listed as a necessary step before operational use.")
    r.h3("Deployment constraints")
    r.p("A free API service sleeps after a period of inactivity (the first request then takes up to about 50 seconds), the free MongoDB Atlas tier offers 512 MB and has to accept connections from any address because the host has no fixed address, and the Streamlit hosting resets its local database when it restarts. The relational routes of the API use a temporary SQLite file on the deployed host, so only the accounts, the sessions and the candidate pools are persistent.")
    r.p("**Strategy:** the documentation states these constraints, the API reads its configuration from environment variables, and the web interface can run without the API in its stand-alone mode. The database password is kept only in the environment of the host, and the responses of the account endpoints do not reveal whether an address is registered.")
    r.h3("Account security")
    r.p("A public sign-in form can be attacked by guessing passwords, by finding out which e-mail addresses are registered, and by stealing a copy of the database. A first version of the web interface kept the accounts in the browser only, which cannot protect against any of these.")
    r.p("**Strategy:** the accounts were moved to the server. Passwords are hashed with a salt and 210,000 PBKDF2 iterations, a wrong password and an unknown address give the same answer, five failures lock the account for 15 minutes, and sessions are random tokens of which only the digest is stored and which expire after seven days. Sign-in with Google is verified on the server instead of being trusted from the browser. The behaviour is checked by 18 automated tests.")
    r.h3("Duplicate candidate names")
    r.p("In the 100-resume benchmark 50 names are used twice, for two different candidates with different roles. A chatbot that looks a candidate up by name would silently answer for the wrong person, or compare a candidate with himself or herself.")
    r.p("**Strategy:** the chatbot groups the candidates that share a name, asks which one is meant, shows the rank numbers and the roles, and accepts a rank number or an expression such as *the first one* as the answer.")

    r.h3("Pseudocode of the Screening Pipeline")
    r.code('''FUNCTION screen(job_text_or_role, resumes, blind_mode):
    jd     <- JDParser.parse(job_text_or_role)         # required, preferred, min years
    cands  <- [ResumeParser.parse(file) for file in resumes]
    IF blind_mode: cands <- [BiasFilter.anonymize(c, i) for i, c in enumerate(cands)]
    FOR EACH c IN cands:
        quality <- ResumeQualityAnalyzer.analyze(c, jd.required_skills)
    ranked <- HybridRanker.rank_all(cands, jd, quality)      # 7 weighted scores
    FOR EACH item IN ranked:
        item.explanation <- ExplainableAI.generate(item, jd)  # reasons, strengths, warnings
        item.council     <- Council.evaluate(item.candidate, jd)
        # four scorecards -> debate -> consensus C -> thresholds -> gates -> flags
    SAVE session, results, audit log
    RETURN ranked WITH verdicts, red flags, confidence, review triggers''', "Pseudocode of the overall screening pipeline")
    r.p("The actual function calls differ slightly between the Streamlit application, the React interface and the API, but the sequence of operations is the one shown above. The behaviour of every module was confirmed by execution and testing, as described in Chapter 7.")

    r.h3("Summary")
    r.p("This chapter described the technologies and the implementation of the fourteen modules of the system, with their formulas and code excerpts. The resume parser and the ontology prepare the data, the hybrid ranker and the quality analyser score it, the blind-screening filter and the council make the decision fair and explainable, and the inspector, the search, the generator and the chatbot support the recruiter. The API and the dashboard expose the results. Finally, the difficulties and the strategies that were adopted were discussed.", indent=False)

"""Chapter 8: Results"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "fig")
SHOT = os.path.join(HERE, "shots")
PROJ = r"C:\DEV\Projects\Experiments\ai_recruitment_system"
RES = json.load(open(PROJ + r"\paper_results.json"))
ROWS = RES["rows"]

LABEL = {
    "Test_Case_1_Gold_Standard_Pass.txt": ("TC1", "Gold standard"),
    "Rahul_Nair_ML_Engineer.pdf": ("RN", "Rahul Nair (ML engineer)"),
    "Test_Case_3_Lateral_Partial_Match.txt": ("TC3", "Lateral partial match"),
    "Sneha_Kulkarni_Fullstack_Dev.txt": ("SK", "Sneha Kulkarni (full-stack)"),
    "Vikram_Singh_Cloud_DevOps.docx": ("VS", "Vikram Singh (DevOps)"),
    "Kavita_Mehta_Buzzword_Flawed.txt": ("KM", "Kavita Mehta (buzzwords)"),
    "Aarav_Sharma_Backend_Dev.docx": ("AS", "Aarav Sharma (backend)"),
    "Ananya_Roy_Fresher_Engineer.pdf": ("AR", "Ananya Roy (fresher)"),
    "Priya_Patel_Data_Analyst.pdf": ("PP", "Priya Patel (analyst)"),
    "Test_Case_2_Buzzword_Exaggeration_Fail.txt": ("TC2", "Buzzword fail"),
    "Test_Case_4_Corrupt_ATS_Format_Error.txt": ("TC4", "Corrupt format"),
    "Edge_Case_Missing_Sections.txt": ("EC", "Edge: missing sections"),
}


def build(r):
    r.chapter("Results")
    r.p("This chapter presents the execution and the results of the implemented system. The first part shows screenshots of the running web interface that were captured from the real application with the demonstration pool of twelve resumes loaded. The second part reports the experiments that were run to answer five research questions about the system: whether evidence-weighted screening separates genuine from keyword-stuffed candidates better than a keyword baseline (RQ1), whether the scores are invariant to the name of the candidate (RQ2), whether the conclusions are robust to the chosen weights (RQ3), what a screening costs (RQ4), and whether temporal and structural anomalies are intercepted by explicit gates (RQ5). All resumes used in the experiments are synthetic.")

    r.h1("8.1", "SNAPSHOTS")
    r.p("This section presents screenshots that illustrate the functions of the web interface. The screenshots were captured from the running application and are not mock-ups.")

    r.h2("8.1.1", "Workspace and Candidate Intake")
    r.p("After signing in, the recruiter selects the role and loads the candidates. Figure 8.1 shows the second step of the workspace after the 12-resume core suite has been loaded: the pool size is shown at the top right, the recruiter can upload their own PDF, DOCX or TXT files (up to 100 in the browser) or load one of the benchmark pools, and the screening engine is started with a single action. In the deployed configuration the benchmark pools are fetched from the candidates collection of the database. The scores of these pools were computed beforehand by the Python pipeline, so the staged progress messages of the interface only illustrate the stages; only resumes uploaded by the recruiter are parsed and scored in the browser.")
    r.fig(os.path.join(SHOT, "jobs_intake.jpg"), "Candidate intake with the core suite of twelve resumes loaded.", 14.0, frame=True)

    r.h2("8.1.2", "Screening Leaderboard")
    r.p("The leaderboard is shown as soon as the screening has finished. Its header displays the telemetry of the run: the number of candidates screened (12) with the average match of 52.2 percent, the top match of 88.1 percent, the model backend (TF-IDF with BM25, local council, local backend) and the active role with its 17 required skills. A natural-language search with prompt shortcuts is placed above the ranked cards. Figure 8.2 shows the top of the leaderboard.")
    r.fig(os.path.join(SHOT, "lb_top.jpg"), "Screening leaderboard: run telemetry, talent-pool search and the first candidate cards.", 14.0, frame=True)
    r.p("Each card contains the rank, the file name and the role of the candidate, the verdict, the match percentage with a score bar, a line of verified evidence from the resume, the matched skills (with a check mark), the partially matched skills (for instance *FastAPI via Flask: 0.5 credit*), the missing skills (with a cross), and the number of red flags. Figure 8.3 shows the cards of the lateral and the weaker candidates, where the flag *REQUIRED_SKILLS_MISSING* is raised.")
    r.fig(os.path.join(SHOT, "lb_cards.jpg"), "Leaderboard cards with evidence lines, skill chips and red-flag counts.", 14.0, frame=True)
    r.p("The cards can be switched to a compact table with the rank, the match, the ATS format score, the council consensus and the red flags, which is useful for a quick comparison of many candidates (Figure 8.4).")
    r.fig(os.path.join(SHOT, "lb_table.jpg"), "Compact table view of the leaderboard.", 14.0, frame=True)

    r.h2("8.1.3", "Candidate DeepDive and Council Dossier")
    r.p("The dossier of a candidate shows the hybrid score and the council consensus, the scorecards of the four agents with their weights (Tech Lead 35 percent, Culture and Retention 20 percent, Fair-Hiring Auditor 25 percent, and Seniority and Compensation 20 percent), the estimated level with the indicative compensation band, and the cross-examination debate, which can be replayed turn by turn. For the top candidate, the Tech Lead scores 89, Culture and Retention 78, the auditor 99 and the Seniority agent assigns level L5 (Figure 8.5).")
    r.fig(os.path.join(SHOT, "dd_top.jpg"), "Candidate dossier: scorecards of the four council agents and the debate.", 14.0, frame=True)

    r.h2("8.1.4", "Candidate Comparison")
    r.p("The comparison page puts two selected candidates side by side. For each dimension it shows the two values and the advantage: overall match, ATS readability, council consensus, GitHub authenticity and the salary range. In Figure 8.6 the first candidate leads the second by 5.8 percentage points.")
    r.fig(os.path.join(SHOT, "compare.jpg"), "Head-to-head comparison matrix of two candidates.", 14.0, frame=True)

    r.h2("8.1.5", "Interview Assistant")
    r.p("The interview assistant prepares a tailored questionnaire for the selected candidate. It combines the question stored with the candidate with questions generated from the role family, the matched skills, the detected gaps, the red flags and the GitHub risk of the candidate. The kit has between 19 and 24 questions for each of the 162 candidates of the three pools (20.7 on average), where the stored data held a single question. Every question has a coloured category badge (for instance Technical Verification, System Design, Red-Flag Verification or Behavioral and Collaboration) and a rubric that states what the interviewer should look for in the answer. Chips above the list filter the kit by category, with the number of questions in each category, and a button copies the whole kit as text (Figure 8.7).")
    r.fig(os.path.join(SHOT, "interview.jpg"), "Interview assistant: about twenty candidate-specific questions with category filters and evaluation rubrics.", 14.0, frame=True)

    r.h2("8.1.6", "Recruiter Analytics")
    r.p("The analytics page summarises the pool: the pool conversion rate (2 of 12 resumes are strong hires), the median score of 48.8 percent, the red-flag intercept rate of 58.3 percent (7 of 12 resumes are flagged), the ATS parse integrity of 91.7 percent, and the frequency of the required skills across the applicant pool (Python in 92 percent of the candidates, Docker in 50 percent, FastAPI in 42 percent, AWS in 33 percent and verified PyTorch in 17 percent), as shown in Figure 8.8.")
    r.fig(os.path.join(SHOT, "analytics.jpg"), "Recruiter analytics and cohort metrics.", 14.0, frame=True)

    r.h2("8.1.7", "Recruiter Chatbot")
    r.p("The recruiter chatbot answers questions in words from the screened pool. Figure 8.9 shows the answer to the question *Who has red flags and why?*: the audit summary lists each flagged candidate with the rank, the match, the verdict, the triggered flags, the finding of the Fair Auditor and the GitHub forensics.")
    r.fig(os.path.join(SHOT, "chat_flags.jpg"), "Recruiter chatbot answering a red-flag audit question.", 14.0, frame=True)
    r.p("The chatbot keeps the context of the conversation. After a question about a candidate, the follow-up *why?* explains the verdict with the council scorecards, *should I hire her?* gives a recommendation with the arguments for and against, and *interview questions for her* returns five questions from the kit. Long lists are shown five at a time and continue with *show more*, a name that belongs to two candidates is answered with a question that shows their rank numbers, and clickable follow-up questions appear below each answer (Figure 8.10). The whole conversation can be exported as a Markdown file.")
    r.fig(os.path.join(SHOT, "chat_followup.jpg"), "Recruiter chatbot answering follow-up questions about the candidate discussed last, with clickable suggestions.", 14.0, frame=True)

    r.h2("8.1.8", "Blind Screening")
    r.p("When the blind-screening switch in the top bar is turned on, the identities in the whole interface are replaced by neutral identifiers (*Candidate #001*, *Candidate #002*, and so on) and the cards show *identity hidden*. The scores, the verdicts and the ranking remain unchanged, which is the behaviour that the name-swap experiment of Section 8.2.5 verifies. Figure 8.11 shows the leaderboard with blind screening on.")
    r.fig(os.path.join(SHOT, "blind_top.jpg"), "Leaderboard with blind screening switched on: identities are hidden.", 14.0, frame=True)

    # ------------------------------------------------------------------ 8.2
    r.h1("8.2", "EXPERIMENTAL RESULTS")
    r.p("The evaluation has three parts. The **pilot study** uses twelve resumes and one job (Machine Learning Engineer, 17 required skills, minimum two years of experience): eight synthetic resumes that ship with the project plus four purpose-written test cases that probe specific behaviours. The **benchmark study** uses 100 synthetic resumes over the eight role families, generated with language-model assistance under four archetypes in fixed proportions: 20 strong hires, 45 lean hires, 25 buzzword exaggerators and 10 chronology or formatting anomalies (the last two form the 35 reject profiles). The **adversarial probe** runs the first 20 benchmark resumes with additional targeted anomalies through the earlier and the upgraded pipelines. All values were measured in the offline configuration (TF-IDF semantics, no language model) with Python 3.11.9 on a laptop CPU, in a single process. The baseline is a keyword score modelled on the Phase 1 ATS: the percentage of required skills whose name appears anywhere in the resume text.")

    r.h2("8.2.1", "Processing Latency (RQ4)")
    lat = RES["latency_ms_per_resume"]
    r.p(f"{r.ref_next_tab()} and {r.ref_next_fig()} report the cost of each stage on the 12-resume pool. A full screening takes {lat['total']:.2f} ms per candidate, which is about 33.8 candidates per second on a single CPU thread. Parsing dominates the cost with {100*lat['parse']/lat['total']:.0f} percent; the hybrid ranking is the cheapest stage. The timings depend on the hardware and exclude dense-embedding inference, which was not installed, and the rendering cost of the browser client. The cost grows linearly with the number of resumes.", keep=True)
    r.table(["Stage", "Latency (ms)", "Share (%)"], [
        ["Resume parsing", f"{lat['parse']:.2f}", f"{100*lat['parse']/lat['total']:.1f}"],
        ["Hybrid scoring and ranking", f"{lat['rank']:.2f}", f"{100*lat['rank']/lat['total']:.1f}"],
        ["Multi-agent consensus", f"{lat['council']:.2f}", f"{100*lat['council']/lat['total']:.1f}"],
        ["End-to-end", f"{lat['total']:.2f}", "100"],
    ], "Per-Resume Processing Latency (12-Resume Pool, TF-IDF, Single Thread)", [3.0, 1.4, 1.2], size=10.5, align=["left", "center", "center"])
    r.fig(os.path.join(FIG, "ch_latency.png"), "Per-stage processing time per resume.", 11.5)

    r.h2("8.2.2", "Ranking Divergence from the Keyword Baseline (RQ1)")
    # compute baseline ranks (stable, ties broken by proposed order)
    order = sorted(range(len(ROWS)), key=lambda i: (-ROWS[i]["baseline"], i))
    brank = {i: k + 1 for k, i in enumerate(order)}
    tab = []
    for i, x in enumerate(ROWS):
        short, name = LABEL[x["file"]]
        years = f"{x['years']:g}" + ("*" if x["file"].startswith("Test_Case_4") else "")
        ver = x["verdict"] + (" (human review)" if x["human_review"] else "")
        tab.append([str(x["rank"]), name, years, f"{x['baseline']:.1f} ({brank[i]})", f"{x['proposed']:.1f} ({x['rank']})", f"{x['council']:.1f}", ver])
    r.p(f"{r.ref_next_tab()} lists the twelve pilot results. The two rankings agree on the extremes, with a Kendall rank correlation of {RES['kendall_tau_baseline_vs_proposed']:.3f}, but they differ where the design intends ({r.ref_next_fig()}). The keyword baseline scores TC2, a resume with 0.3 years of experience and a long list of fashionable tools, at 47.1 percent, identical to TC3, a genuine four-year engineer, and ranks it fifth, whereas the proposed ranker places it tenth and separates TC2 from TC3 by 19.7 points (41.6 against 61.3). A value of 0.667 indicates substantial disagreement between the rankings; it does not by itself show which ranking is correct. The evidence for correctness here is the case analysis of Section 8.2.3, and with a single pool of twelve synthetic resumes the result shows a mechanism and not a statistical effect.", keep=True)
    r.table(["#", "Resume", "Years", "Baseline % (rank)", "Proposed % (rank)", "Council C", "Council verdict"], tab, "Results on the 12-Resume Pilot Pool", [0.35, 2.1, 0.65, 1.15, 1.15, 0.75, 1.7], size=9, align=["center", "left", "center", "center", "center", "center", "left"])
    r.p("* The parsed years of TC4 reflect its inconsistent dates.", indent=False, size=10, space_after=6)
    r.fig(os.path.join(FIG, "ch_baseline.png"), "Keyword baseline versus proposed hybrid score for the twelve pilot resumes.", 13.5)
    r.fig(os.path.join(FIG, "ch_components.png"), "Component scores of the four demonstration resumes.", 13.5)

    r.h2("8.2.3", "Evidence Mechanism")
    byname = {x["file"]: x for x in ROWS}
    ev = []
    for short, fn in (("TC1", "Test_Case_1_Gold_Standard_Pass.txt"), ("TC2", "Test_Case_2_Buzzword_Exaggeration_Fail.txt"), ("TC3", "Test_Case_3_Lateral_Partial_Match.txt"), ("TC4", "Test_Case_4_Corrupt_ATS_Format_Error.txt")):
        x = byname[fn]
        t = x["tech_metrics"]
        flags = ", ".join(f for f in x["flags"] if f != "REQUIRED_SKILLS_MISSING") or ("REQUIRED_SKILLS_MISSING" if x["flags"] else "none")
        ev.append([short, f"{t['required_skills_listed']} / {t['required_skills_evidenced']}", f"{t['required_skill_coverage']:.2f}", f"{t['unevidenced_skill_ratio']:.2f}", str(t["quantified_impacts"]), x["verdict"] + (" (human review)" if x["human_review"] else ""), flags.replace("_", " ").title() if flags != "none" else "None"])
    r.p(f"{r.ref_next_tab()} shows why. TC2 lists 8 required skills but evidences only 1, which gives an unevidenced ratio of 0.90 and an evidence-weighted coverage of 0.27 (TC3: 0.47, TC1: 0.97). Its council consensus of 50.3 falls below the 55-point threshold for LEAN_HIRE, and the resulting REJECT carries the flags for the experience deficit, the unverified skill claims and skill stuffing. TC3 keeps LEAN_HIRE because FastAPI is credited at 0.5 through Flask, while PyTorch and the deep-learning stack are reported as missing, which is what a recruiter should hear about a lateral candidate. TC4 illustrates the handling of uncertainty: with no parsed skills and inverted dates, the ATS quality score is 23 out of 100, the confidence falls to 32.8 and the council requests a human review instead of issuing a confident verdict.", keep=True)
    r.table(["Case", "Listed / evid.", "Coverage c~ev~", "Unevid. ratio", "Quant. results", "Verdict", "Main flags"], ev, "Council Evidence Metrics and Flags of the Four Test Cases", [0.55, 0.95, 0.95, 0.95, 0.9, 1.55, 2.2], size=9, align=["center", "center", "center", "center", "center", "left", "left"])
    r.fig(os.path.join(FIG, "ch_agents.png"), "Scores of the four council agents and the consensus for the demonstration resumes.", 13.5)

    r.h2("8.2.4", "Ablation of Evidence Weighting and Gates")
    abl = RES["ablation"]["no_evidence_weighting"]["scores_changed"]
    items = sorted(abl.items(), key=lambda kv: -kv[1][0])
    chg = {c[0] for c in RES["ablation"]["no_evidence_weighting"]["verdict_changes"]}
    arows = []
    for fn, (full, noev) in items:
        short, name = LABEL[fn]
        vc = next((f"{c[1]} \u2192 {c[2]}" for c in RES["ablation"]["no_evidence_weighting"]["verdict_changes"] if c[0] == fn), "none")
        arows.append([name, f"{full:.1f}", f"{noev:.1f}", f"{noev-full:+.1f}", vc])
    r.p(f"The council was re-run with evidence weighting disabled (coverage computed from the listed skills only, with no unevidenced-skill penalty) and, separately, with the red-flag gates disabled ({r.ref_next_tab()}, {r.ref_next_fig()}). Without evidence weighting every consensus score rises by 0.7 to 4.9 points. TC2 rises from 50.3 (REJECT) to 55.2 and is promoted to LEAN_HIRE just above the 55-point boundary, and Vikram Singh, a DevOps resume that lists several required machine-learning skills, is promoted in the same way; the other ten verdicts are unchanged. Evidence weighting is a deliberate trade-off: it penalises resumes whose skills appear only in lists, which can hurt terse but honest resumes, which is why such cases are routed to human review. Disabling the red-flag gates changed no verdict on this pool, because the flagged candidates already fall below the threshold; the gates are a safety net that this small pool does not exercise, and no empirical benefit is claimed for them here.", keep=True)
    r.table(["Resume", "Full council C", "No evidence weighting", "Change", "Verdict change"], arows, "Ablation: Council Consensus With and Without Evidence Weighting", [2.2, 1.0, 1.4, 0.8, 1.5], size=9.5, align=["left", "center", "center", "center", "left"])
    r.fig(os.path.join(FIG, "ch_ablation.png"), "Council consensus with and without evidence weighting.", 13.0)

    r.h2("8.2.5", "Demographic Robustness: Counterfactual Name Swap (RQ2)")
    r.p(f"Following the design of the audit study of Bertrand and Mullainathan [@bertrand], each of the 12 resumes was re-scored with four names used in that study (Emily Walsh, Greg Baker, Lakisha Washington and Jamal Jackson), substituted in both the name field and the text, with and without blind mode. This gives 12 \u00d7 4 \u00d7 2 = 96 runs. In every run the hybrid score and the council consensus were identical to those of the unmodified resume ({r.ref_next_tab()}). This is expected for a deterministic pipeline in which the name is never a scoring feature, so the invariance holds in the standard mode as well as in the blind mode. It should not be over-read: it demonstrates invariance for the TF-IDF backend and the rule-based council, not for dense embeddings or a language-model narrative, which are exactly the components where bias was observed in the literature [@wilson,@armstrong]. Blind mode is therefore a defence in depth, and testing it with the dense model and a language model is future work.", keep=True)
    ns = RES["name_swap_max_delta"]
    r.table(["Mode", "Hybrid score \u0394", "Council \u0394", "Runs"], [
        ["Standard", f"{ns['plain']['hybrid']:.2f}", f"{ns['plain']['council']:.2f}", "48"],
        ["Blind", f"{ns['blind']['hybrid']:.2f}", f"{ns['blind']['council']:.2f}", "48"],
    ], "Name-Swap Experiment: Maximum Score Change over All Substitutions (Points)", [1.5, 1.5, 1.5, 0.8], size=10.5, align=["left", "center", "center", "center"])

    r.h2("8.2.6", "Sensitivity to the Heuristic Weights (RQ3)")
    sens = RES["sensitivity"]
    r.p(f"Because the weights were chosen by the developers, each ranker weight was perturbed by a random factor between 0.8 and 1.2 (renormalised, {sens['draws']} Monte Carlo draws) and each council weight likewise (50 draws on each of the 12 resumes). {r.ref_next_tab()} shows that the rankings remained close to the default (mean Kendall \u03c4 = {sens['tau_mean']:.3f}, minimum {sens['tau_min']:.3f}); the top candidate and the top-3 set were unchanged in all {sens['draws']} draws, and the council verdict of every resume was unchanged in all 600 evaluations. The conclusions of the ranking analysis therefore do not depend on exact weight values within this range of plus or minus 20 percent, although larger changes and learned weights remain untested.", keep=True)
    r.table(["Quantity", "Value"], [
        ["Ranker draws", str(sens["draws"])],
        ["Mean Kendall \u03c4 against the default ranking", f"{sens['tau_mean']:.3f}"],
        ["Minimum Kendall \u03c4", f"{sens['tau_min']:.3f}"],
        ["Top-1 candidate stability", f"{100*sens['top1_stable']:.1f}%"],
        ["Top-3 set stability", f"{100*sens['top3_set_stable']:.1f}%"],
        ["Council verdict stability (600 evaluations)", f"{100*sens['council_verdict_stable']:.1f}%"],
    ], "Monte Carlo Weight-Perturbation Analysis (\u00b120 Percent)", [4.0, 1.5], size=10.5, align=["left", "center"])

    r.h2("8.2.7", "Talent-Search Retrieval Quality")
    rt = RES["retrieval"]
    r.p(f"Eight natural-language queries (for example *Engineers with 3+ years of Python and Git*) were issued. The resumes whose parsed skills contain every queried skill and whose experience meets the stated minimum were taken as relevant. BM25 only, dense (TF-IDF fallback) only and the hybrid fusion at alpha = 0.55 all reached a precision at 3 of {100*rt['hybrid_0.55']['P@3']:.1f} percent and a recall at 3 of {100*rt['hybrid_0.55']['R@3']:.1f} percent ({r.ref_next_tab()}). On a 12-resume pool the task is saturated, so this test confirms the correctness of the search but cannot show an advantage of the fusion. Evaluating dense and hybrid retrieval with the dense model on a larger pool with paraphrased queries is future work, and no superiority claim is made.", keep=True)
    r.table(["Retriever", "Precision@3", "Recall@3"], [
        ["BM25 only", f"{100*rt['bm25_only']['P@3']:.1f}%", f"{100*rt['bm25_only']['R@3']:.1f}%"],
        ["Dense only (TF-IDF fallback)", f"{100*rt['dense_only']['P@3']:.1f}%", f"{100*rt['dense_only']['R@3']:.1f}%"],
        ["Hybrid, \u03b1 = 0.55", f"{100*rt['hybrid_0.55']['P@3']:.1f}%", f"{100*rt['hybrid_0.55']['R@3']:.1f}%"],
    ], "Retrieval Quality (8 Queries, 12 Resumes)", [3.0, 1.3, 1.3], size=10.5, align=["left", "center", "center"])

    r.h2("8.2.8", "Scaled 100-Resume Multi-Role Benchmark")
    r.p(f"{r.ref_next_tab()} gives the verdict distribution by role; 94 of the 100 resumes carry at least one red flag, and the most frequent flags were REQUIRED_SKILLS_MISSING (70), NO_QUANTIFIED_IMPACT (67), EXPERIENCE_DEFICIT (40) and LEVEL_MISMATCH (12). Agreement with the generation label is defined strictly: a strong-hire profile should receive STRONG_HIRE, a lean-hire profile HIRE or LEAN_HIRE, and a reject profile REJECT. Table {r.chapter_no}.{r.tab_n + 2} shows the confusion matrix. The exact agreement is 46 of 100 (46.0 percent). The gross errors that matter most for a decision-support tool did not occur: no strong-hire profile was rejected and no reject profile received STRONG_HIRE.", keep=True)
    r.table(["Role", "n", "Labels (S / L / R)", "Verdicts (S / L / R)", "Flagged"], [
        ["Senior ML engineer", "13", "3 / 6 / 4", "0 / 11 / 2", "10"],
        ["Cloud DevOps and SRE lead", "13", "3 / 5 / 5", "0 / 11 / 2", "13"],
        ["Full-stack AI engineer", "13", "3 / 5 / 5", "0 / 12 / 1", "10"],
        ["Data platform engineer", "13", "3 / 5 / 5", "0 / 13 / 0", "13"],
        ["Backend systems architect", "12", "2 / 6 / 4", "0 / 11 / 1", "12"],
        ["AI safety and alignment", "12", "2 / 6 / 4", "0 / 4 / 8", "12"],
        ["BI and analytics lead", "12", "2 / 6 / 4", "0 / 6 / 6", "12"],
        ["Python / FastAPI developer", "12", "2 / 6 / 4", "0 / 11 / 1", "12"],
        ["All roles", "100", "20 / 45 / 35", "0 / 79 / 21", "94"],
    ], "100-Resume Benchmark by Role (S = Strong, L = Lean or Hire, R = Reject)", [2.4, 0.5, 1.4, 1.5, 0.8], size=10, align=["left", "center", "center", "center", "center"], bold_first=False)
    r.table(["Generation label", "STRONG_HIRE", "HIRE / LEAN_HIRE", "REJECT", "Mean consensus C"], [
        ["Strong (20)", "0", "20", "0", "71.2"],
        ["Lean (45)", "0", "35", "10", "60.1"],
        ["Reject (35)", "0", "24", "11", "62.0"],
    ], "Confusion Matrix: Generation Label Versus System Verdict", [1.8, 1.7, 1.8, 1.0, 1.5], size=10.5, align=["left", "center", "center", "center", "center"])
    r.fig(os.path.join(FIG, "ch_bench.png"), "Verdicts of the 100-resume benchmark by role.", 13.0)
    r.p("The results also expose weaknesses that are not hidden. The system never issued STRONG_HIRE on this benchmark (strong-hire recall 0 of 20), which is attributed to the level gate of the seniority agent, since senior-level experience was not fully evidenced in the text of the resumes. The mean consensus of the reject profiles (62.0) is slightly higher than that of the lean-hire profiles (60.1), so the score alone does not order these groups, and the reject recall is only 11 of 35. Because the labels were assigned by the generator itself, agreement with them measures consistency with the specification and not hiring accuracy, and no accuracy figure is reported beyond the confusion matrix.")

    r.h2("8.2.9", "Adversarial Edge-Case Stress Test (RQ5)")
    r.p(f"The first 20 benchmark resumes were run through the earlier pipeline (TF-IDF backend, rule-based council, no temporal gates). The four strong profiles all received STRONG_HIRE and all five buzzword profiles were rejected with the flags for experience deficit and unverified claims. The anomaly probes, however, were not caught ({r.ref_next_tab()}). Candidate 019 lists a senior role as *Jul 2026 to Jan 2024*; the old parser discarded the inverted interval, so the resume was scored on a 2.0-year history and still received HIRE (72.5). Candidate 013 lists a full-time on-site role in San Jose from March 2023 concurrent with a full-time role in Bengaluru from January 2022 to August 2025, an overlap of 29 months; it received STRONG_HIRE (89.7) with no flag. Under the upgraded pipeline, the gates of Section 6.2 cap 019, 013 and C1 at LEAN_HIRE, and C2 drops from STRONG_HIRE to HIRE.", keep=True)
    r.table(["ID", "Defect", "Before", "After", "Flag"], [
        ["019", "Inverted dates, Jul 2026 to Jan 2024", "HIRE (72.5)", "LEAN_HIRE (73.5)", "DATE_INCONSISTENCY"],
        ["013", "Concurrent full-time roles, San Jose and Bengaluru", "STRONG_HIRE (89.7)", "LEAN_HIRE (89.0)", "CONCURRENT_EMPLOYMENT_CONFLICT"],
        ["C1", "Inverted dates in a strong profile", "HIRE (78.6)", "LEAN_HIRE (73.2)", "DATE_INCONSISTENCY"],
        ["C2", "No education, phone or LinkedIn", "STRONG_HIRE (92.6)", "HIRE (78.6)", "MISSING_EDUCATION"],
    ], "Adversarial Probes: Verdicts Before and After the New Gates (Consensus in Parentheses)", [0.5, 2.3, 1.3, 1.3, 1.9], size=9, align=["center", "left", "center", "center", "left"])
    r.p("This probe is a regression case study and not a held-out detection rate: the gates were written after these failures were observed, so catching the same resumes shows that the fix works, not that the gates generalise to unseen fraud patterns. The exercise also shows why the semantic component cannot see these attacks: an inverted date range or a second employer is invisible to TF-IDF and to embedding similarity, and only an explicit timeline model exposes them.")

    r.h1("8.3", "DISCUSSION")
    r.p("The experiments support five statements, each with its own limitation. First (RQ1), the evidence mechanism separates a keyword-stuffed resume from a genuine one that the keyword baseline scores identically, and ranks it tenth of twelve; this is shown by a case analysis on a small synthetic pool and not by a statistical test. Second (RQ2), scores and verdicts did not change in 96 name-substitution runs, but this holds for the deterministic components only. Third (RQ3), the rankings and verdicts were stable under random weight changes of 20 percent. Fourth (RQ4), a complete screening costs about 30 milliseconds per resume in the offline configuration. Fifth (RQ5), the explicit timeline gates intercept the inverted-date and concurrent-employment probes, which similarity scoring cannot see, but the probes were used to design the gates.")
    r.p("The main weaknesses are the circularity of synthetic data, the conservative calibration of the verdicts (no strong hire in the 100-resume benchmark and only 11 of 35 reject profiles rejected), the heuristic weights and thresholds, the limited fairness scope of blind screening (direct identifiers only), the lack of a usability study, and the free-tier hosting of the deployed service, which sleeps when idle and has not been load-tested. They are stated here so that the results are not over-read, and they define the next steps in Chapter 9.")
    r.p("Beyond the experiments, the system now runs as a deployed multi-user service, with the web interface on Vercel, the API on Render and the accounts, sessions and candidate pools in MongoDB Atlas. Its behaviour is checked by 78 automated tests and by manual checks of the live site (Chapter 7). These checks show that the service works as designed; they do not measure its performance under load or its usability for recruiters.")
    r.p("Summary. This chapter showed the working system through screenshots of the real interface and reported the experiments on latency, ranking divergence, evidence weighting, name invariance, weight sensitivity, retrieval, a 100-resume benchmark and adversarial resumes, and it discussed the deployed service.", indent=False)

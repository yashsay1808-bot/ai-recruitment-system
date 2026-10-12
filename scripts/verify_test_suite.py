"""
Verification harness for the demo / viva test-resume suite.

Runs every resume in data/sample_resumes through the REAL pipeline (parser -> ATS quality analyzer -> hybrid
ranker -> explainable AI -> multi-agent council) against the default 'Machine Learning Engineer' job description and
prints a results table. Use it to show the professor that scores are computed, not hard-coded.

Run from the project root:   python scripts/verify_test_suite.py
"""
import glob
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.agentic_council import RecruitmentCouncil
from src.core.explainable_ai import ExplainableAI
from src.core.hybrid_ranker import HybridRanker
from src.core.jd_parser import JDParser
from src.core.quality_analyzer import ResumeQualityAnalyzer
from src.core.resume_parser import ResumeParser
from src.ui.views.job_management import SAMPLE_JOB_TEMPLATES


def run(verbose: bool = True):
    tpl = SAMPLE_JOB_TEMPLATES["Machine Learning Engineer"]
    jd = JDParser().parse(tpl["text"], title_hint="Machine Learning Engineer")
    jd["min_experience_years"] = tpl["min_experience"]
    parser, qa, xai = ResumeParser(), ResumeQualityAnalyzer(), ExplainableAI()
    council = RecruitmentCouncil(use_llm=False)

    cands = []
    for path in sorted(glob.glob("data/sample_resumes/*.*")):
        with open(path, "rb") as fh:
            cands.append(parser.parse(fh.read(), os.path.basename(path)))
    quality = {c["file_name"]: qa.analyze(c, jd["required_skills"]) for c in cands}
    ranked = HybridRanker().rank_all_candidates(cands, jd, {k: v["quality_score"] for k, v in quality.items()})

    rows = []
    for r in ranked:
        r["explanation"] = xai.generate_explanation(r, jd)
        rep = council.evaluate_candidate_council(r["candidate_data"], jd)
        ec = rep["executive_consensus"]
        rows.append({
            "rank": r["rank"], "file": r["file_name"], "match": r["overall_score"],
            "ats": quality[r["file_name"]]["quality_score"], "verdict": ec["verdict"],
            "council": ec["final_score"], "flags": [x["code"] for x in ec["red_flags"]],
            "missing": r["gap_results"]["missing_skills"], "partial": [p["required_skill"] for p in r["gap_results"]["partially_matched_skills"]],
            "years": r["candidate_data"]["experience"]["years_of_experience"],
        })
    if verbose:
        print(f"JD: {jd['job_title']} | required: {', '.join(jd['required_skills'])}\n")
        print(f"{'#':>2} {'Resume':<42} {'Match':>6} {'ATS':>5} {'Council':>8} {'Verdict':<11} Red flags")
        for x in rows:
            print(f"{x['rank']:>2} {x['file'][:42]:<42} {x['match']:>5}% {x['ats']:>5} {x['council']:>7}% {x['verdict']:<11} {', '.join(x['flags']) or '-'}")
    return rows


if __name__ == "__main__":
    run()

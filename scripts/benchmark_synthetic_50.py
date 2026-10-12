"""Runs the 50 synthetic resumes through the real pipeline, each against its own role's JD, and scores the ATS
against the ground truth in manifest.csv.  Run from the project root:
    python scripts/benchmark_synthetic_50.py data/synthetic_resumes
"""
import csv, os, sys, warnings, collections
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.agentic_council import RecruitmentCouncil
from src.core.hybrid_ranker import HybridRanker
from src.core.jd_parser import JDParser
from src.core.quality_analyzer import ResumeQualityAnalyzer
from src.core.resume_parser import ResumeParser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_synthetic_resumes import ROLES

def main(d):
    man = list(csv.DictReader(open(os.path.join(d, "manifest.csv"), encoding="utf-8")))
    parser, qa, council = ResumeParser(), ResumeQualityAnalyzer(), RecruitmentCouncil(use_llm=False)
    by_role = collections.defaultdict(list)
    for r in man: by_role[r["role"]].append(r)
    out = []
    for role, rows in by_role.items():
        R = ROLES[role.replace(" ", "_")]
        jd = JDParser().parse(R["jd"], title_hint=R["title"]); jd["min_experience_years"] = R["jd_min"]
        cands = [parser.parse(open(os.path.join(d, r["file"]), "rb").read(), r["file"]) for r in rows]
        q = {c["file_name"]: qa.analyze(c, jd["required_skills"]) for c in cands}
        ranked = HybridRanker().rank_all_candidates(cands, jd, {k: v["quality_score"] for k, v in q.items()})
        meta = {r["file"]: r for r in rows}
        for x in ranked:
            ec = council.evaluate_candidate_council(x["candidate_data"], jd)["executive_consensus"]
            m = meta[x["file_name"]]
            out.append(dict(file=x["file_name"], role=role, category=m["category"], rank_in_role=x["rank"], pool=len(rows),
                            match=x["overall_score"], ats=q[x["file_name"]]["quality_score"], council=ec["final_score"],
                            verdict=ec["verdict"], flags=[f["code"] for f in ec["red_flags"]],
                            years=x["candidate_data"]["experience"]["years_of_experience"], expected=m["expected_verdict"]))
    return out

def ok(r):
    exp = r["expected"].replace(" or ", "|").split("|")
    return r["verdict"] in [e.strip() for e in exp]

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "data/synthetic_resumes"
    res = main(d)
    cats = ["Gold Standard", "Lateral Switcher", "Early Career Fresher", "Keyword Stuffing", "Corrupt Layout"]
    print(f"{'Category':<22}{'n':>3}{'mean match':>12}{'mean council':>14}{'mean ATS':>10}{'verdict as expected':>21}")
    for c in cats:
        rr = [r for r in res if r["category"] == c]
        print(f"{c:<22}{len(rr):>3}{sum(r['match'] for r in rr)/len(rr):>12.1f}{sum(r['council'] for r in rr)/len(rr):>14.1f}{sum(r['ats'] for r in rr)/len(rr):>10.1f}{sum(ok(r) for r in rr):>14}/{len(rr)}")
    print("\nVerdict distribution by category")
    for c in cats:
        cnt = collections.Counter(r["verdict"] for r in res if r["category"] == c)
        print(f"  {c:<22}", dict(cnt))
    fl = collections.defaultdict(collections.Counter)
    for r in res:
        for f in r["flags"]: fl[r["category"]][f] += 1
    print("\nRed flags by category")
    for c in cats: print(f"  {c:<22}", dict(fl[c]))
    gold_top = sum(1 for r in res if r["category"] == "Gold Standard" and r["rank_in_role"] <= 2)
    print(f"\nGold-standard resumes ranked in their role's top-2: {gold_top}/10")
    with open("synthetic_benchmark_results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["file","role","category","rank_in_role","match","ats","council","verdict","years","flags","expected"])
        for r in sorted(res, key=lambda r: r["file"]):
            w.writerow([r["file"],r["role"],r["category"],r["rank_in_role"],r["match"],r["ats"],r["council"],r["verdict"],r["years"],";".join(r["flags"]),r["expected"]])

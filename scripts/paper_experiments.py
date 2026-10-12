"""
Reproduces every number reported in the IEEE paper and writes them to paper_results.json (+ a readable summary).

Run from the project root:   python scripts/paper_experiments.py
Takes about a minute on a laptop. Share the printed summary / paper_results.json so the paper can be updated.
"""
import copy, dataclasses, glob, importlib.util, json, os, platform, re, sys, time, warnings

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault("TALENT_RAG_DISABLE_ST", "1")  # keep the search test deterministic / offline

import numpy as np
from scipy.stats import kendalltau

import src.core.agentic_council as ac
from src.core.bias_filter import BiasFilter
from src.core.hybrid_ranker import HybridRanker
from src.core.jd_parser import JDParser
from src.core.quality_analyzer import ResumeQualityAnalyzer
from src.core.resume_parser import ResumeParser
from src.core.skill_ontology import SKILL_ONTOLOGY, normalize_skill
from src.core.talent_rag import TalentRAG
from src.ui.views.job_management import SAMPLE_JOB_TEMPLATES

tpl = SAMPLE_JOB_TEMPLATES["Machine Learning Engineer"]
jd = JDParser().parse(tpl["text"], title_hint="Machine Learning Engineer")
jd["min_experience_years"] = tpl["min_experience"]
P, QA = ResumeParser(), ResumeQualityAnalyzer()
paths = sorted(glob.glob("data/sample_resumes/*.*"))
out = {"env": {"python": platform.python_version(), "sentence_transformers_installed": importlib.util.find_spec("sentence_transformers") is not None,
               "n_resumes": len(paths), "jd_required": jd["required_skills"], "ontology_skills": len(SKILL_ONTOLOGY)}}

t0 = time.time(); cands = [P.parse(open(p, "rb").read(), os.path.basename(p)) for p in paths]; t_parse = (time.time() - t0) / len(cands)

def rank(cs, weights=None):
    q = {c["file_name"]: QA.analyze(c, jd["required_skills"])["quality_score"] for c in cs}
    hr = HybridRanker()
    if weights: hr.weights = weights
    return hr.rank_all_candidates(cs, jd, q)

t0 = time.time(); ranked = rank(cands); t_rank = (time.time() - t0) / len(cands)
council = ac.RecruitmentCouncil(use_llm=False)
t0 = time.time(); reps = {r["file_name"]: council.evaluate_candidate_council(r["candidate_data"], jd) for r in ranked}; t_council = (time.time() - t0) / len(cands)
out["latency_ms_per_resume"] = {"parse": t_parse * 1e3, "rank": t_rank * 1e3, "council": t_council * 1e3, "total": (t_parse + t_rank + t_council) * 1e3}

# E1 baseline + Table of results
req = jd["required_skills"]; rows = []
for r in ranked:
    txt = r["candidate_data"]["raw_text"].lower()
    base = 100 * sum(1 for s in req if s.lower() in txt) / len(req)
    ec = reps[r["file_name"]]["executive_consensus"]; sc = reps[r["file_name"]]["agent_scorecards"]
    rows.append(dict(file=r["file_name"], rank=r["rank"], proposed=r["overall_score"], baseline=round(base, 1), council=ec["final_score"],
                     verdict=ec["verdict"], confidence=ec["confidence"], human_review=ec["human_review_required"],
                     flags=[f["code"] for f in ec["red_flags"]], years=r["candidate_data"]["experience"]["years_of_experience"],
                     agents={k: round(v["score"], 1) for k, v in sc.items()}, tech_metrics=sc["tech_lead"].get("metrics", {}),
                     breakdown=r["breakdown"], ats=QA.analyze(r["candidate_data"], jd["required_skills"])["quality_score"]))
order = sorted(rows, key=lambda x: -x["baseline"])
for i, x in enumerate(order): x["baseline_rank"] = i + 1
out["kendall_tau_baseline_vs_proposed"] = float(kendalltau([x["rank"] for x in rows], [x["baseline_rank"] for x in rows])[0])
out["rows"] = rows

# E2 name swap (plain and blind)
names = ["Emily Walsh", "Greg Baker", "Lakisha Washington", "Jamal Jackson"]; bf = BiasFilter()
def swap(c, n):
    d = copy.deepcopy(c); old = d["candidate_name"]
    d["raw_text"] = re.sub(re.escape(old), n, d["raw_text"], flags=re.I); d["candidate_name"] = n; return d
sw = {"plain": [], "blind": []}
for idx, c in enumerate(cands):
    for mode in sw:
        sc_, cs_ = [], []
        for n in names:
            pool = [swap(x, n) if j == idx else x for j, x in enumerate(cands)]
            if mode == "blind": pool = [bf.anonymize_candidate(x, j + 1) for j, x in enumerate(pool)]
            rk = rank(pool); key = f"Application_{idx+1:03d}.pdf" if mode == "blind" else c["file_name"]
            me = [r for r in rk if r["file_name"] == key][0]
            sc_.append(me["overall_score"]); cs_.append(council.evaluate_candidate_council(me["candidate_data"], jd)["executive_consensus"]["final_score"])
        sw[mode].append((max(sc_) - min(sc_), max(cs_) - min(cs_)))
out["name_swap_max_delta"] = {m: {"hybrid": max(a for a, _ in v), "council": max(b for _, b in v)} for m, v in sw.items()}

# E3 ablation
orig_bf, orig_rf = ac._build_features, ac.RecruitmentCouncil._red_flags
def run_council():
    c = ac.RecruitmentCouncil(use_llm=False); res = {}
    for r in cands:
        e = c.evaluate_candidate_council(r, jd)["executive_consensus"]; res[r["file_name"]] = (e["final_score"], e["verdict"])
    return res
full = run_council()
def noev(cand, jdd, today=None):
    f = orig_bf(cand, jdd, today)
    return dataclasses.replace(f, evid_coverage=f.coverage, unevidenced_ratio=0.0, hype_unevidenced=[], req_evidenced=list(f.req_hits))
ac._build_features = noev; A1 = run_council(); ac._build_features = orig_bf
ac.RecruitmentCouncil._red_flags = lambda self, *a, **k: []; A2 = run_council(); ac.RecruitmentCouncil._red_flags = orig_rf
out["ablation"] = {name: {"verdict_changes": [(k, full[k][1], A[k][1]) for k in full if A[k][1] != full[k][1]],
                          "scores_changed": {k: [full[k][0], A[k][0]] for k in full if A[k][0] != full[k][0]}} for name, A in [("no_evidence_weighting", A1), ("no_flag_gates", A2)]}

# E4 weight sensitivity
np.random.seed(7); W = dict(HybridRanker.DEFAULT_WEIGHTS); base_order = [r["file_name"] for r in ranked]; taus = []; t1 = t3 = 0; N = 200
for _ in range(N):
    w = {k: v * np.random.uniform(0.8, 1.2) for k, v in W.items()}; s = sum(w.values()); w = {k: v / s for k, v in w.items()}
    f = [x["file_name"] for x in rank(cands, w)]; pos = {n: i for i, n in enumerate(f)}
    taus.append(kendalltau(range(len(base_order)), [pos[n] for n in base_order])[0]); t1 += f[0] == base_order[0]; t3 += set(f[:3]) == set(base_order[:3])
cw = dict(ac.RecruitmentCouncil.DEFAULT_WEIGHTS); same = tot = 0
for _ in range(50):
    c = ac.RecruitmentCouncil(use_llm=False, weights={k: v * np.random.uniform(0.8, 1.2) for k, v in cw.items()})
    for r in cands:
        same += c.evaluate_candidate_council(r, jd)["executive_consensus"]["verdict"] == full[r["file_name"]][1]; tot += 1
out["sensitivity"] = {"draws": N, "tau_mean": float(np.mean(taus)), "tau_min": float(np.min(taus)), "top1_stable": t1 / N, "top3_set_stable": t3 / N, "council_verdict_stable": same / tot}

# E5 retrieval quality
def has(c, sk):
    have = {normalize_skill(s) or s for s in c["skills"]}; return all((normalize_skill(s) or s) in have for s in sk)
queries = [("Find engineers with Docker and AWS experience", ["Docker", "AWS"], 0), ("Candidates who know PyTorch and Deep Learning", ["PyTorch", "Deep Learning"], 0),
           ("Developers with Flask and REST API experience", ["Flask", "REST API"], 0), ("Engineers with 3+ years of Python and Git", ["Python", "Git"], 3),
           ("Machine learning with Scikit-Learn and Pandas", ["Scikit-Learn", "Pandas"], 0), ("Natural language processing with Hugging Face", ["Natural Language Processing", "Hugging Face"], 0),
           ("Backend developers with FastAPI and Docker", ["FastAPI", "Docker"], 0), ("TensorFlow and Deep Learning practitioners with 2+ years", ["TensorFlow", "Deep Learning"], 2)]
ret = {}
for alpha, nm in [(0.0, "bm25_only"), (1.0, "dense_only"), (0.55, "hybrid_0.55")]:
    eng = TalentRAG(embedding_backend="tfidf", alpha=alpha); ps = []; rs = []
    for q, sk, y in queries:
        rel = {c["file_name"] for c in cands if has(c, sk) and c["experience"]["years_of_experience"] >= y}
        got = [c["file_name"] for h in eng.search_talent_pool(q, [dict(c) for c in cands], top_k=3) for c in cands if c["candidate_name"] == h["candidate_name"]]
        tp = len([g for g in got if g in rel]); ps.append(tp / 3); rs.append(tp / min(3, len(rel)) if rel else 1.0)
    ret[nm] = {"P@3": float(np.mean(ps)), "R@3": float(np.mean(rs))}
out["retrieval"] = ret

json.dump(out, open("paper_results.json", "w"), indent=1, default=float)
print("\n=== PAPER RESULTS SUMMARY ===")
print("env:", out["env"]["python"], "| sentence-transformers installed:", out["env"]["sentence_transformers_installed"], "| resumes:", out["env"]["n_resumes"])
print("latency ms/resume:", {k: round(v, 1) for k, v in out["latency_ms_per_resume"].items()})
print(f"{'#':>2} {'resume':<42}{'base':>6}{'prop':>6}{'cncl':>6} verdict      flags")
for x in rows: print(f"{x['rank']:>2} {x['file'][:41]:<42}{x['baseline']:>6}{x['proposed']:>6}{x['council']:>6} {x['verdict']:<12} {','.join(x['flags'])}")
for k in ("kendall_tau_baseline_vs_proposed", "name_swap_max_delta", "ablation", "sensitivity", "retrieval"): print(k, json.dumps(out[k], default=float))
print("\nWrote paper_results.json")

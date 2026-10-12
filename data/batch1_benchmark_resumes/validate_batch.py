import csv, glob, os, sys, warnings, re, collections
warnings.filterwarnings("ignore")
sys.path.insert(0, sys.argv[2])
from src.core.resume_parser import ResumeParser
from src.core.agentic_council import RecruitmentCouncil
from src.core.hybrid_ranker import HybridRanker
from src.core.jd_parser import JDParser
from src.core.quality_analyzer import ResumeQualityAnalyzer
d = sys.argv[1]
man = {r["file"]: r for r in csv.DictReader(open(os.path.join(d, "batch1_manifest.csv"), encoding="utf-8"))}
P = ResumeParser()
JD = {"Senior Machine Learning Engineer": ("Senior Machine Learning Engineer. 4+ years. Production ML. Requires PyTorch, TensorFlow, FastAPI, Docker, AWS, Hugging Face, MLOps, Scikit-Learn, Python.", 4.0),
      "Cloud DevOps & SRE Lead": ("Cloud DevOps and SRE Lead. 5+ years. Requires Kubernetes, Docker, Terraform, AWS, CI/CD, Linux, Prometheus, Grafana, Python.", 5.0),
      "Full-Stack AI Engineer": ("Full-Stack AI Engineer. 3+ years. Requires React, TypeScript, Python, FastAPI, Next.js, LangChain, PostgreSQL, Docker.", 3.0)}
bad = []; res = []
council = RecruitmentCouncil(use_llm=False); qa = ResumeQualityAnalyzer()
for fn, m in man.items():
    txt = open(os.path.join(d, fn), encoding="utf-8").read()
    c = P.parse(txt.encode(), fn)
    lines = txt.splitlines()
    name = lines[0].strip()
    issues = []
    pn = c.get("personal_info", {}) if isinstance(c.get("personal_info"), dict) else {}
    flat = str(c)
    if name not in flat: issues.append("name")
    if m["archetype"] != "missing_edu":
        em = re.search(r"Email: (\S+)", txt).group(1)
        if em not in flat: issues.append("email")
        if not c.get("education"): issues.append("education-empty")
    if m["github"] not in flat: issues.append("github")
    sk = c.get("skills") or []
    n_sk = len(sk) if hasattr(sk, "__len__") else 0
    if n_sk < 8: issues.append(f"skills={n_sk}")
    ex = c.get("experience", {}) or {}
    if not ex.get("work_experience") and not ex.get("years_of_experience"): issues.append("experience")
    res.append((fn, issues, n_sk, ex.get("years_of_experience")))
    if issues: bad.append((fn, issues))
print("parsed:", len(res), "clean:", len(res) - len(bad))
for b in bad: print(" ISSUE", b)
print(list(c.keys()))
rows = []
for role, (jt, mn) in JD.items():
    sel = [(fn, m) for fn, m in man.items() if m["role"] == role]
    if not sel: continue
    jd = JDParser().parse(jt, title_hint=role); jd["min_experience_years"] = mn
    cands = [P.parse(open(os.path.join(d, fn), "rb").read(), fn) for fn, _ in sel]
    q = {x["file_name"]: qa.analyze(x, jd["required_skills"]) for x in cands}
    rk = HybridRanker().rank_all_candidates(cands, jd, {k: v["quality_score"] for k, v in q.items()})
    for x in rk:
        ec = council.evaluate_candidate_council(x["candidate_data"], jd)["executive_consensus"]
        rows.append((man[x["file_name"]]["archetype"], x["file_name"][:42], x["overall_score"], ec["final_score"], ec["verdict"], [f["code"] for f in ec["red_flags"]], x["candidate_data"]["experience"]["years_of_experience"]))
for a in ["gold", "mid", "stuff", "chrono_inv", "chrono_2c", "missing_edu"]:
    rr = [r for r in rows if r[0] == a]
    if rr: print(f"{a:12} n={len(rr):2} match {sum(r[2] for r in rr)/len(rr):5.1f} council {sum(r[3] for r in rr)/len(rr):5.1f}", dict(collections.Counter(r[4] for r in rr)))
for r in sorted(rows, key=lambda r: (r[0], -r[2])): print(r)

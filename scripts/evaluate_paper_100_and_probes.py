import csv
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from collections import defaultdict, Counter
from src.core.resume_parser import ResumeParser
from src.core.agentic_council import RecruitmentCouncil

# 1. Job descriptions for the 8 roles
ROLE_JDS = {
    "Senior_ML": {
        "job_title": "Senior Machine Learning Engineer",
        "required_skills": ["Python", "PyTorch", "TensorFlow", "FastAPI", "Docker", "AWS", "Hugging Face", "MLOps", "Scikit-Learn", "Pandas"],
        "min_experience_years": 4.5
    },
    "Cloud_DevOps": {
        "job_title": "Cloud DevOps and SRE Lead",
        "required_skills": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "Linux", "Prometheus", "Grafana", "Ansible", "Helm"],
        "min_experience_years": 5.0
    },
    "FullStack_AI": {
        "job_title": "Full-Stack AI Application Engineer",
        "required_skills": ["React", "TypeScript", "Python", "FastAPI", "Next.js", "LangChain", "PostgreSQL", "Docker", "TailwindCSS", "Redis"],
        "min_experience_years": 3.5
    },
    "Data_Platform": {
        "job_title": "Data Platform & Distributed Systems Engineer",
        "required_skills": ["Python", "Apache Spark", "Kafka", "SQL", "Snowflake", "AWS S3", "Airflow", "PostgreSQL", "Pandas", "Docker"],
        "min_experience_years": 4.0
    },
    "Backend_Architect": {
        "job_title": "Backend Systems Architect",
        "required_skills": ["Go", "Python", "Distributed Systems", "Microservices", "gRPC", "Redis", "PostgreSQL", "Docker", "Kubernetes", "Kafka"],
        "min_experience_years": 6.0
    },
    "AI_Safety": {
        "job_title": "AI Safety & Alignment Engineer",
        "required_skills": ["Python", "PyTorch", "RLHF", "Red Teaming", "Adversarial Robustness", "Hugging Face", "Docker", "FastAPI", "Pandas", "NumPy"],
        "min_experience_years": 4.0
    },
    "BI_Analyst": {
        "job_title": "Business Intelligence & Analytics Lead",
        "required_skills": ["SQL", "Tableau", "Power BI", "Python", "Data Modeling", "Pandas", "ETL", "Snowflake", "Excel", "PostgreSQL"],
        "min_experience_years": 4.0
    },
    "Python_Backend": {
        "job_title": "Python / FastAPI Core Developer",
        "required_skills": ["Python", "FastAPI", "AsyncIO", "PostgreSQL", "Redis", "Docker", "PyTest", "Celery", "REST API", "SQLAlchemy"],
        "min_experience_years": 3.0
    }
}

ROLE_DISPLAY = {
    "Senior_ML": "Senior ML engineer",
    "Cloud_DevOps": "Cloud DevOps and SRE lead",
    "FullStack_AI": "Full-stack AI engineer",
    "Data_Platform": "Data platform engineer",
    "Backend_Architect": "Backend systems architect",
    "AI_Safety": "AI safety and alignment",
    "BI_Analyst": "BI and analytics lead",
    "Python_Backend": "Python/FastAPI developer"
}

def map_role_key(filename: str) -> str:
    for k in ROLE_JDS.keys():
        if k.lower() in filename.lower():
            return k
    return "Senior_ML"

def run_100_benchmark():
    parser = ResumeParser()
    council = RecruitmentCouncil(use_llm=False)
    manifest_path = Path("data/synthetic_resumes_100/manifest.csv")
    res_dir = Path("data/synthetic_resumes_100")

    rows = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # Aggregators by role
    role_stats = defaultdict(lambda: {
        "n": 0,
        "labels": {"STRONG": 0, "LEAN": 0, "REJECT": 0},
        "verdicts": {"STRONG": 0, "LEAN": 0, "REJECT": 0},
        "flagged": 0
    })

    flag_counts = Counter()
    archetype_scores = defaultdict(list)
    confusion = defaultdict(Counter)

    for r in rows:
        fn = r.get("file") or r.get("filename")
        target = r["expected_verdict"] # STRONG_HIRE, LEAN_HIRE, REJECT
        role_key = map_role_key(fn)
        jd = ROLE_JDS[role_key]

        file_path = res_dir / fn
        cand = parser.parse(file_path.read_bytes(), fn)
        eval_res = council.evaluate_candidate_council(cand, jd)
        consensus = eval_res["executive_consensus"]
        verdict = consensus["verdict"] # STRONG_HIRE, HIRE, LEAN_HIRE, REJECT
        score = consensus["final_score"]
        flags = [f["code"] for f in consensus["red_flags"]]

        # Simplify verdict into S/L/R
        v_simple = "STRONG" if verdict == "STRONG_HIRE" else ("LEAN" if verdict in ["HIRE", "LEAN_HIRE"] else "REJECT")
        t_simple = "STRONG" if target == "STRONG_HIRE" else ("LEAN" if target == "LEAN_HIRE" else "REJECT")

        role_stats[role_key]["n"] += 1
        role_stats[role_key]["labels"][t_simple] += 1
        role_stats[role_key]["verdicts"][v_simple] += 1
        if flags:
            role_stats[role_key]["flagged"] += 1

        for fl in flags:
            flag_counts[fl] += 1

        archetype_scores[t_simple].append(score)
        confusion[t_simple][v_simple] += 1

    print("\n" + "="*80)
    print("TABLE VI: 100-RESUME BENCHMARK BY ROLE")
    print("="*80)
    print(f"{'Role':<32} {'n':<4} {'Labels (S/L/R)':<16} {'Verdicts (S/L/R)':<18} {'Flagged'}")
    print("-"*80)
    
    total_n = 0
    tot_l = {"STRONG": 0, "LEAN": 0, "REJECT": 0}
    tot_v = {"STRONG": 0, "LEAN": 0, "REJECT": 0}
    tot_flagged = 0

    for r_k in ROLE_JDS.keys():
        st = role_stats[r_k]
        disp = ROLE_DISPLAY[r_k]
        lbl_str = f"{st['labels']['STRONG']}/{st['labels']['LEAN']}/{st['labels']['REJECT']}"
        vrd_str = f"{st['verdicts']['STRONG']}/{st['verdicts']['LEAN']}/{st['verdicts']['REJECT']}"
        print(f"{disp:<32} {st['n']:<4} {lbl_str:<16} {vrd_str:<18} {st['flagged']}")
        total_n += st['n']
        for k in tot_l: tot_l[k] += st['labels'][k]
        for k in tot_v: tot_v[k] += st['verdicts'][k]
        tot_flagged += st['flagged']

    print("-"*80)
    print(f"{'All roles':<32} {total_n:<4} {tot_l['STRONG']}/{tot_l['LEAN']}/{tot_l['REJECT']:<14} {tot_v['STRONG']}/{tot_v['LEAN']}/{tot_v['REJECT']:<16} {tot_flagged}")
    print("="*80)

    print("\nPER-FLAG BREAKDOWN (Across 100 Resumes):")
    for fl, cnt in flag_counts.most_common():
        print(f"  • {fl}: {cnt}")

    print("\nCONFUSION MATRIX (Ground Truth Label -> System Verdict):")
    print(f"  STRONG Label (20):  {confusion['STRONG']['STRONG']} Strong, {confusion['STRONG']['LEAN']} Lean/Hire, {confusion['STRONG']['REJECT']} Reject")
    print(f"  LEAN Label (45):    {confusion['LEAN']['STRONG']} Strong, {confusion['LEAN']['LEAN']} Lean/Hire, {confusion['LEAN']['REJECT']} Reject")
    print(f"  REJECT Label (35):  {confusion['REJECT']['STRONG']} Strong, {confusion['REJECT']['LEAN']} Lean/Hire, {confusion['REJECT']['REJECT']} Reject")

    correct = confusion['STRONG']['STRONG'] + confusion['LEAN']['LEAN'] + confusion['REJECT']['REJECT']
    print(f"\nOverall Agreement: {correct}/100 ({correct:.1f}%)")

    print("\nMEAN COUNCIL SCORES PER ARCHETYPE:")
    for arch in ["STRONG", "LEAN", "REJECT"]:
        scs = archetype_scores[arch]
        mean_sc = sum(scs) / len(scs) if scs else 0
        print(f"  • {arch} Profiles: Mean = {mean_sc:.1f} (min {min(scs):.1f}, max {max(scs):.1f})")

def run_adversarial_probes():
    parser = ResumeParser()
    council = RecruitmentCouncil(use_llm=False)
    
    # Check 019 and 013
    jd_ml = ROLE_JDS["Senior_ML"]
    jd_sre = ROLE_JDS["Cloud_DevOps"]

    print("\n" + "="*80)
    print("TABLE VII: ADVERSARIAL PROBES EVALUATION")
    print("="*80)
    
    p19 = Path("data/claude_batch_1/019_Abhishek_Tiwari_Senior_ML_Engineer_ATS_Parse_Warning.txt")
    if p19.exists():
        c19 = parser.parse(p19.read_bytes(), p19.name)
        res19 = council.evaluate_candidate_council(c19, jd_ml)["executive_consensus"]
        fl19 = [f["code"] for f in res19["red_flags"]]
        print(f"ID 019: Inverted dates, Jul 2026-Jan 2024 -> Before: HIRE (72.5) | After: {res19['verdict']} ({res19['final_score']}) | Flags: {fl19}")

    p13 = Path("data/claude_batch_1/013_Pranav_Joshi_Cloud_DevOps_SRE_Lead_ATS_Parse_Warning.txt")
    if p13.exists():
        c13 = parser.parse(p13.read_bytes(), p13.name)
        res13 = council.evaluate_candidate_council(c13, jd_sre)["executive_consensus"]
        fl13 = [f["code"] for f in res13["red_flags"]]
        print(f"ID 013: Concurrent full-time, San Jose & Bengaluru -> Before: STRONG_HIRE (89.7) | After: {res13['verdict']} ({res13['final_score']}) | Flags: {fl13}")

    # C1 probe (inverted dates strong)
    text_c1 = """Vikram Adani
vikram.adani@mail.in | +91 98888 77777 | Bengaluru, India | github.com/vikram-ad
PROFESSIONAL SUMMARY
Lead ML Engineer with 6 years experience shipping production transformers.
TECHNICAL SKILLS
Python, PyTorch, TensorFlow, FastAPI, Docker, AWS, Hugging Face, MLOps, Scikit-Learn, Pandas
EDUCATION
B.Tech CSE, IIT Bombay | 2018
WORK EXPERIENCE
Staff ML Engineer | TechCorp (Aug 2026 - Jan 2024)
• Built RoBERTa model on AWS serving 100k requests/day at 40ms p95.
• Cut GPU costs by 30% via quantization.
Senior ML Engineer | StartupX (Jul 2018 - Dec 2023)
• Led PyTorch recommendation engine."""
    c_c1 = parser.parse(text_c1.encode("utf-8"), "C1.txt")
    res_c1 = council.evaluate_candidate_council(c_c1, jd_ml)["executive_consensus"]
    fl_c1 = [f["code"] for f in res_c1["red_flags"]]
    print(f"Probe C1: Inverted dates strong profile -> Before: HIRE (78.6) | After: {res_c1['verdict']} ({res_c1['final_score']}) | Flags: {fl_c1}")

    # C2 probe (no education, no phone/socials)
    text_c2 = """Anil Deshmukh
Email: anil.deshmukh@mail.in
PROFESSIONAL SUMMARY
Senior ML Engineer with 5.5 years experience shipping production NLP models.
TECHNICAL SKILLS
Python, PyTorch, TensorFlow, FastAPI, Docker, AWS, Hugging Face, MLOps, Scikit-Learn, Pandas
WORK EXPERIENCE
Senior ML Engineer | CloudNest (Jan 2021 - Present)
• Built RoBERTa model on AWS serving 90k requests/day at 45ms p95.
• Reduced inference costs by 35% with TensorRT.
ML Engineer | DataWorks (Jul 2018 - Dec 2020)
• Developed PyTorch pipelines handling 10M records."""
    c_c2 = parser.parse(text_c2.encode("utf-8"), "C2.txt")
    res_c2 = council.evaluate_candidate_council(c_c2, jd_ml)["executive_consensus"]
    fl_c2 = [f["code"] for f in res_c2["red_flags"]]
    print(f"Probe C2: No education, no phone/socials -> Before: STRONG_HIRE (92.6) | After: {res_c2['verdict']} ({res_c2['final_score']}) | Flags: {fl_c2}")

if __name__ == "__main__":
    run_100_benchmark()
    run_adversarial_probes()

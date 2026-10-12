import csv
import json
import os
import random

target_dir = os.path.join("data", "synthetic_resumes_100")
os.makedirs(target_dir, exist_ok=True)

# 8 Engineering Roles with target skills, companies, and projects
ROLES_DEF = [
    {
        "role": "Senior Machine Learning Engineer",
        "short": "Senior_ML",
        "skills": ["Python", "PyTorch", "TensorFlow", "FastAPI", "Docker", "AWS", "Hugging Face", "MLOps", "Scikit-Learn", "Pandas"],
        "min_years": 4.5,
        "sal_usd": "$165k - $190k",
        "sal_inr": "35 - 42 LPA",
        "level": "L5 - Senior Staff ML Engineer",
        "metrics": [
            "Served 95,000 requests/day at p95 latency under 68ms on AWS ECS.",
            "Cut model inference costs by 34% via TensorRT INT8 quantization.",
            "Raised F1 classification accuracy from 0.79 to 0.91 using fine-tuned RoBERTa.",
            "Built distributed PyTorch DDP pipelines across 8 NVIDIA A100 GPUs."
        ]
    },
    {
        "role": "Cloud DevOps & Site Reliability Lead",
        "short": "Cloud_DevOps",
        "skills": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "Linux", "Prometheus", "Grafana", "Ansible", "Helm"],
        "min_years": 5.0,
        "sal_usd": "$150k - $180k",
        "sal_inr": "30 - 38 LPA",
        "level": "L5 - Lead SRE",
        "metrics": [
            "Maintained 99.99% system availability across 4 AWS multi-region Kubernetes clusters.",
            "Reduced mean-time-to-recovery (MTTR) from 45 minutes to 6 minutes using automated runbooks.",
            "Provisioned 120+ cloud resources declaratively using Terraform and GitOps with ArgoCD.",
            "Optimized spot-instance provisioning reducing cloud spend by $24,000/month."
        ]
    },
    {
        "role": "Full-Stack AI Application Engineer",
        "short": "FullStack_AI",
        "skills": ["React", "TypeScript", "Python", "FastAPI", "Next.js", "LangChain", "PostgreSQL", "Docker", "TailwindCSS", "Redis"],
        "min_years": 3.5,
        "sal_usd": "$140k - $170k",
        "sal_inr": "28 - 36 LPA",
        "level": "L4 - Senior Full-Stack AI",
        "metrics": [
            "Delivered reactive AI dashboard handling 40,000 monthly active users with sub-100ms TTFT.",
            "Engineered streaming Server-Sent Events (SSE) FastAPI pipelines with token buffering.",
            "Achieved 95% unit test code coverage across React frontend and Python API layer.",
            "Integrated multi-agent tool execution workflows utilizing LangChain and Redis cache."
        ]
    },
    {
        "role": "Data Platform & Distributed Systems Engineer",
        "short": "Data_Platform",
        "skills": ["Python", "Apache Spark", "Kafka", "SQL", "Snowflake", "AWS S3", "Airflow", "PostgreSQL", "Pandas", "Docker"],
        "min_years": 4.0,
        "sal_usd": "$145k - $175k",
        "sal_inr": "29 - 37 LPA",
        "level": "L4 - Senior Data Platform",
        "metrics": [
            "Processed 2.4 TB of daily telemetry logs through real-time Kafka and Apache Spark streaming.",
            "Reduced query execution time by 58% on Snowflake via partition pruning and cluster keys.",
            "Built automated data quality assertion gates in Airflow preventing corrupt ingestion.",
            "Constructed lakehouse pipelines on AWS S3 with parquet compression saving 40TB storage."
        ]
    },
    {
        "role": "Backend Microservices Architect",
        "short": "Backend_Architect",
        "skills": ["Golang", "Python", "Microservices", "gRPC", "Docker", "Kubernetes", "PostgreSQL", "Redis", "Kafka", "Linux"],
        "min_years": 6.0,
        "sal_usd": "$170k - $205k",
        "sal_inr": "38 - 46 LPA",
        "level": "L6 - Principal Architect",
        "metrics": [
            "Architected event-driven microservices processing 180,000 requests/minute with zero data loss.",
            "Transitioned monolithic legacy API to 14 gRPC microservices reducing p99 latency by 72ms.",
            "Implemented distributed saga transactions and idempotent consumers with Kafka and Redis.",
            "Conducted architectural design reviews across 5 distributed backend engineering squads."
        ]
    },
    {
        "role": "AI Safety, Governance & Alignment Auditor",
        "short": "AI_Safety",
        "skills": ["AI Safety", "Model Evaluation", "Red Teaming", "Bias Auditing", "Python", "LLM Evaluation", "PyTorch", "Explainable AI", "Fairness Metrics", "ISO 42001"],
        "min_years": 3.5,
        "sal_usd": "$155k - $185k",
        "sal_inr": "32 - 40 LPA",
        "level": "L5 - Staff AI Safety Auditor",
        "metrics": [
            "Conducted adversarial red teaming on 14 foundation models intercepting 180+ jailbreaks.",
            "Standardized fairness and demographic parity testing framework compliant with ISO 42001.",
            "Developed automated bias evaluation test harnesses using counterfactual prompting.",
            "Formulated corporate model release criteria adopted across 4 business units."
        ]
    },
    {
        "role": "Senior Business Intelligence & Data Analyst",
        "short": "BI_Analyst",
        "skills": ["SQL", "Python", "Tableau", "Power BI", "Pandas", "NumPy", "Business Intelligence", "Data Warehousing", "Statistical Analysis", "A/B Testing"],
        "min_years": 3.0,
        "sal_usd": "$115k - $140k",
        "sal_inr": "20 - 26 LPA",
        "level": "L3 - Senior Analyst",
        "metrics": [
            "Created executive revenue dashboard tracking $45M ARR across 12 product lines in Tableau.",
            "Formulated statistical A/B test methodologies identifying 14% lift in user onboarding funnel.",
            "Automated weekly cohort churn reports using complex SQL window functions and Pandas.",
            "Trained 35 cross-functional business stakeholders on self-serve BI reporting suites."
        ]
    },
    {
        "role": "Python Backend & API Developer",
        "short": "Python_Backend",
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Celery", "Docker", "Linux", "Git", "REST API", "PyTest"],
        "min_years": 2.5,
        "sal_usd": "$125k - $150k",
        "sal_inr": "22 - 30 LPA",
        "level": "L3 - Backend Engineer",
        "metrics": [
            "Constructed asynchronous REST API endpoints with FastAPI handling 45,000 daily queries.",
            "Implemented asynchronous background task queues with Celery and Redis reducing sync blocks.",
            "Maintained 92% PyTest test coverage and automated linting in GitHub Actions CI.",
            "Optimized PostgreSQL queries through proper indexing and connection pooling with asyncpg."
        ]
    }
]

first_names = [
    "Aakash", "Ananya", "Arun", "Bhavna", "Chetan", "Deepa", "Dev", "Divya",
    "Gaurav", "Harsh", "Ishaan", "Jaya", "Karan", "Kavya", "Kunal", "Lakshmi",
    "Manish", "Meera", "Mohan", "Nandini", "Nikhil", "Omkar", "Padma", "Pooja",
    "Pranav", "Preethi", "Radhika", "Rahul", "Rajat", "Ritika", "Rohan", "Sanjana",
    "Shreya", "Siddharth", "Suresh", "Swati", "Tanmay", "Tara", "Uday", "Varun",
    "Vidya", "Vikram", "Waseem", "Yash", "Zoya", "Aditi", "Brijesh", "Chirag",
    "Farhan", "Hemant"
]
last_names = [
    "Agarwal", "Ahmed", "Banerjee", "Bhat", "Bose", "Chatterjee", "Das", "Deshmukh",
    "Dsouza", "Fernandes", "Ghosh", "Gowda", "Gupta", "Hegde", "Iyer", "Jain",
    "Joshi", "Kamath", "Kapoor", "Khan", "Krishnan", "Kulkarni", "Lobo", "Malhotra",
    "Mathur", "Menon", "Mishra", "Mukherjee", "Naidu", "Nambiar", "Nayak", "Oberoi",
    "Pandey", "Patel", "Patil", "Pillai", "Prabhu", "Raman", "Rastogi", "Reddy",
    "Saxena", "Sethi", "Shetty", "Singh", "Singhania", "Sinha", "Thakur", "Trivedi",
    "Varma", "Yadav"
]

categories = [
    ("Gold Standard", 0.20),
    ("Lateral Switcher", 0.45),
    ("Keyword Stuffing", 0.20),
    ("Corrupt Layout", 0.10),
    ("Early Career Fresher", 0.05)
]

candidates_100 = []
manifest_rows = []

random.seed(42)

for i in range(100):
    idx_num = i + 1
    role_def = ROLES_DEF[i % len(ROLES_DEF)]
    fn = first_names[i % len(first_names)]
    ln = last_names[(i * 3 + 7) % len(last_names)]
    cand_name = f"{fn} {ln}"
    gh_handle = f"{fn.lower()}-{ln.lower()}"
    
    # Determine category
    r_val = (i % 100) / 100.0
    if r_val < 0.20:
        cat = "Gold Standard"
        exp_verdict = "STRONG_HIRE"
        red_flags = []
        tenure = round(role_def["min_years"] + (i % 4) * 0.8, 1)
        skills_subset = role_def["skills"][:8]
        evidence = role_def["metrics"][i % len(role_def["metrics"])]
        match_score = round(86.0 + (i % 8) * 1.4, 1)
        ats_score = 92 + (i % 7)
        council_score = round(88.0 + (i % 8) * 1.3, 1)
        risk = "LOW"
    elif r_val < 0.65:
        cat = "Lateral Switcher"
        exp_verdict = "LEAN_HIRE"
        red_flags = ["REQUIRED_SKILLS_MISSING"]
        tenure = round(max(2.0, role_def["min_years"] - 1.2 + (i % 3) * 0.5), 1)
        skills_subset = role_def["skills"][:4] + ["Git", "Linux"]
        evidence = f"Maintained production {skills_subset[0]} and {skills_subset[1]} pipelines. Adjacent skills transitioning to {role_def['role']}."
        match_score = round(62.0 + (i % 10) * 1.3, 1)
        ats_score = 78 + (i % 12)
        council_score = round(68.0 + (i % 8) * 1.1, 1)
        risk = "LOW"
    elif r_val < 0.85:
        cat = "Keyword Stuffing"
        exp_verdict = "REJECT"
        red_flags = ["EXPERIENCE_DEFICIT", "SKILL_STUFFING", "UNVERIFIED_SKILL_CLAIMS"]
        tenure = 0.4
        skills_subset = role_def["skills"] + ["Quantum Computing", "Blockchain", "CUDA", "Kubernetes Master", "Solidity", "Rust", "Hadoop"]
        evidence = f"Claimed mastery across {len(skills_subset)} enterprise technologies in 4 months total tenure; untouched forks."
        match_score = round(38.0 + (i % 8) * 1.2, 1)
        ats_score = 52 + (i % 10)
        council_score = round(42.0 + (i % 6) * 1.1, 1)
        risk = "HIGH"
    elif r_val < 0.95:
        cat = "Corrupt Layout"
        exp_verdict = "REJECT"
        red_flags = ["FORMAT_CORRUPT", "NO_QUANTIFIED_IMPACT"]
        tenure = 2.0
        skills_subset = role_def["skills"][:2]
        evidence = "Corrupt layout: overlapping timelines, unparseable tables and missing section headers."
        match_score = round(28.0 + (i % 6) * 1.2, 1)
        ats_score = 24 + (i % 8)
        council_score = round(32.0 + (i % 5) * 1.1, 1)
        risk = "MEDIUM"
    else:
        cat = "Early Career Fresher"
        exp_verdict = "REJECT"
        red_flags = ["EXPERIENCE_DEFICIT", "REQUIRED_SKILLS_MISSING"]
        tenure = 0.5
        skills_subset = ["Python", "Pandas"]
        evidence = "Academic capstone projects only; missing 2+ years required production tenure."
        match_score = round(46.0 + (i % 5) * 1.1, 1)
        ats_score = 68 + (i % 6)
        council_score = round(44.0 + (i % 4) * 1.1, 1)
        risk = "LOW"

    filename = f"{idx_num:03d}_{cat.replace(' ', '_')}_{role_def['short']}_{fn}_{ln}.txt"
    filepath = os.path.join(target_dir, filename)

    # Generate realistic resume text file
    content = f"""{cand_name}
Email: {fn.lower()}.{ln.lower()}@domain.com | Phone: +91 {random.randint(90000, 99999)} {random.randint(10000, 99999)} | Location: Bengaluru, India
LinkedIn: https://linkedin.com/in/{gh_handle} | GitHub: https://github.com/{gh_handle}

PROFESSIONAL SUMMARY
{role_def['role']} with {tenure} years of experience. Focus in {', '.join(skills_subset[:5])}. {evidence}

TECHNICAL SKILLS
{', '.join(skills_subset)}

WORK EXPERIENCE
{role_def['role']} | TechCorp Enterprise Systems (2022 - Present)
• {evidence}
• Orchestrated continuous deployment and monitoring with CI/CD and Docker.
• Mentored junior engineers and improved automated test coverage.

EDUCATION
B.Tech / B.E. in Computer Science & Engineering
VTU University | Graduated 2021
"""

    with open(filepath, "w", encoding="utf-8") as f_out:
        f_out.write(content)

    manifest_rows.append({
        "file": filename,
        "candidate": cand_name,
        "role": role_def["role"],
        "category": cat,
        "stated_tenure_years": tenure,
        "github_handle": gh_handle,
        "expected_verdict": exp_verdict,
        "expected_red_flags": "; ".join(red_flags) or "none"
    })

    cand_obj = {
        "id": f"CAN-100-{idx_num:03d}",
        "name": cand_name,
        "anonymizedId": f"Candidate #{idx_num:03d} ({cat})",
        "fileName": filename,
        "title": role_def["role"],
        "category": cat,
        "experienceYears": tenure,
        "matchScore": match_score,
        "atsScore": ats_score,
        "councilScore": council_score,
        "verdict": exp_verdict,
        "verdictType": "positive" if exp_verdict == "STRONG_HIRE" else ("neutral" if exp_verdict == "LEAN_HIRE" else "negative"),
        "redFlags": red_flags,
        "matchedSkills": skills_subset[:6],
        "partiallyMatchedSkills": [],
        "missingSkills": [s for s in role_def["skills"] if s not in skills_subset][:4],
        "salaryRange": role_def["sal_usd"],
        "salaryInr": role_def["sal_inr"],
        "level": role_def["level"],
        "bandPosPct": int(match_score * 0.85),
        "evidenceSnippet": evidence,
        "github": {
            "username": gh_handle,
            "score": int(match_score * 0.94),
            "risk": risk,
            "reposAnalyzed": 14 if risk == "LOW" else 5,
            "authenticRepos": 13 if risk == "LOW" else (1 if risk == "HIGH" else 4),
            "forksCount": 1 if risk == "LOW" else 10,
            "archSignals": 7 if risk == "LOW" else 1,
            "quantifiedMetrics": 5 if risk == "LOW" else 0,
            "languages": ["Python (70%)", "Shell (30%)"]
        },
        "council": {
            "techLead": {"score": int(council_score * 0.95), "feedback": f"Category: {cat}. Evaluated against {role_def['role']} baseline."},
            "culture": {"score": 82 if risk == "LOW" else 45, "feedback": f"GitHub analysis for {gh_handle}."},
            "fairAuditor": {"score": 98 if not red_flags else 92, "feedback": f"Audit verification. Flags: {', '.join(red_flags) or 'Clean'}."},
            "seniorityComp": {"score": int(council_score * 0.9), "feedback": f"Compensation aligned with {role_def['sal_usd']}."}
        },
        "debateSnippet": [
            {"agent": "Tech Lead", "text": f"Evidence: {evidence}"},
            {"agent": "Fair Auditor", "text": f"Flags: {', '.join(red_flags) or 'Zero flags.'}"}
        ],
        "interviewQuestions": [
            {"q": f"Can you walk us through: \"{evidence[:60]}...\"?", "type": "Technical Verification", "lookFor": "System architecture and measurable impact."}
        ]
    }
    candidates_100.append(cand_obj)

# Sort candidates_100 by matchScore descending and assign ranks
candidates_100.sort(key=lambda x: x["matchScore"], reverse=True)
for rank_idx, c in enumerate(candidates_100):
    c["rank"] = rank_idx + 1

# Write manifest.csv into data/synthetic_resumes_100/
with open(os.path.join(target_dir, "manifest.csv"), "w", encoding="utf-8", newline="") as f_man:
    writer = csv.DictWriter(f_man, fieldnames=list(manifest_rows[0].keys()))
    writer.writeheader()
    writer.writerows(manifest_rows)

# Write frontend/src/data/synthetic_100.json
with open("frontend/src/data/synthetic_100.json", "w", encoding="utf-8") as f_json:
    json.dump(candidates_100, f_json, indent=2)

print(f"Generated 100 synthetic resumes in {target_dir} and saved synthetic_100.json!")
print("Top 3 Candidates in 100-batch:")
for c in candidates_100[:3]:
    print(f"Rank #{c['rank']}: {c['name']} ({c['title']} • {c['matchScore']}%)")

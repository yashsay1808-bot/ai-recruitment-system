import json
import re

# Read App.jsx lines 67-629 to get the original 12 candidates exactly
with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Extract CANDIDATES_DATA block
start_idx = content.find("const CANDIDATES_DATA = [")
end_idx = content.find("const PROMPT_PILLS = [")
cand_code = content[start_idx:end_idx].strip()
# remove trailing semicolon if any
if cand_code.endswith(";"):
    cand_code = cand_code[:-1].strip()

# Let's inspect the original 12 candidates code
original_12_code = cand_code.replace("const CANDIDATES_DATA = [", "").rstrip("]")

# 38 additional realistic candidates
additional_38 = [
    {
        "id": "CAN-013",
        "name": "Aarav Mehta",
        "anonymizedId": "Candidate #013",
        "fileName": "Synthetic_013_Aarav_Mehta_ML_Lead.txt",
        "title": "Lead ML Systems Engineer",
        "experienceYears": 5.2,
        "matchScore": 86.4,
        "atsScore": 98,
        "councilScore": 89.2,
        "verdict": "STRONG_HIRE",
        "verdictType": "positive",
        "redFlags": [],
        "matchedSkills": ["Python", "PyTorch", "FastAPI", "Docker", "AWS", "NLP", "Scikit-Learn"],
        "partiallyMatchedSkills": [],
        "missingSkills": [],
        "salaryRange": "$170k - $195k",
        "salaryInr": "36 - 44 LPA",
        "level": "L5 - Lead ML Systems",
        "bandPosPct": 78,
        "evidenceSnippet": "Engineered real-time PyTorch inference microservices on AWS ECS serving 80k req/day with p95 <65ms.",
        "github": {"username": "aarav-ml-core", "score": 92, "risk": "LOW", "reposAnalyzed": 14, "authenticRepos": 13, "forksCount": 1, "archSignals": 8, "quantifiedMetrics": 7, "languages": ["Python (80%)", "C++ (15%)", "CUDA (5%)"]},
        "council": {
            "techLead": {"score": 91, "feedback": "Sub-65ms p95 latency on AWS ECS verified; robust PyTorch inference architecture."},
            "culture": {"score": 85, "feedback": "Mentored 4 junior engineers on MLOps best practices."},
            "fairAuditor": {"score": 99, "feedback": "Zero bias detected; clean verifiable accomplishments."},
            "seniorityComp": {"score": 94, "feedback": "Solid L5 Lead candidate; salary target within budget band."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": "Sub-65ms latency at 80k requests/day is verified via AWS CloudWatch logs."}],
        "interviewQuestions": [{"q": "How do you manage PyTorch memory fragmentation during heavy concurrent inference bursts?", "type": "Systems Performance", "lookFor": "torch.cuda.empty_cache, memory pinning, pre-allocated tensor buffers."}]
    },
    {
        "id": "CAN-014",
        "name": "Diya Sharma",
        "anonymizedId": "Candidate #014",
        "fileName": "Synthetic_014_Diya_Sharma_MLOps.txt",
        "title": "MLOps & Inference Engineer",
        "experienceYears": 3.8,
        "matchScore": 83.7,
        "atsScore": 95,
        "councilScore": 84.1,
        "verdict": "STRONG_HIRE",
        "verdictType": "positive",
        "redFlags": [],
        "matchedSkills": ["Python", "PyTorch", "FastAPI", "Docker", "Kubernetes", "AWS", "CI/CD"],
        "partiallyMatchedSkills": [],
        "missingSkills": [],
        "salaryRange": "$155k - $180k",
        "salaryInr": "32 - 38 LPA",
        "level": "L4/L5 - Senior MLOps",
        "bandPosPct": 65,
        "evidenceSnippet": "Containerized PyTorch models with Docker and deployed across Kubernetes with automated drift monitoring.",
        "github": {"username": "diya-mlops", "score": 89, "risk": "LOW", "reposAnalyzed": 10, "authenticRepos": 9, "forksCount": 1, "archSignals": 6, "quantifiedMetrics": 5, "languages": ["Python (75%)", "YAML (15%)", "Shell (10%)"]},
        "council": {
            "techLead": {"score": 86, "feedback": "Great infrastructure tooling for continuous model evaluation."},
            "culture": {"score": 82, "feedback": "Strong documentation and CI/CD automation discipline."},
            "fairAuditor": {"score": 98, "feedback": "Objective evaluation pass."},
            "seniorityComp": {"score": 88, "feedback": "Senior MLOps leveling verified."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": "Excellent Kubernetes deployment automation for PyTorch models."}],
        "interviewQuestions": [{"q": "How do you handle zero-downtime model rollouts when updating PyTorch weights in Kubernetes?", "type": "MLOps Lifecycle", "lookFor": "Readiness probes, canary deployments, Istio traffic splitting."}]
    },
    {
        "id": "CAN-015",
        "name": "Suresh Nambiar",
        "anonymizedId": "Candidate #015",
        "fileName": "Synthetic_015_Suresh_Nambiar_Architect.txt",
        "title": "Microservices Architect",
        "experienceYears": 6.5,
        "matchScore": 87.8,
        "atsScore": 97,
        "councilScore": 89.5,
        "verdict": "STRONG_HIRE",
        "verdictType": "positive",
        "redFlags": [],
        "matchedSkills": ["Python", "Docker", "AWS", "REST API", "CI/CD", "FastAPI"],
        "partiallyMatchedSkills": ["PyTorch (via ONNX runtime: 0.7 credit)"],
        "missingSkills": [],
        "salaryRange": "$180k - $210k",
        "salaryInr": "40 - 48 LPA",
        "level": "L6 - Principal Architect",
        "bandPosPct": 85,
        "evidenceSnippet": "Designed fault-tolerant event-driven microservices architecture handling 200,000 requests per minute with gRPC.",
        "github": {"username": "suresh-arch", "score": 95, "risk": "LOW", "reposAnalyzed": 18, "authenticRepos": 17, "forksCount": 1, "archSignals": 10, "quantifiedMetrics": 8, "languages": ["Go (50%)", "Python (35%)", "Rust (15%)"]},
        "council": {
            "techLead": {"score": 94, "feedback": "Exceptional system design and high-scale concurrency experience."},
            "culture": {"score": 86, "feedback": "Seasoned technical leader."},
            "fairAuditor": {"score": 99, "feedback": "Objective metrics verified across 18 public code repositories."},
            "seniorityComp": {"score": 92, "feedback": "Principal level compensation band."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": "Handles 200k req/min at scale. Strong architectural anchor."}],
        "interviewQuestions": [{"q": "How do you maintain distributed consistency across event-driven microservices?", "type": "System Design", "lookFor": "Saga pattern, transactional outbox, idempotent consumers."}]
    },
    {
        "id": "CAN-016",
        "name": "Pooja Sundaram",
        "anonymizedId": "Candidate #016",
        "fileName": "Synthetic_016_Pooja_Sundaram_Data.txt",
        "title": "Data Platform Engineer",
        "experienceYears": 4.1,
        "matchScore": 81.3,
        "atsScore": 93,
        "councilScore": 82.5,
        "verdict": "STRONG_HIRE",
        "verdictType": "positive",
        "redFlags": [],
        "matchedSkills": ["Python", "Docker", "AWS", "Pandas", "NumPy", "Git", "REST API"],
        "partiallyMatchedSkills": [],
        "missingSkills": ["PyTorch"],
        "salaryRange": "$150k - $175k",
        "salaryInr": "30 - 37 LPA",
        "level": "L4 - Senior Data Platform",
        "bandPosPct": 62,
        "evidenceSnippet": "Constructed petabyte-scale streaming data pipelines on AWS with Kafka and Apache Spark.",
        "github": {"username": "pooja-data", "score": 88, "risk": "LOW", "reposAnalyzed": 9, "authenticRepos": 9, "forksCount": 0, "archSignals": 6, "quantifiedMetrics": 5, "languages": ["Python (65%)", "Scala (25%)", "SQL (10%)"]},
        "council": {
            "techLead": {"score": 82, "feedback": "Strong distributed data processing skills; Spark pipelines well-optimized."},
            "culture": {"score": 84, "feedback": "Clear analytical documentation and collaborative spirit."},
            "fairAuditor": {"score": 98, "feedback": "Fair audit passed."},
            "seniorityComp": {"score": 86, "feedback": "Compensation aligns with L4 senior data engineering band."}
        },
        "debateSnippet": [{"agent": "Culture", "text": "Demonstrates excellent code quality and pipeline unit testing coverage."}],
        "interviewQuestions": [{"q": "How do you prevent data skew when partitioning large distributed streaming datasets in Spark?", "type": "Distributed Computing", "lookFor": "Salting keys, broadcast joins, repartitioning strategies."}]
    },
    {
        "id": "CAN-017",
        "name": "Harish Patel",
        "anonymizedId": "Candidate #017",
        "fileName": "Synthetic_017_Harish_Patel_FullStack.txt",
        "title": "Full-Stack AI Application Lead",
        "experienceYears": 4.2,
        "matchScore": 80.4,
        "atsScore": 92,
        "councilScore": 81.6,
        "verdict": "STRONG_HIRE",
        "verdictType": "positive",
        "redFlags": [],
        "matchedSkills": ["Python", "FastAPI", "Docker", "Git", "REST API"],
        "partiallyMatchedSkills": [],
        "missingSkills": ["PyTorch"],
        "salaryRange": "$148k - $172k",
        "salaryInr": "30 - 36 LPA",
        "level": "L4 - Lead FullStack AI",
        "bandPosPct": 60,
        "evidenceSnippet": "Built reactive AI dashboards with Next.js and FastAPI processing 50k monthly agent workflows.",
        "github": {"username": "harish-fs", "score": 86, "risk": "LOW", "reposAnalyzed": 12, "authenticRepos": 11, "forksCount": 1, "archSignals": 6, "quantifiedMetrics": 5, "languages": ["TypeScript (55%)", "Python (35%)", "HTML (10%)"]},
        "council": {
            "techLead": {"score": 81, "feedback": "Great full-stack delivery; API design conforms to clean REST principles."},
            "culture": {"score": 85, "feedback": "Strong product mindset and UX empathy."},
            "fairAuditor": {"score": 97, "feedback": "Valid credentials verified."},
            "seniorityComp": {"score": 84, "feedback": "Standard L4 full-stack package."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": "Solid API architecture and clean state management in Next.js."}],
        "interviewQuestions": [{"q": "How do you stream LLM token outputs to web clients with sub-100ms time-to-first-token?", "type": "Fullstack Architecture", "lookFor": "Server-Sent Events (SSE), HTTP/2 streaming, generator response loops."}]
    },
    {
        "id": "CAN-018",
        "name": "Tanvi Joshi",
        "anonymizedId": "Candidate #018",
        "fileName": "Synthetic_018_Tanvi_Joshi_Safety.txt",
        "title": "AI Safety & Governance Auditor",
        "experienceYears": 3.6,
        "matchScore": 79.1,
        "atsScore": 94,
        "councilScore": 82.0,
        "verdict": "STRONG_HIRE",
        "verdictType": "positive",
        "redFlags": [],
        "matchedSkills": ["Python", "PyTorch", "NLP", "Scikit-Learn", "Git"],
        "partiallyMatchedSkills": [],
        "missingSkills": ["Docker", "AWS"],
        "salaryRange": "$152k - $178k",
        "salaryInr": "31 - 38 LPA",
        "level": "L4 - AI Safety Auditor",
        "bandPosPct": 58,
        "evidenceSnippet": "Developed fairness and bias benchmark test harnesses verifying LLM alignment against ISO 42001 standard.",
        "github": {"username": "tanvi-safety", "score": 89, "risk": "LOW", "reposAnalyzed": 7, "authenticRepos": 7, "forksCount": 0, "archSignals": 5, "quantifiedMetrics": 4, "languages": ["Python (85%)", "R (15%)"]},
        "council": {
            "techLead": {"score": 80, "feedback": "Rigorous statistical validation and model alignment testing methodology."},
            "culture": {"score": 87, "feedback": "High ethical standards and governance communication."},
            "fairAuditor": {"score": 100, "feedback": "Outstanding alignment on bias mitigation metrics."},
            "seniorityComp": {"score": 85, "feedback": "Specialized AI Safety compensation tier."}
        },
        "debateSnippet": [{"agent": "Fair Auditor", "text": "100/100 alignment audit: candidate built open-source bias testing suites."}],
        "interviewQuestions": [{"q": "How do you detect subtle demographic bias in black-box LLM embedding outputs?", "type": "AI Safety", "lookFor": "WEAT/SEAT test suites, cosine distance disparities, counterfactual evaluation."}]
    },
    {
        "id": "CAN-019",
        "name": "Kiran Venkatesh",
        "anonymizedId": "Candidate #019",
        "fileName": "Synthetic_019_Kiran_Venkatesh_Lateral.txt",
        "title": "Senior Backend & ML Engineer",
        "experienceYears": 4.5,
        "matchScore": 78.5,
        "atsScore": 91,
        "councilScore": 79.3,
        "verdict": "LEAN_HIRE",
        "verdictType": "neutral",
        "redFlags": [],
        "matchedSkills": ["Python", "FastAPI", "Docker", "AWS", "Git", "REST API"],
        "partiallyMatchedSkills": ["PyTorch (via personal projects)"],
        "missingSkills": ["NLP"],
        "salaryRange": "$150k - $175k",
        "salaryInr": "30 - 36 LPA",
        "level": "L4 - Senior Backend/ML",
        "bandPosPct": 55,
        "evidenceSnippet": "Architected asynchronous FastAPI microservices on AWS handling 150k transactions/day with redis caching.",
        "github": {"username": "kiran-backend", "score": 85, "risk": "LOW", "reposAnalyzed": 11, "authenticRepos": 10, "forksCount": 1, "archSignals": 5, "quantifiedMetrics": 4, "languages": ["Python (70%)", "SQL (20%)", "Go (10%)"]},
        "council": {
            "techLead": {"score": 78, "feedback": "Solid backend microservices, lateral transition to ML is achievable."},
            "culture": {"score": 82, "feedback": "Collaborative, strong test coverage."},
            "fairAuditor": {"score": 97, "feedback": "Clean background verification."},
            "seniorityComp": {"score": 80, "feedback": "Senior backend compensation aligned."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": "Reliable backend throughput: 150k daily transactions on AWS."}],
        "interviewQuestions": [{"q": "How do you structure database connection pooling in high-concurrency FastAPI services?", "type": "System Performance", "lookFor": "asyncpg pool size, max_overflow, lifespan events."}]
    },
    {
        "id": "CAN-020",
        "name": "Neha Deshmukh",
        "anonymizedId": "Candidate #020",
        "fileName": "Synthetic_020_Neha_Deshmukh_NLP.txt",
        "title": "NLP & Transformer Specialist",
        "experienceYears": 3.2,
        "matchScore": 76.9,
        "atsScore": 90,
        "councilScore": 77.8,
        "verdict": "LEAN_HIRE",
        "verdictType": "neutral",
        "redFlags": [],
        "matchedSkills": ["Python", "PyTorch", "Hugging Face", "NLP", "FastAPI", "Docker", "AWS"],
        "partiallyMatchedSkills": [],
        "missingSkills": ["Scikit-Learn"],
        "salaryRange": "$145k - $170k",
        "salaryInr": "29 - 35 LPA",
        "level": "L4 - Senior NLP Engineer",
        "bandPosPct": 54,
        "evidenceSnippet": "Fine-tuned Hugging Face transformer models for automated document triaging with 93% accuracy.",
        "github": {"username": "neha-nlp", "score": 87, "risk": "LOW", "reposAnalyzed": 8, "authenticRepos": 8, "forksCount": 0, "archSignals": 4, "quantifiedMetrics": 4, "languages": ["Python (88%)", "Jupyter (12%)"]},
        "council": {
            "techLead": {"score": 79, "feedback": "Good transformer fine-tuning chops, needs more distributed systems exposure."},
            "culture": {"score": 81, "feedback": "Clear written documentation."},
            "fairAuditor": {"score": 98, "feedback": "Clean screening."},
            "seniorityComp": {"score": 79, "feedback": "L4 NLP offer appropriate."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": "Fine-tuned transformer models with 93% F1 score."}],
        "interviewQuestions": [{"q": "How do you mitigate catastrophic forgetting when fine-tuning transformer models on domain data?", "type": "Deep Learning", "lookFor": "LoRA, PEFT, low learning rates, replay buffers."}]
    }
]

# Generate more candidates to reach 50 total candidates
role_templates = [
    ("ML Engineer", ["Python", "PyTorch", "FastAPI", "Docker", "AWS"], "$140k - $165k", "28 - 34 LPA", "L4 - ML Systems"),
    ("Cloud DevOps", ["Kubernetes", "Docker", "AWS", "CI/CD", "Linux"], "$135k - $160k", "26 - 32 LPA", "L4 - DevOps Specialist"),
    ("FullStack AI", ["React", "Python", "FastAPI", "Docker", "PostgreSQL"], "$130k - $155k", "25 - 31 LPA", "L4 - Full-Stack Developer"),
    ("Data Engineer", ["Python", "SQL", "Pandas", "AWS", "Spark"], "$135k - $160k", "26 - 32 LPA", "L4 - Data Engineer"),
    ("Backend Dev", ["Python", "FastAPI", "Docker", "PostgreSQL", "Git"], "$125k - $145k", "22 - 28 LPA", "L3 - Backend Engineer"),
    ("Data Analyst", ["Python", "Pandas", "SQL", "Tableau", "NumPy"], "$110k - $130k", "18 - 24 LPA", "L3 - Data Analyst")
]

first_names = [
    "Aditi", "Bhavya", "Chetan", "Deepak", "Esha", "Farhan", "Gaurav", "Himani",
    "Ishaan", "Jaya", "Kalyan", "Lavanya", "Manish", "Nandini", "Omkar", "Pranav",
    "Radha", "Sahil", "Tara", "Umesh", "Varun", "Yash", "Zoya", "Ravi", "Meera",
    "Abhinav", "Shalini", "Girish", "Divya", "Ankit"
]
last_names = [
    "Bhat", "Chopra", "Desai", "Goyal", "Hegde", "Iyengar", "Jain", "Kapoor",
    "Malhotra", "Natarajan", "Pandey", "Rangan", "Sen", "Trivedi", "Varma", "Yadav"
]

idx = 21
for fn in first_names:
    if idx > 50:
        break
    ln = last_names[(idx * 3) % len(last_names)]
    full_name = f"{fn} {ln}"
    role_info = role_templates[(idx) % len(role_templates)]
    
    # Decide verdict & red flag status
    is_flagged = (idx % 4 == 0) or (idx % 7 == 0)
    if is_flagged:
        verdict = "REJECT"
        verdict_type = "negative"
        flags = ["REQUIRED_SKILLS_MISSING"] if idx % 2 == 0 else ["EXPERIENCE_DEFICIT", "REQUIRED_SKILLS_MISSING"]
        match_score = round(35.0 + (idx % 15) * 1.2, 1)
        ats_score = 50 + (idx % 25)
        council_score = round(40.0 + (idx % 18) * 1.1, 1)
        risk = "HIGH" if "EXPERIENCE_DEFICIT" in flags else "MEDIUM"
        forks = 8 if risk == "HIGH" else 3
        auth_repos = 2 if risk == "HIGH" else 4
    elif idx % 3 == 0:
        verdict = "LEAN_HIRE"
        verdict_type = "neutral"
        flags = []
        match_score = round(62.0 + (idx % 12) * 1.3, 1)
        ats_score = 75 + (idx % 15)
        council_score = round(68.0 + (idx % 10) * 1.2, 1)
        risk = "LOW"
        forks = 1
        auth_repos = 6 + (idx % 4)
    else:
        score_est = 75.0 + (idx % 10) * 1.1
        verdict = "STRONG_HIRE" if score_est > 80 else "LEAN_HIRE"
        verdict_type = "positive" if verdict == "STRONG_HIRE" else "neutral"
        flags = []
        match_score = round(72.0 + (idx % 15) * 1.1, 1)
        ats_score = 85 + (idx % 12)
        council_score = round(75.0 + (idx % 12) * 1.1, 1)
        risk = "LOW"
        forks = 0
        auth_repos = 8 + (idx % 5)

    exp_years = round(1.5 + (idx % 6) * 0.8, 1)
    if "EXPERIENCE_DEFICIT" in flags:
        exp_years = 0.5

    cand_obj = {
        "id": f"CAN-{idx:03d}",
        "name": full_name,
        "anonymizedId": f"Candidate #{idx:03d}",
        "fileName": f"Synthetic_{idx:03d}_{fn}_{ln}_{role_info[0].replace(' ', '_')}.txt",
        "title": f"Senior {role_info[0]}" if exp_years >= 3.5 else f"{role_info[0]} Specialist",
        "experienceYears": exp_years,
        "matchScore": match_score,
        "atsScore": ats_score,
        "councilScore": council_score,
        "verdict": verdict,
        "verdictType": verdict_type,
        "redFlags": flags,
        "matchedSkills": role_info[1][:3] if not is_flagged else role_info[1][:1],
        "partiallyMatchedSkills": [],
        "missingSkills": ["PyTorch", "Kubernetes"] if is_flagged else [],
        "salaryRange": role_info[2],
        "salaryInr": role_info[3],
        "level": role_info[4],
        "bandPosPct": int(match_score * 0.85),
        "evidenceSnippet": f"Delivered production {role_info[1][0]} and {role_info[1][1]} workflows under high availability requirements.",
        "github": {
            "username": f"{fn.lower()}-{ln.lower()}",
            "score": int(match_score * 0.95),
            "risk": risk,
            "reposAnalyzed": auth_repos + forks,
            "authenticRepos": auth_repos,
            "forksCount": forks,
            "archSignals": 4,
            "quantifiedMetrics": 3,
            "languages": [f"{role_info[1][0]} (70%)", "Shell (30%)"]
        },
        "council": {
            "techLead": {"score": int(council_score * 0.95), "feedback": f"Evaluated against {role_info[0]} core competency requirements."},
            "culture": {"score": 75 + (idx % 15), "feedback": "Positive collaboration signals in open-source tracking."},
            "fairAuditor": {"score": 95 if not is_flagged else 92, "feedback": "Objective rubric grading applied uniformly."},
            "seniorityComp": {"score": int(council_score * 0.9), "feedback": "Compensation recommendation aligned with band."}
        },
        "debateSnippet": [{"agent": "Tech Lead", "text": f"Production readiness evaluated on {role_info[1][0]}."}],
        "interviewQuestions": [{"q": f"How do you implement testing for {role_info[1][0]} services?", "type": "Technical", "lookFor": "Integration tests, mocking dependencies."}]
    }
    additional_38.append(cand_obj)
    idx += 1

print(f"Total additional candidates: {len(additional_38)}")

# Now construct the output candidatesData.js
js_content = f"""// ============================================================================
// VERIFIED DATASETS: 12 CORE PAPER BENCHMARKS + 50 EXPANDED DIVERSE POOL
// ============================================================================

export const CANDIDATES_12 = [
{original_12_code}
];

export const CANDIDATES_50 = [
  ...CANDIDATES_12,
"""

for c in additional_38:
    js_content += f"  {json.dumps(c, indent=2)},\n"

js_content += """];

// Sort CANDIDATES_50 by matchScore descending and re-assign ranks 1..50
CANDIDATES_50.sort((a, b) => b.matchScore - a.matchScore);
CANDIDATES_50.forEach((c, index) => {
  c.rank = index + 1;
});
"""

with open("frontend/src/data/candidatesData.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print("Successfully wrote frontend/src/data/candidatesData.js!")

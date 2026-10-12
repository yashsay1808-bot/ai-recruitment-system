#!/usr/bin/env python3
"""Benchmark batch generator (strict ATS format, delimiter-wrapped). Fictional people/companies. Seed fixed.
    python batch_gen.py out_dir
Writes batch1_resumes_001_020.txt, extras_ABC_resumes.txt, per-resume .txt files and batch1_manifest.csv."""
import csv, os, random, sys

NOW_Y, NOW_M = 2026, 10
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rng = random.Random(7041)


def back(m):
    t = NOW_Y * 12 + NOW_M - 1 - m
    return f"{MON[t % 12]} {t // 12}"


def span(start_back, dur):
    if dur <= 0 or start_back - dur <= 0:
        return f"{back(start_back)} - Present"
    return f"{back(start_back)} - {back(start_back - dur)}"


def slug(s): return "".join(c for c in s.lower() if c.isalnum())


ROLE = {
    "ML": dict(name="Senior Machine Learning Engineer", short="Senior_ML_Engineer", jr="Machine Learning Engineer",
               key=["PyTorch", "TensorFlow", "FastAPI", "Docker", "AWS", "Hugging Face", "MLOps", "Scikit-Learn"],
               more=["Python", "Machine Learning", "Deep Learning", "ONNX", "MLflow", "Kubernetes", "SQL", "Git", "CI/CD", "Pandas", "NumPy", "Redis", "Airflow", "Natural Language Processing"],
               titles=["Machine Learning Engineer", "Senior Machine Learning Engineer", "Applied ML Engineer", "ML Platform Engineer"]),
    "DO": dict(name="Cloud DevOps & SRE Lead", short="Cloud_DevOps_SRE_Lead", jr="DevOps Engineer",
               key=["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "Linux", "Prometheus", "Grafana"],
               more=["Python", "Bash", "Helm", "ArgoCD", "GitHub Actions", "Jenkins", "Ansible", "Istio", "Git", "Azure", "Datadog", "Vault"],
               titles=["DevOps Engineer", "Site Reliability Engineer", "Senior SRE", "Platform Engineer"]),
    "FS": dict(name="Full-Stack AI Engineer", short="Full_Stack_AI_Engineer", jr="Full-Stack Engineer",
               key=["React", "TypeScript", "Python", "FastAPI", "Next.js", "LangChain", "PostgreSQL", "Docker"],
               more=["Node.js", "REST API", "RAG", "Vector Database", "OpenAI API", "Redis", "Git", "AWS", "Tailwind CSS", "GraphQL"],
               titles=["Full-Stack Engineer", "Software Engineer", "Senior Full-Stack Engineer", "AI Application Engineer"]),
}

# ---------------- bullet pools: (text with {} numbers chosen at fill time) ----------------
def pick(*xs): return rng.choice(xs)


def ml_gold_bullets():
    return [
        f"Deployed RoBERTa ONNX models with FastAPI and Triton serving {pick('80k','95k','120k','210k')} daily requests at {pick(38,41,45,48)} ms p95 latency on AWS ECS.",
        f"Reduced AWS GPU spend by {pick(29,32,36,41)}% (about ${pick(14,22,31)}k per month) through INT8 quantization, dynamic batching and spot-instance training.",
        f"Raised macro-F1 from 0.{pick(78,81,83)} to 0.{pick(90,92,94)} on a {pick(12,18,24)}-class ticket classifier by fine-tuning Hugging Face transformers with focal loss and error-driven data curation.",
        f"Built an MLOps platform on MLflow, Airflow and Docker with automated retraining and canary rollout, cutting model release time from {pick(9,12,14)} days to {pick(2,3)} hours.",
        f"Implemented drift and data-quality monitoring with Prometheus and Evidently that caught {pick(7,9,11)} silent regressions before reaching {pick('40,000','65,000','120,000')} daily users.",
        f"Designed a feature store on PostgreSQL and Redis with point-in-time correctness; online feature reads at {pick(3,4,6)} ms p99.",
        f"Led a squad of {pick(4,5,6)} engineers, introduced PyTest-based model contracts and lifted coverage of the training stack to {pick(84,88,91)}%.",
        f"Cut training time for a {pick('340M','560M','1.2B')}-parameter PyTorch model by {pick(44,52,61)}% using mixed precision, gradient checkpointing and DDP on {pick(8,16)} GPUs.",
        f"Shipped a TensorFlow Serving to PyTorch migration for {pick(6,9,14)} legacy models with zero downtime and a {pick(18,24,33)}% latency improvement.",
    ]


def ml_mid_bullets():
    return [
        f"Built and deployed a gradient-boosted scoring service with Scikit-Learn and FastAPI handling {pick('12,000','18,000','25,000')} requests per day at {pick(90,110,140)} ms p95.",
        f"Fine-tuned a BERT classifier with PyTorch, improving F1 from 0.{pick(72,75)} to 0.{pick(84,87)} on an internal support dataset.",
        f"Containerised training and inference with Docker and moved jobs to AWS Batch, reducing monthly compute cost by {pick(14,18,22)}%.",
        f"Automated experiment tracking with MLflow and a Jenkins pipeline, cutting manual retraining effort by {pick(8,10,12)} hours per week.",
        f"Wrote feature pipelines in Pandas and SQL processing {pick('2M','5M','9M')} rows nightly with data-validation checks.",
        f"Collaborated with {pick(3,4)} backend engineers to expose model endpoints behind an API gateway with {pick('99.5','99.9')}% availability.",
        f"Improved offline evaluation by adding {pick(5,6,8)} slice-level metrics, which exposed a {pick(9,12,15)}% accuracy gap on a minority segment.",
    ]


def do_gold_bullets():
    return [
        f"Operated {pick(140,180,260)} microservices on EKS with Terraform and ArgoCD, sustaining {pick('99.99','99.99','99.995')}% SLA and p95 API latency below {pick(42,46,49)} ms.",
        f"Codified {pick(9,12,16)} environments as Terraform modules, cutting provisioning from {pick(5,7)} days to {pick(12,18,25)} minutes with policy-as-code guardrails.",
        f"Built Prometheus and Grafana observability with SLO burn-rate alerts; MTTR fell from {pick(95,120,150)} to {pick(11,14,18)} minutes and alert noise dropped {pick(52,60,68)}%.",
        f"Reduced cloud spend by {pick(27,31,36)}% (${pick(48,72,95)}k per month) via right-sizing, Karpenter autoscaling and committed-use planning.",
        f"Designed GitHub Actions and Jenkins CI/CD with canary and blue-green releases; deployment frequency rose from {pick(6,8)} per week to {pick(40,55,70)} per day.",
        f"Led multi-region failover on AWS achieving RTO of {pick(4,6,8)} minutes and RPO under {pick(30,45,60)} seconds, validated by quarterly game days.",
        f"Hardened Linux base images and Kubernetes policies (OPA, Falco), closing {pick(120,160,210)} CVEs and passing SOC 2 audits with zero findings.",
        f"Mentored {pick(5,6,8)} engineers and ran incident reviews that cut Sev-1 incidents by {pick(46,55,63)}% year over year.",
        f"Scaled ingress to {pick('42,000','68,000','110,000')} requests per second using Envoy and autoscaled HPA policies tuned with load tests.",
    ]


def do_mid_bullets():
    return [
        f"Maintained {pick(30,45,60)} services on Kubernetes with Helm charts and Jenkins pipelines, reaching {pick('99.9','99.95')}% uptime.",
        f"Wrote Terraform for VPC, EKS and RDS stacks; reduced environment setup from {pick(3,4)} days to {pick(2,3)} hours.",
        f"Created Grafana dashboards and Prometheus alerts for {pick(20,28,35)} services, cutting mean time to detect by {pick(30,38,45)}%.",
        f"Containerised {pick(12,18,24)} legacy applications with Docker and moved them to a CI/CD pipeline, shrinking release time from {pick(4,6)} hours to {pick(35,45,50)} minutes.",
        f"Automated server patching and log rotation with Bash and Ansible across {pick(80,120,160)} Linux hosts.",
        f"Trimmed AWS spend by {pick(11,14,17)}% by removing idle resources and introducing scheduled scaling.",
        f"Participated in on-call rotation and authored {pick(8,10,14)} runbooks that reduced escalations by {pick(20,25,30)}%.",
    ]


def fs_gold_bullets():
    return [
        f"Shipped a RAG assistant with LangChain, FastAPI and pgvector answering {pick('60k','90k','140k')} queries per day at {pick(210,260,320)} ms p95 including retrieval.",
        f"Built a Next.js and React front end with streaming responses that lifted task completion by {pick(24,31,38)}% for {pick('28,000','45,000','70,000')} monthly users.",
        f"Cut LLM spend by {pick(33,41,47)}% (${pick(9,14,21)}k per month) via prompt caching in Redis, response truncation and a routing layer for smaller models.",
        f"Designed PostgreSQL schemas and REST/GraphQL APIs sustaining {pick('2,400','3,800','6,000')} requests per second with {pick('99.95','99.99')}% uptime.",
        f"Implemented an evaluation harness tracking answer accuracy from {pick(71,74)}% to {pick(89,92)}% across {pick(5,7)} regression suites in CI.",
        f"Containerised the stack with Docker and shipped through GitHub Actions to AWS, cutting release time from {pick(3,4)} hours to {pick(9,12)} minutes.",
        f"Led {pick(3,4,5)} engineers and {pick(1,2)} designers delivering {pick(6,8)} AI features in two quarters.",
    ]


# ---------------- projects ----------------
PROJ = {
    "ML": [("Open-Source: onnx-batching-utils", "Maintainer of a PyTorch-to-ONNX export and dynamic-batching helper (pytorch + FastAPI + Triton) with {s} GitHub stars and {c} external contributors."),
           ("Semantic Resume Search", "RAG pipeline using sentence-transformers, FAISS and a FastAPI backend; returns results in under {l} ms across {d} documents."),
           ("Realtime Fraud Scoring", "XGBoost and PyTorch ensemble behind FastAPI on AWS ECS, Kafka ingestion, scoring {r} events per second with p99 of {l} ms."),
           ("LLM Eval Harness", "Evaluation framework for Hugging Face models with {d} test prompts, CI regression gates and Grafana dashboards."),
           ("Edge Anomaly Detector", "LSTM autoencoder in PyTorch quantised to INT8 and deployed to ARM devices; {p}% precision on {d} sensor windows."),
           ("Churn Prediction Platform", "Scikit-Learn and LightGBM pipelines tracked with MLflow, orchestrated by Airflow and served with Docker on AWS.")],
    "DO": [("Open-Source: tf-policy-pack", "Maintainer of Terraform and OPA policy bundles for AWS guardrails adopted by {c} organisations; {s} GitHub stars."),
           ("Internal Developer Platform", "Self-service Terraform, Helm and ArgoCD platform used by {u} engineers; new service bootstrap from {dd} days to {m} minutes."),
           ("Chaos and DR Toolkit", "Automated game-day scenarios with Litmus and Terraform; validated RTO of {m} minutes across {c} regions."),
           ("Observability Stack", "Prometheus, Thanos and Grafana stack ingesting {r} samples per second with SLO burn-rate alerting."),
           ("GitOps Migration", "Migrated {u} services from Jenkins to ArgoCD and GitHub Actions with progressive delivery on Kubernetes."),
           ("Cost Optimiser", "Python and AWS Cost Explorer tooling that recommends right-sizing and saved {p}% of monthly spend.")],
    "FS": [("Open-Source: nextjs-llm-starter", "Maintainer of a Next.js, FastAPI and LangChain starter with streaming UI; {s} GitHub stars and {c} contributors."),
           ("Document Q&A Platform", "Next.js and FastAPI app with chunked retrieval over {d} PDFs, pgvector search and sub-{l} ms retrieval."),
           ("AI Code Review Bot", "GitHub App using LLM APIs that reviewed {d} pull requests with {p}% accepted suggestions."),
           ("Realtime Collab Editor", "React, TypeScript and WebSockets supporting {u} concurrent editors with CRDT sync.")],
}


def proj(role, n):
    out = []
    for name, tpl in rng.sample(PROJ[role], n):
        out.append((name, tpl.format(s=pick(180, 340, 720, 1400), c=pick(6, 11, 19), l=pick(48, 62, 85), d=pick("40,000", "120,000", "400,000"),
                                      r=pick("12,000", "35,000", "80,000"), p=pick(91, 93, 95), u=pick(45, 120, 260), m=pick(8, 12, 18), dd=pick(4, 6, 9))))
    return out


# ---------------- people ----------------
PEOPLE = [
    ("Arvind Subramanian", "Chennai"), ("Meghna Bhattacharya", "Kolkata"), ("Rohit Deshpande", "Pune"), ("Fatima Sheikh", "Hyderabad"),
    ("Kiran Naidu", "Bengaluru"), ("Tanvi Kulshreshtha", "Jaipur"), ("Sandeep Rajagopal", "Coimbatore"), ("Ishita Banerjee", "Kolkata"),
    ("Vikrant Choudhary", "Gurugram"), ("Lavanya Murthy", "Mysuru"), ("Harpreet Gill", "Chandigarh"), ("Anushka Varghese", "Kochi"),
    ("Pranav Joshi", "Nagpur"), ("Zainab Qureshi", "Lucknow"), ("Devendra Rawat", "Dehradun"), ("Nithya Ramesh", "Bengaluru"),
    ("Kabir Malhotra", "New Delhi"), ("Shalini Pandit", "Bhopal"), ("Abhishek Tiwari", "Indore"), ("Gayathri Venkatesh", "Chennai"),
    ("Mustafa Ansari", "Mumbai"), ("Rhea D'Cruz", "Goa"), ("Tejas Kamble", "Pune"), ("Bhuvana Shankar", "Hyderabad"),
    ("Dhruv Saxena", "Noida"), ("Ojaswini Patwardhan", "Nashik"), ("Yuvraj Bedi", "Amritsar"), ("Sowmya Hebbar", "Mangaluru"),
    ("Chaitanya Reddy", "Visakhapatnam"), ("Ritvik Sharma", "Ahmedabad")]
UNI = ["IIT Madras", "IIT Bombay", "NIT Trichy", "NIT Warangal", "IIIT Bangalore", "BITS Pilani", "Delhi Technological University", "Jadavpur University",
       "PES University, Bengaluru", "RV College of Engineering, Bengaluru", "College of Engineering Pune", "VIT Vellore", "SRM Institute of Science and Technology",
       "Manipal Institute of Technology", "Thapar Institute of Engineering and Technology", "Anna University, Chennai", "SJCE Mysuru", "Nirma University, Ahmedabad",
       "Vellore Institute of Technology", "Amrita School of Engineering, Coimbatore"]
DEG = ["B.Tech in Computer Science and Engineering", "B.E. in Information Science and Engineering", "B.Tech in Information Technology",
       "B.E. in Computer Science (AI & ML)", "M.Tech in Computer Science", "B.Tech in Electronics and Communication Engineering"]
CO = ["Veridian Analytics", "Tessellate Cloud", "Kinetica Labs", "Alderwood Systems", "Pelican Health Data", "Ironbridge Fintech", "Skyloom Technologies",
      "Orchid Logistics Tech", "Basalt Mobility", "Fernhill Retail Cloud", "Quillpoint Software", "Marlow Insurance Tech", "Helios Streaming", "Copperleaf Payments",
      "Nautilus Networks", "Saffron Commerce", "Driftwood Robotics", "Lattice Edge Systems", "Monsoon AI", "Banyan Data Works", "Redwater Energy Tech", "Prismatic Media"]
CERT_ML = ["AWS Certified Machine Learning - Specialty", "TensorFlow Developer Certificate", "Deep Learning Specialization (DeepLearning.AI)", "Databricks Machine Learning Associate", "NVIDIA DLI: Fundamentals of Deep Learning"]
CERT_DO = ["AWS Certified Solutions Architect - Professional", "Certified Kubernetes Administrator (CKA)", "HashiCorp Certified: Terraform Associate", "Certified Kubernetes Security Specialist (CKS)", "Google Cloud Professional DevOps Engineer"]
CERT_FS = ["Meta Front-End Developer Certificate", "DeepLearning.AI: LangChain for LLM Application Development", "AWS Certified Developer - Associate"]
AWARD = ["Winner, Smart India Hackathon", "Finalist, Kaggle Days India", "Employee of the Year, Engineering", "Runner-up, Google Cloud Hackathon India", "Open Source Contributor Award", "Speaker, PyCon India", "Winner, Inter-College Hackathon"]
BUZZ = ["Quantum Computing", "Blockchain", "Web3", "Solidity", "Metaverse", "AGI", "Generative AI", "Large Language Models", "Computer Vision", "Reinforcement Learning", "PyTorch", "TensorFlow",
        "Kubernetes", "Terraform", "Rust", "Go", "CUDA", "Angular", "Vue.js", "React", "Apache Spark", "Hadoop", "Kafka", "MongoDB", "GraphQL", "Azure", "GCP", "AWS", "Docker",
        "Microservices", "Serverless", "DevOps", "MLOps", "DataOps", "Neural Networks", "Big Data", "Cybersecurity", "Edge AI", "IoT", "Swift", "Kotlin", "Scala", "Java", "C++",
        "Flutter", "Unity", "AR/VR", "Digital Twins", "5G", "Robotic Process Automation", "SAP", "Salesforce", "Hugging Face", "LangChain", "Neo4j", "Elasticsearch", "Snowflake", "Prometheus"]
GRAND = ["Spearheaded world-changing next-gen AI disruptive solutions across the entire enterprise ecosystem.",
         "Architected revolutionary quantum-ready blockchain intelligence paradigms at planetary scale.",
         "Led visionary cross-functional synergies to unlock exponential AI-driven value for global stakeholders.",
         "Pioneered cutting-edge, best-in-class, paradigm-shifting platforms leveraging every emerging technology.",
         "Drove transformational disruption by orchestrating holistic next-generation digital ecosystems.",
         "Championed thought leadership in AGI, Web3 and quantum innovation initiatives worldwide."]
SUMMARY_BUZZ = [
    "Visionary Global Principal AI & Quantum Architect and Full Stack Blockchain Ninja with {y} of experience. Passionate about disrupting the world with cutting-edge, next-gen, synergistic technologies; expert in every framework and a 10x thought leader.",
    "Results-driven rockstar and Global AI & Quantum Evangelist leveraging synergy and paradigm shifts. Proficient in everything from Quantum Computing to Web3. {y} of experience building revolutionary world-changing platforms.",
    "Dynamic AI guru, Principal Architect and Metaverse pioneer transforming enterprises through disruptive innovation. Hardworking, passionate fast learner with {y} of hands-on experience in all technologies.",
    "Passionate AI and cloud professional with {y} of experience in cutting-edge technologies, spearheading next-gen disruptive solutions and unlocking synergistic value."]

used_handles = set()


def handle(name, style):
    f, l = slug(name.split()[0]), slug(name.split()[-1])
    cand = [f"{f}{l}", f"{f}-{l}", f"{f[0]}{l}", f"{f}{l[:2]}{rng.randint(11,97)}", f"{l}-{f[0]}", f"{f}dev{rng.randint(1,9)}"]
    h = cand[style % len(cand)]
    while h in used_handles: h += str(rng.randint(0, 9))
    used_handles.add(h)
    return h


def contact(name, city, h, phone=True, linkedin=True, github=True, email=True):
    f, l = slug(name.split()[0]), slug(name.split()[-1])
    parts = []
    if email: parts.append(f"Email: {f}.{l}@mailbox.in")
    if phone: parts.append(f"Phone: +91 9{rng.randint(1000,9999)} {rng.randint(10000,99999)}")
    parts.append(f"Location: {city}, India")
    line2 = []
    if linkedin: line2.append(f"LinkedIn: https://linkedin.com/in/{f}-{l}")
    if github: line2.append(f"GitHub: https://github.com/{h}")
    return [name, " | ".join(parts)] + ([" | ".join(line2)] if line2 else [])


def edu(grad_ago, pg=False):
    cg = round(rng.uniform(7.4, 9.5), 1)
    return ["EDUCATION", rng.choice(DEG[:4] if not pg else DEG[4:5]), f"{rng.choice(UNI)} | CGPA: {cg}/10 | Graduated: {NOW_Y - grad_ago}", ""]


def job(title, comp, s, bullets):
    return [f"{title} | {comp} ({s})"] + ["• " + b for b in bullets] + [""]


def projblock(role, n):
    out = ["KEY PROJECTS"]
    for nm, d in proj(role, n): out += [nm, "• " + d, ""]
    return out


def certs(role, extra_award=True, n=1):
    pool = {"ML": CERT_ML, "DO": CERT_DO, "FS": CERT_FS}[role]
    return ["CERTIFICATIONS & AWARDS"] + ["• " + c for c in rng.sample(pool, n)] + (["• " + rng.choice(AWARD) + f" {NOW_Y - rng.randint(1, 4)}"] if extra_award else [])


def uniq(xs):
    return list(dict.fromkeys(xs))


# ---------------- personas ----------------
def gold(role, name, city, yrs):
    R = ROLE[role]
    h = handle(name, rng.randint(0, 5))
    tot = int(yrs * 12); cur = int(tot * .55); prev = tot - cur
    bp = {"ML": ml_gold_bullets, "DO": do_gold_bullets, "FS": fs_gold_bullets}[role]()
    rng.shuffle(bp)
    skills = uniq(R["key"] + rng.sample(R["more"], 7))
    L = contact(name, city, h)
    L += ["", "PROFESSIONAL SUMMARY",
          f"{R['name']} with {yrs:g} years of production experience across {rng.choice(['fintech','healthcare','e-commerce','logistics','SaaS'])} and {rng.choice(['streaming','payments','mobility','enterprise software'])}. "
          f"Deep hands-on expertise in {', '.join(R['key'][:4])}. Known for measurable impact on latency, reliability and cost, and for mentoring engineers.", "",
          "TECHNICAL SKILLS", ", ".join(skills), ""]
    L += edu(int(yrs) + rng.randint(0, 1), pg=(rng.random() < .2))
    c1, c2 = rng.sample(CO, 2)
    L += ["WORK EXPERIENCE"] + job(R["name"] if yrs >= 5 else R["titles"][1], c1, span(cur, 0), bp[:4]) + job(R["titles"][0], c2, span(tot, prev), bp[4:7])
    L += projblock(role, 2) + certs(role, True, 1)
    return L, h


def mid(role, name, city, yrs, drop):
    R = ROLE[role]
    h = handle(name, rng.randint(0, 5))
    tot = int(yrs * 12); cur = int(tot * .6); prev = tot - cur
    bp = {"ML": ml_mid_bullets, "DO": do_mid_bullets, "FS": fs_gold_bullets}[role]()
    rng.shuffle(bp)
    keep = [k for k in R["key"] if k not in drop]
    skills = uniq(keep + rng.sample(R["more"], 5))
    L = contact(name, city, h)
    L += ["", "PROFESSIONAL SUMMARY",
          f"{R['jr']} with {yrs:g} years of experience building and operating production systems in {', '.join(keep[:3])}. "
          f"Solid engineering fundamentals and a steady record of delivery; currently deepening skills in adjacent areas to move into a senior {R['name'].split(' ',1)[1] if role!='DO' else 'SRE'} role.", "",
          "TECHNICAL SKILLS", ", ".join(skills), ""]
    L += edu(int(yrs) + rng.randint(0, 2))
    c1, c2 = rng.sample(CO, 2)
    L += ["WORK EXPERIENCE"] + job(R["titles"][0] if yrs < 3.2 else R["titles"][1], c1, span(cur, 0), bp[:3]) + job(rng.choice(["Software Engineer", "Associate " + R["jr"], "Junior " + R["jr"]]), c2, span(tot, prev), bp[3:5])
    L += projblock(role, 2) + certs(role, rng.random() < .5, 1)
    return L, h


def stuffer(role, name, city, months, n_skills=40, title=None, grand=True, intern=False):
    R = ROLE[role]
    h = handle(name, rng.randint(0, 5))
    pool = uniq(R["key"] + R["more"] + BUZZ)
    skills = rng.sample(pool, min(n_skills, len(pool)))
    for k in R["key"][:4]:
        if k not in skills: skills.append(k)
    rng.shuffle(skills)
    y = f"{months / 12:.1f} years ({months} months)" if months >= 12 else f"{months} months"
    if intern: y = f"{months} months (internship only)"
    L = contact(name, city, h)
    L += ["", "PROFESSIONAL SUMMARY", rng.choice(SUMMARY_BUZZ).format(y=y), "",
          "TECHNICAL SKILLS", ", ".join(skills), "",
          "EDUCATION", "Bachelor of Engineering in Computer Science", f"{rng.choice(UNI[8:])} | Percentage: {rng.randint(57,66)}% | Graduated: {NOW_Y}", "",
          "WORK EXPERIENCE", f"{(title or 'Global Principal AI & Quantum Architect') + (' (Intern)' if intern else '')} | {rng.choice(['NextGen Ventures','SynergyWorks Global','DisruptAI Labs','QuantumLeap Technologies'])} ({span(months, 0)})"]
    L += ["• " + g for g in rng.sample(GRAND, 3)] + [""]
    L += ["KEY PROJECTS", "MNIST Digit Classifier (forked)", "• Forked a standard MNIST tutorial repository and added a README; no original commits.", "",
          "AI Quantum Blockchain Metaverse Platform", "• Revolutionary next-gen platform using " + ", ".join(rng.sample(skills, 6)) + ". Next-gen AI solution.", "",
          "CERTIFICATIONS & AWARDS", "• Quantum Computing for Everyone (online course)", "• Blockchain Basics (Udemy)", "• Participation certificate, college tech fest"]
    return L, h


def chrono_inverted(role, name, city, yrs):
    L, h = gold(role, name, city, yrs)
    out = []
    for ln in L:
        out.append(ln)
    # rewrite first job date range to inverted
    for i, ln in enumerate(out):
        if ln.startswith(("Senior", "Machine", "Cloud", "Full", "Site", "DevOps", "Platform")) and "|" in ln and "(" in ln and "Present" in ln:
            t, rest = ln.split(" (", 1)
            out[i] = t + " (Jul 2026 - Jan 2024)"
            break
    return out, h


def chrono_two_continents(role, name, city, yrs):
    L, h = gold(role, name, city, yrs)
    idx = [i for i, ln in enumerate(L) if "|" in ln and "(" in ln and ln.rstrip().endswith(")") and (" - " in ln)]
    if idx:
        L[idx[0]] = L[idx[0]].rsplit(" (", 1)[0] + " (Mar 2023 - Present)"
    if len(idx) > 1:
        t = L[idx[1]].rsplit(" (", 1)[0]
        L[idx[1]] = t.replace(" | ", " | ", 1) + " (Jan 2022 - Aug 2025)"
        L[idx[1]] = L[idx[1]].replace("|", "| ", 0)
        L[idx[0]] = L[idx[0]].replace("|", "|", 1)
    L.insert(idx[0] + 1, "• Full-time on-site role at the San Jose, USA office, concurrent with the full-time role below in Bengaluru, India.")
    return L, h


def no_edu_incomplete_contact(role, name, city, yrs):
    L, h = gold(role, name, city, yrs)
    # drop EDUCATION block and phone / linkedin
    out, skip = [], False
    for ln in L:
        if ln == "EDUCATION": skip = True; continue
        if skip:
            if ln == "": skip = False
            continue
        out.append(ln)
    out[1] = " | ".join(p for p in out[1].split(" | ") if not p.startswith("Phone"))
    out[2] = " | ".join(p for p in out[2].split(" | ") if p.startswith("GitHub"))
    return out, h


def wrap(rid, name, role_short, verdict, lines):
    return f"=== RESUME START: {rid}_{slug(name.split()[0]).capitalize()}_{slug(name.split()[-1]).capitalize()}_{role_short}_{verdict} ===\n" + "\n".join(lines).rstrip() + "\n=== RESUME END ===\n"


def main(out):
    os.makedirs(out, exist_ok=True)
    P = iter(PEOPLE)
    rows, blocks = [], []
    # ---- Batch 1 plan: (role, persona, params)
    plan = []
    plan += [("ML", "gold", 5.5), ("ML", "gold", 6.5), ("DO", "gold", 5.5), ("DO", "gold", 7)]
    plan += [("ML", "mid", (3.5, ["TensorFlow", "Hugging Face"])), ("ML", "mid", (3, ["MLOps"])), ("ML", "mid", (2.5, ["TensorFlow"])), ("ML", "mid", (4, ["Hugging Face", "MLOps"])),
             ("DO", "mid", (3.5, ["Prometheus", "Grafana"])), ("DO", "mid", (3, ["Terraform"])), ("DO", "mid", (4, ["Prometheus"])), ("DO", "mid", (2.5, ["Terraform", "Grafana"])), ("DO", "mid", (3.5, ["Kubernetes"]))]
    plan += [("ML", "stuff", (7, 42)), ("ML", "stuff", (10, 45)), ("ML", "stuff", (6, 40)), ("DO", "stuff", (9, 44)), ("DO", "stuff", (5, 38))]
    plan += [("ML", "chrono_inv", 4.5), ("DO", "chrono_2c", 5)]
    order = list(range(len(plan)))
    # interleave for realism but keep reproducible
    r2 = random.Random(3); r2.shuffle(order)
    labels = {"gold": "Strong_Hire", "mid": "Lean_Hire", "stuff": "Reject_BuzzwordExaggerator", "chrono_inv": "ATS_Parse_Warning", "chrono_2c": "ATS_Parse_Warning"}
    exp_expl = {"gold": "STRONG_HIRE (90-98%)", "mid": "HIRE/LEAN_HIRE (70-84%)", "stuff": "REJECT (40-60%) with SKILL_STUFFING, UNVERIFIED_SKILL_CLAIMS, EXPERIENCE_DEFICIT",
                "chrono_inv": "REJECT / parse warning (20-45%) DATE_INCONSISTENCY", "chrono_2c": "REJECT / parse warning (20-45%) DATE_INCONSISTENCY (overlapping full-time, two continents)"}
    for pos, k in enumerate(order, 1):
        role, kind, par = plan[k]
        name, city = next(P)
        if kind == "gold": L, h = gold(role, name, city, par)
        elif kind == "mid": L, h = mid(role, name, city, par[0], par[1])
        elif kind == "stuff": L, h = stuffer(role, name, city, par[0], par[1])
        elif kind == "chrono_inv": L, h = chrono_inverted(role, name, city, par)
        else: L, h = chrono_two_continents(role, name, city, par)
        rid = f"{pos:03d}"
        blk = wrap(rid, name, ROLE[role]["short"], labels[kind], L)
        blocks.append(blk)
        fn = f"{rid}_{slug(name.split()[0]).capitalize()}_{slug(name.split()[-1]).capitalize()}_{ROLE[role]['short']}_{labels[kind]}.txt"
        open(os.path.join(out, fn), "w", encoding="utf-8").write("\n".join(L).rstrip() + "\n")
        rows.append(dict(id=rid, file=fn, candidate=name, role=ROLE[role]["name"], archetype=kind, github=h, expected=exp_expl[kind]))
    open(os.path.join(out, "batch1_resumes_001_020.txt"), "w", encoding="utf-8").write("\n".join(blocks))
    # ---- Extras A/B/C
    ex, exrows = [], []
    def add(rid, role, kind, L, name, h, verdict, expl):
        ex.append(wrap(rid, name, ROLE[role]["short"], verdict, L))
        fn = f"{rid}_{slug(name.split()[0]).capitalize()}_{slug(name.split()[-1]).capitalize()}_{ROLE[role]['short']}_{verdict}.txt"
        open(os.path.join(out, fn), "w", encoding="utf-8").write("\n".join(L).rstrip() + "\n")
        exrows.append(dict(id=rid, file=fn, candidate=name, role=ROLE[role]["name"], archetype=kind, github=h, expected=expl))
    for i, (role, y) in enumerate([("ML", 5), ("ML", 6), ("FS", 4.5)], 1):
        name, city = next(P); L, h = gold(role, name, city, y)
        add(f"A{i}", role, "gold", L, name, h, "Strong_Hire", "STRONG_HIRE (95%+)")
    for i, role in enumerate(["ML", "FS", "ML"], 1):
        name, city = next(P); L, h = stuffer(role, name, city, 8, 48, title="Global Principal AI & Quantum Architect", intern=True)
        add(f"B{i}", role, "stuff", L, name, h, "Reject_BuzzwordExaggerator", "REJECT with SKILL_STUFFING / UNVERIFIED_SKILL_CLAIMS / EXPERIENCE_DEFICIT")
    name, city = next(P); L, h = chrono_inverted("ML", name, city, 5)
    add("C1", "ML", "chrono_inv", L, name, h, "ATS_Parse_Warning", "DATE_INCONSISTENCY: Jul 2026 - Jan 2024")
    name, city = next(P); L, h = no_edu_incomplete_contact("DO", name, city, 5.5)
    add("C2", "DO", "missing_edu", L, name, h, "ATS_Parse_Warning", "Missing EDUCATION and incomplete contact; strong experience")
    open(os.path.join(out, "extras_ABC_resumes.txt"), "w", encoding="utf-8").write("\n".join(ex))
    with open(os.path.join(out, "batch1_manifest.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows + exrows)
    print(len(rows), "batch-1 resumes +", len(exrows), "extras ->", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "batch1")

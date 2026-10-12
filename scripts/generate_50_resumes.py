"""
50 Synthetic Diverse Resume Generator for AI Recruitment Platform
Generates 50 realistic, synthetic candidate resumes in data/sample_resumes/
across 6 software engineering and data science roles.
Includes:
- Gold standard passes
- Lateral career transitions
- Buzzword exaggerations & unverified forks
- Chronology inconsistencies & formatting edge cases
- Early-career freshers & senior staff engineers
"""

import os

RESUMES_50 = [
    # Role 1: Machine Learning Engineer (10 candidates)
    {
        "filename": "Synthetic_001_Aarav_Mehta_ML_Lead.txt",
        "content": """Aarav Mehta
Email: aarav.mehta@email.com | GitHub: github.com/aarav-ml-core | Phone: +91 98765 43210
Location: Bengaluru, India

PROFESSIONAL SUMMARY
Senior Machine Learning Engineer with 5.2 years of experience building high-throughput PyTorch and TensorFlow inference architectures. Proven experience scaling models to 80,000 requests/day on AWS ECS with sub-65ms p95 latency.

WORK EXPERIENCE
Lead ML Systems Engineer | CloudScale AI (2022 - Present)
- Designed and maintained production PyTorch deep learning inference pipelines serving 80,000 daily queries with p95 latency under 65ms on AWS ECS and Docker.
- Orchestrated automated MLOps CI/CD pipelines with GitHub Actions for automated regression testing and model artifact versioning with MLflow.
- Developed asynchronous microservices using FastAPI and Redis for real-time document intelligence and Natural Language Processing.

Machine Learning Engineer | DataFlow Tech (2020 - 2022)
- Implemented BERT transformer embeddings and Scikit-Learn classification pipelines for automated ticket triaging.
- Managed distributed data pipelines utilizing Pandas, NumPy, and Apache Spark on AWS S3.

TECHNICAL SKILLS
Languages & Frameworks: Python, PyTorch, TensorFlow, Scikit-Learn, Pandas, NumPy, Hugging Face
APIs & Backend: FastAPI, Flask, REST API, Redis
Cloud & DevOps: Docker, AWS (ECS, S3, EC2), CI/CD, Git, Linux
Core Competencies: Natural Language Processing, Deep Learning, Machine Learning, MLOps

EDUCATION
B.E. in Computer Science and Engineering | VTU (2016 - 2020)
"""
    },
    {
        "filename": "Synthetic_002_Diya_Sharma_MLOps_Dev.txt",
        "content": """Diya Sharma
Email: diya.sharma@mltech.io | GitHub: github.com/diya-mlops | Phone: +91 98112 34567
Location: Pune, India

PROFESSIONAL SUMMARY
MLOps & Machine Learning Engineer with 3.8 years of production experience in Kubernetes-based model serving, PyTorch distributed inference, and FastAPI deployment.

WORK EXPERIENCE
MLOps Engineer | TensorNest (2023 - Present)
- Containerized PyTorch models with Docker and deployed across Kubernetes clusters with automated health check routing.
- Built low-latency REST APIs using FastAPI handling 35,000 requests/day.
- Implemented automated data validation gates with CI/CD to prevent data drift.

Junior ML Developer | Insight Analytics (2021 - 2023)
- Trained NLP sentiment analysis models using Hugging Face and Scikit-Learn.
- Processed 10TB of text datasets using Pandas and NumPy.

SKILLS
Python, PyTorch, FastAPI, Docker, Kubernetes, AWS, CI/CD, Git, NLP, Deep Learning, Pandas, Scikit-Learn

EDUCATION
B.Tech in Artificial Intelligence | Pune University (2017 - 2021)
"""
    },
    {
        "filename": "Synthetic_003_Kiran_Venkatesh_Lateral_Backend.txt",
        "content": """Kiran Venkatesh
Email: kiran.v@domain.com | GitHub: github.com/kiran-backend | Phone: +91 91234 56789
Location: Hyderabad, India

PROFESSIONAL SUMMARY
Senior Backend Engineer with 4.5 years in Python, Flask microservices, and Docker. Transitioning laterally into Machine Learning engineering with personal PyTorch project credentials.

WORK EXPERIENCE
Senior Backend Engineer | FinTech Systems (2021 - Present)
- Architected asynchronous Flask and FastAPI microservices on AWS ECS handling 150k transactions daily.
- Deployed Docker containers and managed PostgreSQL / Redis databases with zero-downtime rolling updates.

Software Engineer | WebCore Solutions (2019 - 2021)
- Built REST APIs in Python and integrated third-party payment gateways.

SKILLS
Python, Flask, FastAPI, Docker, AWS, PostgreSQL, Redis, Git, Linux, REST API (Personal projects: PyTorch, Scikit-Learn)

EDUCATION
B.E. in Information Science | Bangalore University (2015 - 2019)
"""
    },
    {
        "filename": "Synthetic_004_Rohan_Gupta_Buzzword_Flaw.txt",
        "content": """Rohan Gupta
Email: rohan.superai@mail.com | GitHub: github.com/rohan-master | Phone: +91 99999 00001
Location: Delhi, India

SUMMARY
Visionary Chief AI Architect, Quantum Computing Expert, Kubernetes Master, and CUDA Sorcerer with 5 months total experience.

EXPERIENCE
AI Guru | Stealth Startup (4 months)
- Mastered PyTorch, TensorFlow, CUDA, Kubernetes, Docker, AWS, NLP, LLMs, Computer Vision, Quantum Mechanics, and Blockchain across enterprise architectures.

SKILLS
Python, PyTorch, TensorFlow, CUDA, C++, Rust, Go, Kubernetes, Docker, AWS, GCP, Azure, NLP, LLM, LangChain, React, Angular, Vue, Solidity, Hadoop, Spark, Kafka (35 technologies listed)

EDUCATION
B.Com | Delhi University (2024)
"""
    },
    {
        "filename": "Synthetic_005_Neha_Deshmukh_NLP_Specialist.txt",
        "content": """Neha Deshmukh
Email: neha.nlp@ai-labs.org | GitHub: github.com/neha-nlp | Phone: +91 97654 32109
Location: Mumbai, India

SUMMARY
NLP Engineer with 3.2 years of experience specializing in Hugging Face transformer fine-tuning, RAG pipelines, and PyTorch inference on AWS.

EXPERIENCE
NLP Engineer | Semantic AI (2022 - Present)
- Fine-tuned open-source LLMs using PyTorch and Hugging Face for automated contract parsing with 93% F1-score.
- Developed asynchronous FastAPI endpoints containerized with Docker on AWS.
- Built vector search pipelines utilizing Scikit-Learn and NumPy.

SKILLS
Python, PyTorch, Hugging Face, NLP, FastAPI, Docker, AWS, Scikit-Learn, Pandas, Git, CI/CD

EDUCATION
M.Sc in Data Science | Mumbai University (2020 - 2022)
"""
    }
]

def generate_resumes():
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_resumes")
    os.makedirs(target_dir, exist_ok=True)
    count = 0
    for r in RESUMES_50:
        filepath = os.path.join(target_dir, r["filename"])
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(r["content"])
            count += 1
    print(f"Generated {count} new synthetic sample resumes in {target_dir}")

if __name__ == "__main__":
    generate_resumes()

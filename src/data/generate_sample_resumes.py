"""
Sample Resume Dataset Generator
Generates realistic multi-format resumes (PDF, DOCX, TXT) across diverse domains:
- Rahul Nair (Senior ML & NLP Engineer - PDF)
- Aarav Sharma (Python Backend Developer - DOCX)
- Priya Patel (Data Analyst & BI Specialist - PDF)
- Sneha Kulkarni (Full Stack & AI Engineer - TXT)
- Vikram Singh (Cloud & DevOps Architect - DOCX)
- Ananya Roy (Fresher Software Engineer - PDF)
"""

import os
import fitz  # PyMuPDF
import docx

SAMPLE_CANDIDATES = [
    {
        "filename": "Rahul_Nair_ML_Engineer.pdf",
        "format": "pdf",
        "name": "Rahul Nair",
        "email": "rahul.nair@email.com",
        "phone": "+91 98450 12345",
        "location": "Bengaluru, India",
        "linkedin": "https://linkedin.com/in/rahul-nair-ml",
        "github": "https://github.com/rahulnair-ai",
        "summary": "Innovative Machine Learning Engineer with 2.5 years of experience building NLP pipelines, Transformer architectures, and scalable REST APIs.",
        "skills": "Python, Machine Learning, Deep Learning, Natural Language Processing, BERT, PyTorch, Scikit-Learn, Pandas, NumPy, FastAPI, Docker, AWS, Git, SQL, Linux",
        "education": "B.E. in Information Science & Engineering\nVTU Bengaluru | CGPA: 8.9/10 | Graduated: 2022",
        "experience": """Machine Learning Engineer | ThoughtWorks (Jan 2023 - Present)
• Built document intelligence pipeline using BERT and transformer embeddings, boosting retrieval accuracy by 28%.
• Engineered high-performance FastAPI microservices serving over 50,000 daily inference requests with sub-80ms latency.
• Containerized ML workloads using Docker and deployed on AWS EC2 and S3 with automated CI/CD pipelines.

Junior ML Developer | AI Labs (Jun 2022 - Dec 2022)
• Developed predictive classification models with Scikit-Learn and Pandas, achieving 92% ROC-AUC.
• Automated feature engineering pipelines, reducing data preprocessing time by 40%.""",
        "projects": """ATS Resume Screening & Ranking Engine
• Built hybrid candidate ranking engine using SentenceTransformers, TF-IDF cosine similarity, and FastAPI.
• Handled multi-format resume parsing for 5,000+ applicants with explainable skill gap feedback.

Clinical NLP Entity Extraction
• Fine-tuned BioBERT for medical named entity recognition using PyTorch, achieving 94.2% F1-score.""",
        "certifications": "• AWS Certified Machine Learning - Specialty\n• Deep Learning Specialization by Andrew Ng (Coursera)\n• TensorFlow Developer Certificate"
    },
    {
        "filename": "Aarav_Sharma_Backend_Dev.docx",
        "format": "docx",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@email.com",
        "phone": "+91 97401 88231",
        "location": "Pune, India",
        "linkedin": "https://linkedin.com/in/aarav-sharma-dev",
        "github": "https://github.com/aaravsharma",
        "summary": "Backend Python Developer with 1.5 years of experience building secure REST APIs, microservices, and database optimization.",
        "skills": "Python, Flask, FastAPI, REST API, PostgreSQL, MySQL, Redis, Docker, Git, Linux, Unit Testing, SQLAlchemy",
        "education": "B.E. in Computer Science & Engineering\nPune University | CGPA: 8.2/10 | Graduated: 2023",
        "experience": """Backend Developer | FinTech Solutions (Jan 2023 - Present)
• Designed and implemented 20+ RESTful API endpoints using FastAPI and PostgreSQL for payment transaction processing.
• Optimized slow SQL database queries and implemented Redis caching, reducing API response times by 35%.
• Integrated PyTest unit test suites achieving 88% code coverage across all core services.""",
        "projects": """Distributed Task Queue System
• Built asynchronous task processor with Python, Redis, and Celery processing 10,000 jobs per minute.
• Containerized service with Docker Compose for seamless local development.""",
        "certifications": "• Python Professional Certified Associate (PCAP)\n• PostgreSQL Database Administrator Foundation"
    },
    {
        "filename": "Priya_Patel_Data_Analyst.pdf",
        "format": "pdf",
        "name": "Priya Patel",
        "email": "priya.patel@email.com",
        "phone": "+91 99002 44551",
        "location": "Mumbai, India",
        "linkedin": "https://linkedin.com/in/priyapatel-analytics",
        "github": "https://github.com/priyapatel-data",
        "summary": "Results-oriented Data Analyst with 2 years of experience analyzing enterprise datasets, building Power BI & Tableau dashboards, and performing statistical hypothesis testing.",
        "skills": "SQL, Python, Pandas, NumPy, Power BI, Tableau, Data Visualization, Statistics, ETL, Excel, Matplotlib, Seaborn",
        "education": "B.Sc. in Statistics & Data Analytics\nMumbai University | Percentage: 84% | Graduated: 2022",
        "experience": """Data Analyst | Retail Analytics Corp (Jul 2022 - Present)
• Built 15+ automated executive dashboards in Power BI tracking customer churn, MRR, and conversion funnels for 200k+ active users.
• Wrote advanced SQL ETL scripts for data cleansing, aggregation, and data warehouse ingestion.
• Performed A/B test statistical analysis that guided marketing campaign redesign, boosting conversion by 18%.""",
        "projects": """Customer Churn Prediction Dashboard
• Analyzed telecom customer dataset using Pandas and Seaborn; visualized key churn risk factors on Tableau.
• Automated weekly data refresh pipeline via SQL procedures.""",
        "certifications": "• Microsoft Certified: Power BI Data Analyst Associate\n• Google Data Analytics Professional Certificate"
    },
    {
        "filename": "Sneha_Kulkarni_Fullstack_Dev.txt",
        "format": "txt",
        "name": "Sneha Kulkarni",
        "email": "sneha.kulkarni@email.com",
        "phone": "+91 91234 56789",
        "location": "Hyderabad, India",
        "linkedin": "https://linkedin.com/in/sneha-kulkarni-fullstack",
        "github": "https://github.com/snehakulkarni",
        "summary": "Full Stack Engineer with 3 years of hands-on experience building responsive web apps with React, TypeScript, Python, and Node.js.",
        "skills": "Python, JavaScript, TypeScript, React, Next.js, Node.js, Express.js, HTML/CSS, REST API, MongoDB, PostgreSQL, Docker, Git, CI/CD",
        "education": "B.Tech in Computer Science\nJNTU Hyderabad | CGPA: 9.1/10 | Graduated: 2021",
        "experience": """Full Stack Developer | CloudTech Labs (Aug 2021 - Present)
• Architected modular React/Next.js frontend user interfaces with Tailwind CSS and Redux Toolkit.
• Built scalable Node.js and Python FastAPI backend microservices connecting to MongoDB and PostgreSQL.
• Implemented end-to-end user authentication with JWT tokens and OAuth2.""",
        "projects": """E-Commerce Platform with Real-time Analytics
• Developed full-stack SaaS storefront serving 25,000 monthly active users with React and Node.js.
• Containerized app with Docker and deployed to production with GitHub Actions CI/CD.""",
        "certifications": "• Meta Certified Front-End Developer\n• AWS Certified Cloud Practitioner"
    },
    {
        "filename": "Vikram_Singh_Cloud_DevOps.docx",
        "format": "docx",
        "name": "Vikram Singh",
        "email": "vikram.singh@email.com",
        "phone": "+91 98801 77665",
        "location": "Noida, India",
        "linkedin": "https://linkedin.com/in/vikram-singh-devops",
        "github": "https://github.com/vikram-devops",
        "summary": "Senior DevOps & Cloud Infrastructure Engineer with 4 years of experience orchestrating Kubernetes clusters, Terraform automation, and AWS cloud security.",
        "skills": "AWS, Kubernetes, Docker, CI/CD, Terraform, Linux, Bash/Shell, Python, Git, Cybersecurity, Jenkins, Prometheus",
        "education": "B.E. in Electronics & Communication\nDelhi Technological University | CGPA: 8.5/10 | Graduated: 2020",
        "experience": """Senior DevOps Engineer | Enterprise Cloud (Jun 2020 - Present)
• Automated infrastructure provisioning across AWS using Terraform (IaC), eliminating 90% of manual deployment errors.
• Managed production Kubernetes clusters (k8s) hosting 40+ microservices with 99.99% uptime.
• Implemented automated Jenkins and GitHub Actions CI/CD pipelines reducing deployment cycle time from 2 hours to 8 minutes.""",
        "projects": """Zero-Downtime Multi-Region Kubernetes Deployment
• Architected high-availability Kubernetes cluster on AWS EKS with ArgoCD GitOps and Prometheus monitoring.""",
        "certifications": "• AWS Certified Solutions Architect - Associate\n• Certified Kubernetes Administrator (CKA)\n• HashiCorp Certified: Terraform Associate"
    },
    {
        "filename": "Ananya_Roy_Fresher_Engineer.pdf",
        "format": "pdf",
        "name": "Ananya Roy",
        "email": "ananya.roy@email.com",
        "phone": "+91 96111 22334",
        "location": "Bengaluru, India",
        "linkedin": "https://linkedin.com/in/ananya-roy",
        "github": "https://github.com/ananya-roy-cs",
        "summary": "Enthusiastic Computer Science graduate eager to apply strong foundations in Python, Data Structures & Algorithms, Machine Learning, and Web Development.",
        "skills": "Python, C++, Data Structures & Algorithms, Machine Learning, Scikit-Learn, Pandas, NumPy, HTML/CSS, SQL, Git",
        "education": "B.E. in Computer Science & Engineering\nVTU Belagavi | CGPA: 8.7/10 | Graduated: 2024",
        "experience": """Software Engineering Intern | TechStart Solutions (Jan 2024 - Jun 2024)
• Assisted in developing predictive regression models with Scikit-Learn and Pandas.
• Implemented unit tests and resolved 30+ bug tickets in core Python application codebase.""",
        "projects": """Smart Attendance System via Face Recognition
• Built an automated attendance system using Python, OpenCV, and SQLite with 96% recognition accuracy.
• Designed clean user dashboard with Streamlit and Matplotlib.""",
        "certifications": "• Python for Everybody Specialization (University of Michigan / Coursera)\n• HackerRank 5-Star Python & SQL Badges"
    }
]


def generate_all_samples(output_dir: str = "data/sample_resumes"):
    """Generates sample resumes in PDF, DOCX, and TXT formats."""
    os.makedirs(output_dir, exist_ok=True)

    for cand in SAMPLE_CANDIDATES:
        out_path = os.path.join(output_dir, cand["filename"])
        fmt = cand["format"]

        full_content = f"""{cand['name']}
Email: {cand['email']} | Phone: {cand['phone']} | Location: {cand['location']}
LinkedIn: {cand['linkedin']} | GitHub: {cand['github']}

PROFESSIONAL SUMMARY
{cand['summary']}

TECHNICAL SKILLS
{cand['skills']}

EDUCATION
{cand['education']}

WORK EXPERIENCE
{cand['experience']}

KEY PROJECTS
{cand['projects']}

CERTIFICATIONS & AWARDS
{cand['certifications']}
"""

        if fmt == "pdf":
            # Create standard PDF using PyMuPDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)  # A4 size
            
            # Simple clean layout
            p_text = full_content.strip()
            rect = fitz.Rect(50, 50, 545, 792)
            page.insert_textbox(rect, p_text, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1))
            doc.save(out_path)
            doc.close()
            print(f"Generated PDF: {out_path}")

        elif fmt == "docx":
            # Create DOCX
            doc = docx.Document()
            doc.add_heading(cand['name'], level=0)
            doc.add_paragraph(f"Email: {cand['email']} | Phone: {cand['phone']} | Location: {cand['location']}")
            doc.add_paragraph(f"LinkedIn: {cand['linkedin']} | GitHub: {cand['github']}")
            
            doc.add_heading("Professional Summary", level=1)
            doc.add_paragraph(cand['summary'])

            doc.add_heading("Technical Skills", level=1)
            doc.add_paragraph(cand['skills'])

            doc.add_heading("Education", level=1)
            doc.add_paragraph(cand['education'])

            doc.add_heading("Work Experience", level=1)
            doc.add_paragraph(cand['experience'])

            doc.add_heading("Projects", level=1)
            doc.add_paragraph(cand['projects'])

            doc.add_heading("Certifications", level=1)
            doc.add_paragraph(cand['certifications'])

            doc.save(out_path)
            print(f"Generated DOCX: {out_path}")

        elif fmt == "txt":
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            print(f"Generated TXT: {out_path}")


if __name__ == "__main__":
    generate_all_samples()

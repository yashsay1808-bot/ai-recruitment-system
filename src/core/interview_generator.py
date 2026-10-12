"""
AI-Powered Interview Question Generator
Synthesizes contextual interview questions tailored to:
- Matched Technical Skills
- Candidate Projects & Tech Stacks
- Skill Gaps / Missing Competencies (Probing Questions)
- Candidate Experience Level (Fresher vs Mid/Senior)
- Behavioral & HR Competencies
Provides evaluation tips and expected answers for recruiters.
"""

from typing import Dict, List, Any, Optional

# Knowledge bank of skill-specific technical interview questions
SKILL_QUESTION_BANK: Dict[str, List[Dict[str, str]]] = {
    "Python": [
        {
            "question": "How do Python's GIL (Global Interpreter Lock) and memory management (garbage collection/reference counting) impact multi-threading?",
            "difficulty": "Medium",
            "eval_criteria": "Candidate should explain GIL prevents multiple threads from executing Python bytecodes simultaneously, and propose multiprocessing or asyncio for concurrency."
        },
        {
            "question": "What is the difference between `@classmethod`, `@staticmethod`, and regular instance methods?",
            "difficulty": "Easy",
            "eval_criteria": "Look for clarity on `self` vs `cls` and practical use cases for factory methods."
        }
    ],
    "Machine Learning": [
        {
            "question": "How do you detect and mitigate overfitting in a high-dimensional machine learning pipeline?",
            "difficulty": "Medium",
            "eval_criteria": "Expect mentions of Cross-Validation, Regularization (L1/L2), Feature Selection/PCA, Dropout, and data augmentation."
        },
        {
            "question": "When evaluating an imbalanced classification problem, why is Accuracy misleading, and which metrics would you prioritize?",
            "difficulty": "Medium",
            "eval_criteria": "Candidate should discuss Precision-Recall AUC, F1-Score, ROC-AUC, Confusion Matrix, and SMOTE/cost-sensitive learning."
        }
    ],
    "Natural Language Processing": [
        {
            "question": "Explain how modern Transformer attention mechanisms (e.g., BERT/GPT) differ from classical TF-IDF and n-gram approaches.",
            "difficulty": "Hard",
            "eval_criteria": "Candidate should highlight contextual embeddings vs bag-of-words, self-attention matrix calculation, and bidirectional vs autoregressive pre-training."
        },
        {
            "question": "How would you handle domain-specific terminology and out-of-vocabulary (OOV) tokens in an NLP pipeline?",
            "difficulty": "Medium",
            "eval_criteria": "Look for subword tokenization (Byte-Pair Encoding, WordPiece), custom embeddings, and domain fine-tuning."
        }
    ],
    "Deep Learning": [
        {
            "question": "What causes vanishing and exploding gradients in deep neural networks, and how do modern architectures solve this?",
            "difficulty": "Medium",
            "eval_criteria": "Expect explanations of ReLU/GELU activations, Batch Normalization, Layer Normalization, Residual skip connections, and gradient clipping."
        }
    ],
    "Large Language Models": [
        {
            "question": "Explain the architecture of a Retrieval-Augmented Generation (RAG) system and how you evaluate retrieval quality vs generation hallucination.",
            "difficulty": "Hard",
            "eval_criteria": "Look for chunking strategies, vector databases, reranking (cross-encoders), context window management, and Ragas/TruLens evaluation metrics."
        }
    ],
    "FastAPI": [
        {
            "question": "How does FastAPI achieve high performance using `asyncio` and Pydantic data validation?",
            "difficulty": "Medium",
            "eval_criteria": "Candidate should mention ASGI servers (Uvicorn), non-blocking I/O event loops, and type-hint serialization with Pydantic."
        }
    ],
    "Flask": [
        {
            "question": "How do application context and request context work in Flask, and how would you structure a scalable modular app?",
            "difficulty": "Medium",
            "eval_criteria": "Look for Blueprint architecture, g object, application factories, and WSGI middleware."
        }
    ],
    "React": [
        {
            "question": "Explain how React's Virtual DOM reconciliation and Fiber architecture work under the hood.",
            "difficulty": "Medium",
            "eval_criteria": "Candidate should explain diffing algorithm, key prop necessity, and time-slicing/concurrent rendering."
        },
        {
            "question": "When would you use `useCallback` and `useMemo` versus letting components re-render naturally?",
            "difficulty": "Medium",
            "eval_criteria": "Look for understanding of referential equality, expensive computations, and avoiding premature optimization."
        }
    ],
    "SQL": [
        {
            "question": "How do database indexes (B-Tree vs Hash) accelerate queries, and what are the trade-offs on WRITE operations?",
            "difficulty": "Medium",
            "eval_criteria": "Candidate should explain tree traversals, O(log N) lookup, clustered vs non-clustered indexing, and index maintenance overhead during INSERT/UPDATE."
        },
        {
            "question": "Explain the ACID properties of a transactional relational database with a real-world banking scenario.",
            "difficulty": "Easy",
            "eval_criteria": "Atomicity, Consistency, Isolation, Durability explained clearly."
        }
    ],
    "Docker": [
        {
            "question": "How do Docker multi-stage builds help optimize production container image security and footprint?",
            "difficulty": "Medium",
            "eval_criteria": "Look for separation of build dependencies from minimal runtime base images (e.g. Alpine/Distroless)."
        }
    ],
    "AWS": [
        {
            "question": "How would you design a scalable, fault-tolerant web application using AWS services (VPC, EC2/ECS, RDS, S3, CloudFront)?",
            "difficulty": "Hard",
            "eval_criteria": "Candidate should cover multi-AZ deployment, Auto-Scaling Groups, Application Load Balancers, read replicas, and secure IAM roles."
        }
    ],
    "Kubernetes": [
        {
            "question": "Explain the role of Kubernetes Pods, Deployments, Services (ClusterIP vs NodePort vs Ingress), and Horizontal Pod Autoscaling (HPA).",
            "difficulty": "Hard",
            "eval_criteria": "Candidate should describe declarative desired state, control loop reconciliation, and service routing."
        }
    ]
}


class InterviewQuestionGenerator:
    """Generates custom interview questionnaires tailored to candidate profile and JD."""

    def generate_questionnaire(
        self,
        candidate_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        gap_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes categorized interview questions with answer guidelines.
        """
        matched_skills = gap_results.get("matched_skills", [])
        missing_skills = gap_results.get("missing_skills", [])
        projects = candidate_data.get("projects", [])
        exp_years = candidate_data.get("experience", {}).get("years_of_experience", 0.0)
        is_fresher = candidate_data.get("experience", {}).get("is_fresher", False)

        # 1. Technical Domain Questions (from matched skills)
        technical_questions = []
        for skill in matched_skills:
            if skill in SKILL_QUESTION_BANK:
                for q in SKILL_QUESTION_BANK[skill]:
                    if len(technical_questions) < 5:
                        technical_questions.append({
                            "skill": skill,
                            "question": q["question"],
                            "difficulty": q["difficulty"],
                            "eval_criteria": q["eval_criteria"]
                        })

        # Fallback technical questions if few matched in bank
        if len(technical_questions) < 3:
            for skill in matched_skills[:3]:
                technical_questions.append({
                    "skill": skill,
                    "question": f"Can you walk us through a real-world challenge you faced while implementing {skill} and how you debugged it?",
                    "difficulty": "Medium",
                    "eval_criteria": f"Evaluate depth of hands-on experience, edge-case handling, and best practices with {skill}."
                })

        # 2. Project-Specific Deep-Dive Questions
        project_questions = []
        for p in projects[:3]:
            title = p.get("title", "Project")
            skills_used = ", ".join(p.get("skills_used", [])) or "the chosen tech stack"
            project_questions.append({
                "project_title": title,
                "question": f"In your project '{title}', what key architectural decisions did you make using {skills_used}, and how did you measure its success or performance?",
                "eval_criteria": "Assess architectural ownership, trade-off awareness, quantitative impact, and testing strategy."
            })
            project_questions.append({
                "project_title": title,
                "question": f"If you had to scale '{title}' to handle 100x user traffic or data volume, what bottlenecks would arise and how would you re-architect it?",
                "eval_criteria": "Look for caching strategies, asynchronous message queues, database indexing/sharding, and horizontal scaling."
            })

        # 3. Skill Gap & Adaptive Probing Questions
        gap_probing_questions = []
        for missing in missing_skills[:3]:
            gap_probing_questions.append({
                "missing_skill": missing,
                "question": f"This position heavily utilizes {missing}, which is not prominent on your resume. Have you had exposure to {missing} or equivalent alternatives, and how would you ramp up?",
                "eval_criteria": f"Evaluate learning agility, enthusiasm, and relevant conceptual fundamentals applicable to {missing}."
            })

        # 4. Behavioral & HR Cultural Fit Questions
        behavioral_questions = []
        if is_fresher:
            behavioral_questions = [
                {
                    "question": "Tell us about a technical problem during your academic coursework or project that initially stumped you. How did you research and resolve it?",
                    "eval_criteria": "Assesses problem-solving persistence, self-learning capability, and resourcefulness."
                },
                {
                    "question": "How do you prioritize deadlines when juggling multiple project deliverables or coursework?",
                    "eval_criteria": "Assesses time management and communication under pressure."
                },
                {
                    "question": "Why are you interested in this specific role and our organization?",
                    "eval_criteria": "Evaluates genuine motivation, company research, and career alignment."
                }
            ]
        else:
            behavioral_questions = [
                {
                    "question": "Describe a time when you strongly disagreed with a teammate or lead regarding a technical implementation. How did you navigate the discussion and reach alignment?",
                    "eval_criteria": "Look for emotional intelligence, constructive communication, and data-driven debate."
                },
                {
                    "question": "Tell us about a production incident or bug that caused downtime. What was your root cause analysis (RCA) and post-mortem action?",
                    "eval_criteria": "Evaluates accountability, composure under crisis, and preventive engineering mindset."
                },
                {
                    "question": "How do you mentor junior engineers or ensure high code quality and test coverage in your team?",
                    "eval_criteria": "Evaluates leadership potential, code review hygiene, and team collaboration."
                }
            ]

        return {
            "technical_questions": technical_questions[:6],
            "project_questions": project_questions[:4],
            "gap_probing_questions": gap_probing_questions[:4],
            "behavioral_questions": behavioral_questions
        }

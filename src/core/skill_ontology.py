"""
Skill Ontology & Synonym Knowledge Base
Provides comprehensive tech skill dictionaries, alias normalization,
fuzzy matching, and category classification.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from difflib import SequenceMatcher
from functools import lru_cache

# Master Skill Dictionary: Canonical Name -> Dict(aliases, category)
SKILL_ONTOLOGY: Dict[str, Dict] = {
    # ------------------ Programming Languages ------------------
    "Python": {
        "aliases": ["python", "python 3", "python3", "python programming", "py"],
        "category": "Programming Languages"
    },
    "JavaScript": {
        "aliases": ["javascript", "js", "ecmascript", "es6", "es6+", "vanilla js"],
        "category": "Programming Languages"
    },
    "TypeScript": {
        "aliases": ["typescript", "ts"],
        "category": "Programming Languages"
    },
    "Java": {
        "aliases": ["java", "core java", "java 8", "java 11", "java 17", "j2ee"],
        "category": "Programming Languages"
    },
    "C++": {
        "aliases": ["c++", "cpp", "c plus plus", "c/c++"],
        "category": "Programming Languages"
    },
    "C": {
        "aliases": ["c language", "ansi c"],
        "category": "Programming Languages"
    },
    "C#": {
        "aliases": ["c#", "c-sharp", "csharp", ".net c#"],
        "category": "Programming Languages"
    },
    "Go": {
        "aliases": ["go", "golang"],
        "category": "Programming Languages"
    },
    "Rust": {
        "aliases": ["rust", "rustlang"],
        "category": "Programming Languages"
    },
    "PHP": {
        "aliases": ["php", "php7", "php8"],
        "category": "Programming Languages"
    },
    "Ruby": {
        "aliases": ["ruby", "ruby on rails", "ror"],
        "category": "Programming Languages"
    },
    "Swift": {
        "aliases": ["swift", "swiftui"],
        "category": "Programming Languages"
    },
    "Kotlin": {
        "aliases": ["kotlin", "android kotlin"],
        "category": "Programming Languages"
    },
    "SQL": {
        "aliases": ["sql", "structured query language", "pl/sql", "t-sql", "ansi sql"],
        "category": "Programming Languages"
    },
    "R": {
        "aliases": ["r programming", "r language", "r-project"],
        "category": "Programming Languages"
    },
    "Scala": {
        "aliases": ["scala"],
        "category": "Programming Languages"
    },
    "Bash/Shell": {
        "aliases": ["bash", "shell", "shell scripting", "sh", "zsh", "powershell"],
        "category": "Programming Languages"
    },

    # ------------------ AI, Machine Learning & Deep Learning ------------------
    "Machine Learning": {
        "aliases": ["machine learning", "ml", "machine-learning", "statistical learning", "supervised learning", "unsupervised learning"],
        "category": "AI & Machine Learning"
    },
    "Deep Learning": {
        "aliases": ["deep learning", "dl", "deep-learning", "neural networks", "ann", "cnn", "rnn", "lstm"],
        "category": "AI & Machine Learning"
    },
    "Natural Language Processing": {
        "aliases": ["natural language processing", "nlp", "text mining", "text analytics", "computational linguistics", "nlu", "nlg"],
        "category": "AI & Machine Learning"
    },
    "Large Language Models": {
        "aliases": ["large language models", "llm", "llms", "genai", "generative ai", "rag", "retrieval augmented generation", "prompt engineering", "langchain", "llamaindex"],
        "category": "AI & Machine Learning"
    },
    "Computer Vision": {
        "aliases": ["computer vision", "cv", "opencv", "image processing", "object detection", "yolo", "image segmentation"],
        "category": "AI & Machine Learning"
    },
    "Scikit-Learn": {
        "aliases": ["scikit-learn", "sklearn", "scikit learn"],
        "category": "AI & Machine Learning"
    },
    "TensorFlow": {
        "aliases": ["tensorflow", "tf", "tensorflow 2", "tf2"],
        "category": "AI & Machine Learning"
    },
    "PyTorch": {
        "aliases": ["pytorch", "torch"],
        "category": "AI & Machine Learning"
    },
    "Keras": {
        "aliases": ["keras"],
        "category": "AI & Machine Learning"
    },
    "Hugging Face": {
        "aliases": ["hugging face", "huggingface", "transformers", "bert", "gpt", "roberta", "t5"],
        "category": "AI & Machine Learning"
    },
    "Reinforcement Learning": {
        "aliases": ["reinforcement learning", "rl", "q-learning", "deep rl"],
        "category": "AI & Machine Learning"
    },
    "Spacy/NLTK": {
        "aliases": ["spacy", "nltk", "gensim", "textblob"],
        "category": "AI & Machine Learning"
    },
    "MLOps": {
        "aliases": ["mlops", "mlflow", "kubeflow", "model deployment", "model monitoring", "dvc", "wandb"],
        "category": "AI & Machine Learning"
    },
    "Feature Engineering": {
        "aliases": ["feature engineering", "data preprocessing", "data cleaning", "dimensionality reduction", "pca"],
        "category": "AI & Machine Learning"
    },

    # ------------------ Data Science & Analytics ------------------
    "Pandas": {
        "aliases": ["pandas", "pandas dataframe"],
        "category": "Data Science & Analytics"
    },
    "NumPy": {
        "aliases": ["numpy"],
        "category": "Data Science & Analytics"
    },
    "Data Visualization": {
        "aliases": ["data visualization", "matplotlib", "seaborn", "plotly", "bokeh", "data viz"],
        "category": "Data Science & Analytics"
    },
    "Power BI": {
        "aliases": ["power bi", "powerbi", "ms power bi", "dax"],
        "category": "Data Science & Analytics"
    },
    "Tableau": {
        "aliases": ["tableau", "tableau desktop", "tableau server"],
        "category": "Data Science & Analytics"
    },
    "Apache Spark": {
        "aliases": ["apache spark", "spark", "pyspark", "spark sql", "spark streaming"],
        "category": "Data Science & Analytics"
    },
    "Big Data": {
        "aliases": ["big data", "hadoop", "hdfs", "hive", "mapreduce"],
        "category": "Data Science & Analytics"
    },
    "ETL": {
        "aliases": ["etl", "elt", "data pipeline", "data pipelines", "apache airflow", "airflow"],
        "category": "Data Science & Analytics"
    },
    "Statistics": {
        "aliases": ["statistics", "statistical analysis", "hypothesis testing", "a/b testing", "probability", "regression analysis"],
        "category": "Data Science & Analytics"
    },

    # ------------------ Web & Backend Frameworks ------------------
    "FastAPI": {
        "aliases": ["fastapi", "fast-api"],
        "category": "Web & Backend Frameworks"
    },
    "Flask": {
        "aliases": ["flask"],
        "category": "Web & Backend Frameworks"
    },
    "Django": {
        "aliases": ["django", "django rest framework", "drf"],
        "category": "Web & Backend Frameworks"
    },
    "Spring Boot": {
        "aliases": ["spring boot", "spring", "spring mvc", "springboot"],
        "category": "Web & Backend Frameworks"
    },
    "Node.js": {
        "aliases": ["node.js", "nodejs", "node"],
        "category": "Web & Backend Frameworks"
    },
    "Express.js": {
        "aliases": ["express.js", "express", "expressjs"],
        "category": "Web & Backend Frameworks"
    },
    "ASP.NET": {
        "aliases": ["asp.net", ".net core", "dotnet", ".net", "asp.net core"],
        "category": "Web & Backend Frameworks"
    },
    "REST API": {
        "aliases": ["rest api", "rest apis", "restful api", "restful web services", "rest", "api development", "swagger", "openapi"],
        "category": "Web & Backend Frameworks"
    },
    "GraphQL": {
        "aliases": ["graphql", "apollo graphql"],
        "category": "Web & Backend Frameworks"
    },
    "Microservices": {
        "aliases": ["microservices", "microservice architecture", "micro-services", "soa", "service oriented architecture"],
        "category": "Web & Backend Frameworks"
    },

    # ------------------ Frontend Technologies ------------------
    "React": {
        "aliases": ["react", "react.js", "reactjs", "react native"],
        "category": "Frontend Technologies"
    },
    "Angular": {
        "aliases": ["angular", "angularjs", "angular 2+"],
        "category": "Frontend Technologies"
    },
    "Vue.js": {
        "aliases": ["vue.js", "vue", "vuejs", "nuxt", "nuxtjs"],
        "category": "Frontend Technologies"
    },
    "Next.js": {
        "aliases": ["next.js", "nextjs", "next"],
        "category": "Frontend Technologies"
    },
    "HTML/CSS": {
        "aliases": ["html", "html5", "css", "css3", "sass", "scss", "tailwind", "tailwind css", "bootstrap"],
        "category": "Frontend Technologies"
    },
    "Redux": {
        "aliases": ["redux", "redux toolkit", "zustand", "mobx"],
        "category": "Frontend Technologies"
    },

    # ------------------ Databases & Storage ------------------
    "DBMS": {
        "aliases": ["dbms", "rdbms", "database management", "database management system", "relational database"],
        "category": "Databases & Storage"
    },
    "PostgreSQL": {
        "aliases": ["postgresql", "postgres", "pgsql"],
        "category": "Databases & Storage"
    },
    "MySQL": {
        "aliases": ["mysql", "mariadb"],
        "category": "Databases & Storage"
    },
    "MongoDB": {
        "aliases": ["mongodb", "mongo", "nosql mongodb"],
        "category": "Databases & Storage"
    },
    "Redis": {
        "aliases": ["redis", "in-memory cache"],
        "category": "Databases & Storage"
    },
    "Elasticsearch": {
        "aliases": ["elasticsearch", "elastic search", "elk stack", "opensearch"],
        "category": "Databases & Storage"
    },
    "NoSQL": {
        "aliases": ["nosql", "dynamodb", "cassandra", "couchdb"],
        "category": "Databases & Storage"
    },
    "SQLite": {
        "aliases": ["sqlite", "sqlite3"],
        "category": "Databases & Storage"
    },

    # ------------------ Cloud & DevOps ------------------
    "AWS": {
        "aliases": ["aws", "amazon web services", "amazon cloud", "ec2", "amazon s3", "aws s3", "aws lambda", "rds", "cloudformation"],
        "category": "Cloud & DevOps"
    },
    "Google Cloud": {
        "aliases": ["google cloud", "gcp", "google cloud platform", "bigquery", "vertex ai", "gke"],
        "category": "Cloud & DevOps"
    },
    "Azure": {
        "aliases": ["azure", "microsoft azure", "azure devops", "azure cloud"],
        "category": "Cloud & DevOps"
    },
    "Docker": {
        "aliases": ["docker", "containerization", "docker compose", "containers"],
        "category": "Cloud & DevOps"
    },
    "Kubernetes": {
        "aliases": ["kubernetes", "k8s", "container orchestration", "helm"],
        "category": "Cloud & DevOps"
    },
    "CI/CD": {
        "aliases": ["ci/cd", "ci-cd", "continuous integration", "continuous deployment", "jenkins", "github actions", "gitlab ci"],
        "category": "Cloud & DevOps"
    },
    "Terraform": {
        "aliases": ["terraform", "infrastructure as code", "infrastructure-as-code", "ansible"],
        "category": "Cloud & DevOps"
    },
    "Linux": {
        "aliases": ["linux", "ubuntu", "centos", "redhat", "unix", "debian"],
        "category": "Cloud & DevOps"
    },
    "Git": {
        "aliases": ["git", "github", "gitlab", "version control", "vcs", "bitbucket"],
        "category": "Cloud & DevOps"
    },

    # ------------------ Software Engineering & Architecture ------------------
    "Data Structures & Algorithms": {
        "aliases": ["data structures", "algorithms", "dsa", "data structures and algorithms", "algorithm design"],
        "category": "Software Engineering"
    },
    "Object-Oriented Programming": {
        "aliases": ["oop", "oops", "object oriented programming", "object-oriented design", "ood"],
        "category": "Software Engineering"
    },
    "System Design": {
        "aliases": ["system design", "software architecture", "scalability", "high availability", "distributed systems"],
        "category": "Software Engineering"
    },
    "Agile/Scrum": {
        "aliases": ["agile", "scrum", "kanban", "sprint planning", "jira"],
        "category": "Software Engineering"
    },
    "Testing/QA": {
        "aliases": ["unit testing", "pytest", "junit", "selenium", "integration testing", "tdd", "test driven development", "automation testing"],
        "category": "Software Engineering"
    },
    "Cybersecurity": {
        "aliases": ["cybersecurity", "information security", "infosec", "owasp", "penetration testing", "cryptography", "network security"],
        "category": "Software Engineering"
    }
}

# Build reverse lookup map: lowercase alias -> canonical skill name
_ALIAS_LOOKUP: Dict[str, str] = {}
for canonical, data in SKILL_ONTOLOGY.items():
    _ALIAS_LOOKUP[canonical.lower()] = canonical
    for alias in data["aliases"]:
        _ALIAS_LOOKUP[alias.lower()] = canonical


def _build_alias_patterns():
    """Compiles one boundary-aware regex per alias, longest alias first (done once at import)."""
    patterns = []
    for alias in sorted(_ALIAS_LOOKUP.keys(), key=len, reverse=True):
        # For short 1-3 letter aliases (like C, R, Go, JS, ML), use strict boundary
        if len(alias) <= 3:
            pat = rf'(?<![a-zA-Z0-9\+\#]){re.escape(alias)}(?![a-zA-Z0-9\+\#])'
        else:
            pat = rf'(?<![a-zA-Z0-9]){re.escape(alias)}(?![a-zA-Z0-9])'
        patterns.append((alias, re.compile(pat)))
    return patterns


_ALIAS_PATTERNS = _build_alias_patterns()


def get_all_canonical_skills() -> List[str]:
    """Returns list of all canonical skill names."""
    return sorted(list(SKILL_ONTOLOGY.keys()))


def normalize_skill(skill_str: str) -> Optional[str]:
    """
    Normalizes a given skill query or phrase to its canonical ontology name.
    Handles exact alias match, stripped punctuation, and fuzzy fallback.
    """
    if not skill_str or not isinstance(skill_str, str):
        return None
    return _normalize_cached(skill_str)


@lru_cache(maxsize=4096)
def _normalize_cached(skill_str: str) -> Optional[str]:
    """Memoized normalization; the fuzzy fallback scans every alias, so misses are costly."""
    cleaned = skill_str.strip().lower()
    if cleaned in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[cleaned]
    
    # Try removing special chars like dots, slashes, hyphens
    sub_cleaned = re.sub(r'[\.\-\_\/\s]+', ' ', cleaned).strip()
    if sub_cleaned in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[sub_cleaned]
    
    # Fast fuzzy match against aliases
    best_match = None
    best_score = 0.0
    for alias, canonical in _ALIAS_LOOKUP.items():
        if len(alias) >= 3 and len(cleaned) >= 3:
            ratio = SequenceMatcher(None, cleaned, alias).ratio()
            if ratio > 0.88 and ratio > best_score:
                best_score = ratio
                best_match = canonical
                
    return best_match


def get_skill_category(skill_name: str) -> str:
    """Returns the high-level category of a skill."""
    canonical = normalize_skill(skill_name)
    if canonical and canonical in SKILL_ONTOLOGY:
        return SKILL_ONTOLOGY[canonical]["category"]
    return "Other / Domain Specific"


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extracts all known skills from free-form text using phrase boundary matching
    and synonym expansion.
    """
    if not text:
        return []
    
    found_skills: Set[str] = set()
    lower_text = " " + text.lower() + " "
    # Replace non-alphanumeric (except +, #, ., /) with space for safe tokenizing
    sanitized_text = re.sub(r'[^a-z0-9\+\#\.\/\-\s]', ' ', lower_text)

    # Aliases are pre-sorted by length descending so longer phrases match first
    for alias, pattern in _ALIAS_PATTERNS:
        if pattern.search(sanitized_text):
            found_skills.add(_ALIAS_LOOKUP[alias])
            # Remove matched portion to avoid substring overlap
            sanitized_text = pattern.sub(' ', sanitized_text)

    return sorted(list(found_skills))


def match_skills(
    jd_skills: List[str], 
    resume_skills: List[str]
) -> Dict[str, any]:
    """
    Matches candidate skills against required JD skills using exact synonym matching
    and semantic partial matching.
    """
    norm_jd = []
    for s in jd_skills:
        canonical = normalize_skill(s)
        norm_jd.append(canonical if canonical else s.strip())
        
    norm_resume = []
    for s in resume_skills:
        canonical = normalize_skill(s)
        norm_resume.append(canonical if canonical else s.strip())
        
    set_resume = set(norm_resume)
    
    matched: List[str] = []
    partially_matched: List[Dict[str, any]] = []
    missing: List[str] = []
    
    # Specific related pairs where possessing skill A gives partial credit for skill B
    related_pairs = {
        ("Machine Learning", "Deep Learning"),
        ("Machine Learning", "Natural Language Processing"),
        ("Deep Learning", "Large Language Models"),
        ("Deep Learning", "Computer Vision"),
        ("FastAPI", "Flask"),
        ("FastAPI", "Django"),
        ("Flask", "Django"),
        ("React", "Next.js"),
        ("React", "TypeScript"),
        ("PostgreSQL", "MySQL"),
        ("AWS", "Google Cloud"),
        ("AWS", "Azure"),
        ("Google Cloud", "Azure"),
        ("Pandas", "NumPy"),
        ("Docker", "Kubernetes")
    }

    for req_skill in norm_jd:
        if req_skill in set_resume:
            matched.append(req_skill)
        else:
            partial_found = False
            
            for res_skill in set_resume:
                if (req_skill, res_skill) in related_pairs or (res_skill, req_skill) in related_pairs:
                    req_cat = get_skill_category(req_skill)
                    partially_matched.append({
                        "required_skill": req_skill,
                        "related_candidate_skill": res_skill,
                        "similarity_reason": f"Adjacent domain competency under {req_cat}"
                    })
                    partial_found = True
                    break
                        
            if not partial_found:
                missing.append(req_skill)
                
    total_req = len(norm_jd)
    if total_req > 0:
        raw_score = (len(matched) * 1.0 + len(partially_matched) * 0.5) / total_req
        match_percentage = round(min(1.0, raw_score) * 100, 1)
    else:
        match_percentage = 100.0 if len(resume_skills) > 0 else 0.0

    return {
        "matched": sorted(list(set(matched))),
        "partially_matched": partially_matched,
        "missing": sorted(list(set(missing))),
        "total_required": total_req,
        "match_percentage": match_percentage
    }

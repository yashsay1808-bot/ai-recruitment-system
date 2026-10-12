"""
Hybrid RAG & Vector Semantic Talent Search
==========================================

Natural-language search over a pool of parsed resumes, for questions such as::

    "Find engineers with 3+ years in distributed systems who know Docker and deployed microservices on AWS"

Pipeline
--------
1. **Chunking** - every resume becomes searchable chunks tagged ``skills``, ``experience`` or ``projects``
   (plus lighter ``summary`` / ``education`` / ``certifications`` chunks).
2. **Query understanding** - extracts the experience requirement ("3+ years") and a list of *competencies*
   (concepts such as "distributed systems", tools such as Docker, and leftover keywords). Concepts are expanded
   with synonyms ("distributed systems" -> Kafka, gRPC, sharding, ...), so wording differences still match.
3. **Hybrid retrieval** - per chunk, a *dense* similarity and a *sparse* Okapi-BM25 score are fused::

       chunk_score = alpha * dense + (1 - alpha) * bm25          (alpha = 0.55)

   Dense = ``sentence-transformers`` (``all-MiniLM-L6-v2``) when available, otherwise TF-IDF cosine with word
   bigrams over the same tokens. The backend is chosen automatically and reported in every result.
4. **Candidate ranking** - chunk scores are aggregated per candidate and combined with *competency coverage*
   (is every facet of the query evidenced somewhere in the resume?) and an experience-fit factor.
5. **Explainable output** - relevance score, matched / missing competencies (with the section that proves each),
   and highlighted snippets (Markdown ``**bold**`` and HTML ``<mark>``).

Dependencies: ``numpy`` and ``scikit-learn`` (both already in requirements.txt). ``sentence-transformers`` is
optional; ``src.core.skill_ontology`` is used for skill aliases when importable. Set ``TALENT_RAG_DISABLE_ST=1`` to
skip loading the transformer model (e.g. offline environments), or ``TALENT_RAG_MODEL`` to choose another model.

Notes
-----
* Experience years are the resume's *total* years; the parser cannot attribute years to a specific domain, so
  "3+ years in distributed systems" is checked as (total years >= 3) AND (distributed-systems evidence present).
* Indexes are cached by content fingerprint, so repeated queries over the same pool (typical in Streamlit
  reruns) neither re-chunk nor re-embed.

Typical use
-----------
    from src.core.talent_rag import search_talent_pool

    hits = search_talent_pool("backend engineers with 3+ years in distributed systems who know Docker and AWS",
                              resumes, top_k=5)
    hits[0]["relevance_score"], hits[0]["matched_competencies"], hits[0]["snippets"][0]["markdown"]
"""

from __future__ import annotations

import hashlib
import html
import logging
import math
import os
import re
import threading
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

try:  # Optional: project ontology provides skill aliases.
    from src.core.skill_ontology import SKILL_ONTOLOGY as _ONTOLOGY
    from src.core.skill_ontology import extract_skills_from_text as _extract_skills
except Exception:  # pragma: no cover
    _ONTOLOGY = {}
    _extract_skills = None

logger = logging.getLogger(__name__)

__all__ = ["TalentRAG", "TalentIndex", "QueryPlan", "Competency", "search_talent_pool", "get_default_engine"]

DEFAULT_MODEL = "all-MiniLM-L6-v2"

# --------------------------------------------------------------------------------------
# Tokenisation
# --------------------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#./\-]*[a-z0-9+#]|[a-z0-9]")
_STOPWORDS = frozenset("""
a an and are as at be been being by for from has have had having he her his i if in into is it its of on or our
she so such than that the their them then there these they this those to was we were what when where which while
who whom whose why will with would you your yours not no nor but also can could should may might must shall do
does did done via per across within over under about above below between among during before after again
find show give list search looking look need needs want wants get fetch
candidate candidates engineer engineers developer developers people person someone anyone everybody professional
professionals resume resumes profile profiles applicant applicants
know knows knowing knowledge familiar familiarity experience experiences experienced year years yr yrs
least minimum min plus strong good great excellent solid proficient proficiency expertise expert hands-on handson
skilled skill skills ability able worked working work works using use used who's whos
""".split())
_TOKEN_ALIASES = {
    "nodejs": "node.js", "node-js": "node.js", "node": "node.js", "k8s": "kubernetes", "golang": "go",
    "postgres": "postgresql", "psql": "postgresql", "reactjs": "react", "react.js": "react", "vuejs": "vue",
    "vue.js": "vue", "js": "javascript", "ts": "typescript", "cicd": "ci/cd", "ci-cd": "ci/cd",
    "py": "python", "tf": "tensorflow", "mongo": "mongodb", "dockerized": "docker", "containerized": "container",
    "containerised": "container", "containerization": "container", "containerisation": "container",
}


def _stem(tok: str) -> str:
    if len(tok) <= 3 or not tok.isalpha():
        return tok
    if tok.endswith("ies") and len(tok) > 4:
        return tok[:-3] + "y"
    if tok.endswith("sses"):
        return tok[:-2]
    if tok.endswith("s") and not tok.endswith(("ss", "us", "is")):
        return tok[:-1]
    return tok


def _tokenize(text: str, with_bigrams: bool = True) -> List[str]:
    """Lower-cased, alias-normalised, lightly stemmed tokens; hyphen/slash parts and word bigrams are added."""
    out: List[str] = []
    seq: List[str] = []
    for raw in _TOKEN_RE.findall((text or "").lower()):
        tok = _TOKEN_ALIASES.get(raw, raw)
        if tok in _STOPWORDS or (len(tok) == 1 and tok not in {"c", "r"}):
            continue
        tok = _stem(tok)
        out.append(tok)
        seq.append(tok)
        if any(ch in tok for ch in "-/") and len(tok) > 3:
            for part in re.split(r"[-/]", tok):
                if len(part) > 1 and part not in _STOPWORDS:
                    out.append(_stem(part))
    if with_bigrams:
        out.extend(f"{a}_{b}" for a, b in zip(seq, seq[1:]))
    return out


# --------------------------------------------------------------------------------------
# Competency lexicon (query concept -> terms to look for in resumes)
# --------------------------------------------------------------------------------------
# "triggers": how a recruiter might phrase it; "core": direct evidence; "related": supporting evidence.
_LEXICON: Dict[str, Dict[str, List[str]]] = {
    "distributed systems": {
        "triggers": ["distributed systems", "distributed system", "distributed computing", "distributed architecture"],
        "core": ["distributed systems", "distributed system", "distributed computing", "distributed architecture",
                 "distributed database", "distributed training", "distributed processing"],
        "related": ["microservices", "kafka", "rabbitmq", "grpc", "message queue", "message broker", "event-driven",
                    "event driven", "sharding", "replication", "consensus", "cassandra", "zookeeper", "service mesh",
                    "horizontal scaling", "high availability", "fault tolerance", "eventual consistency",
                    "load balancing", "load balancer", "pub/sub", "celery", "spark", "scalable"],
    },
    "microservices": {
        "triggers": ["microservices", "microservice", "micro-services", "service oriented", "soa"],
        "core": ["microservices", "microservice", "micro-services", "service-oriented"],
        "related": ["api gateway", "service mesh", "grpc", "rest api", "docker", "kubernetes", "event-driven", "fastapi",
                    "spring boot", "kafka"],
    },
    "aws": {
        "triggers": ["aws", "amazon web services", "amazon aws"],
        "core": ["aws", "amazon web services", "ec2", "s3", "lambda", "ecs", "eks", "rds", "dynamodb", "cloudformation",
                 "sqs", "sns", "cloudwatch", "fargate"],
        "related": ["cloud", "terraform"],
    },
    "azure": {"triggers": ["azure"], "core": ["azure", "azure devops", "aks", "azure functions"], "related": ["cloud"]},
    "gcp": {"triggers": ["gcp", "google cloud"], "core": ["gcp", "google cloud", "bigquery", "gke", "cloud run"],
            "related": ["cloud"]},
    "cloud": {
        "triggers": ["cloud", "cloud native", "cloud-native"],
        "core": ["aws", "azure", "gcp", "google cloud", "cloud-native", "cloud native", "cloud computing"],
        "related": ["kubernetes", "terraform", "serverless", "ec2", "lambda"],
    },
    "docker": {
        "triggers": ["docker", "containers", "container", "containerization", "containerisation", "dockerized"],
        "core": ["docker", "dockerfile", "docker-compose", "docker compose", "containerization", "containerized",
                 "containerisation", "containers"],
        "related": ["kubernetes", "helm", "podman"],
    },
    "kubernetes": {
        "triggers": ["kubernetes", "k8s", "container orchestration"],
        "core": ["kubernetes", "k8s", "helm", "eks", "gke", "aks", "container orchestration"],
        "related": ["docker", "istio"],
    },
    "ci/cd": {
        "triggers": ["ci/cd", "cicd", "ci cd", "continuous integration", "continuous delivery", "continuous deployment"],
        "core": ["ci/cd", "continuous integration", "continuous delivery", "continuous deployment", "github actions",
                 "gitlab ci", "jenkins", "circleci", "argo cd", "argocd"],
        "related": ["pipeline", "automated deployment"],
    },
    "devops": {
        "triggers": ["devops", "sre", "site reliability", "infrastructure as code"],
        "core": ["devops", "sre", "site reliability", "infrastructure as code", "terraform", "ansible", "pulumi"],
        "related": ["ci/cd", "kubernetes", "docker", "monitoring", "prometheus", "grafana"],
    },
    "deployment": {
        "triggers": ["deployed", "deploy", "deployment", "deployments", "shipped", "ship", "production", "productionized",
                     "launched", "released"],
        "core": ["deployed", "deployment", "deploying", "shipped", "in production", "production environment",
                 "productionized", "productionised", "went live", "released to production", "rolled out", "launched"],
        "related": ["docker", "kubernetes", "ci/cd", "aws", "azure", "gcp", "heroku", "vercel", "live users"],
    },
    "machine learning": {
        "triggers": ["machine learning", "ml", "ml engineer"],
        "core": ["machine learning", "ml models", "scikit-learn", "sklearn", "xgboost", "model training", "ml pipeline"],
        "related": ["tensorflow", "pytorch", "pandas", "numpy", "feature engineering", "classification", "regression"],
    },
    "deep learning": {
        "triggers": ["deep learning", "neural network", "neural networks"],
        "core": ["deep learning", "neural network", "neural networks", "cnn", "rnn", "lstm", "transformer", "transformers"],
        "related": ["pytorch", "tensorflow", "keras", "gpu", "cuda"],
    },
    "nlp": {
        "triggers": ["nlp", "natural language processing", "language models", "llm", "llms"],
        "core": ["nlp", "natural language processing", "llm", "llms", "language model", "bert", "gpt", "rag",
                 "text classification", "sentiment analysis"],
        "related": ["transformers", "spacy", "huggingface", "hugging face", "embeddings"],
    },
    "computer vision": {
        "triggers": ["computer vision", "image processing", "opencv"],
        "core": ["computer vision", "opencv", "image processing", "object detection", "yolo", "image classification"],
        "related": ["cnn", "pytorch", "segmentation"],
    },
    "data engineering": {
        "triggers": ["data engineering", "data engineer", "data pipeline", "data pipelines", "etl"],
        "core": ["data engineering", "data pipeline", "data pipelines", "etl", "elt", "airflow", "data warehouse",
                 "data lake"],
        "related": ["spark", "kafka", "dbt", "snowflake", "bigquery", "redshift", "hadoop"],
    },
    "backend": {
        "triggers": ["backend", "back-end", "back end", "server-side", "server side"],
        "core": ["backend", "back-end", "server-side", "rest api", "rest apis", "api development", "fastapi", "django",
                 "flask", "spring boot", "express"],
        "related": ["postgresql", "mysql", "redis", "microservices"],
    },
    "frontend": {
        "triggers": ["frontend", "front-end", "front end", "ui development"],
        "core": ["frontend", "front-end", "react", "angular", "vue", "next.js", "html", "css", "tailwind"],
        "related": ["javascript", "typescript", "redux"],
    },
    "full stack": {
        "triggers": ["full stack", "full-stack", "fullstack"],
        "core": ["full stack", "full-stack", "fullstack"],
        "related": ["react", "node.js", "django", "next.js", "postgresql", "mongodb"],
    },
    "api design": {
        "triggers": ["api design", "rest api", "rest apis", "restful", "graphql", "apis"],
        "core": ["rest api", "rest apis", "restful", "graphql", "api design", "openapi", "swagger", "grpc"],
        "related": ["fastapi", "flask", "express", "django rest"],
    },
    "databases": {
        "triggers": ["databases", "database", "sql", "nosql"],
        "core": ["sql", "nosql", "postgresql", "mysql", "mongodb", "database design", "dynamodb", "cassandra", "oracle"],
        "related": ["redis", "elasticsearch", "indexing", "query optimization"],
    },
    "system design": {
        "triggers": ["system design", "architecture", "software architecture", "scalable systems", "scalability"],
        "core": ["system design", "software architecture", "architected", "scalable", "scalability", "high availability",
                 "low latency", "design patterns"],
        "related": ["microservices", "distributed", "caching", "load balancing"],
    },
    "security": {
        "triggers": ["security", "cybersecurity", "appsec"],
        "core": ["security", "cybersecurity", "oauth", "oauth2", "jwt", "penetration testing", "owasp", "encryption", "iam"],
        "related": ["authentication", "authorization"],
    },
    "testing": {
        "triggers": ["testing", "test automation", "qa"],
        "core": ["unit test", "unit tests", "pytest", "integration test", "integration tests", "test automation", "selenium",
                 "tdd", "jest"],
        "related": ["ci/cd", "coverage"],
    },
    "embedded": {
        "triggers": ["embedded", "iot", "firmware", "microcontroller", "microcontrollers"],
        "core": ["embedded", "iot", "firmware", "microcontroller", "microcontrollers", "rtos", "arduino", "esp32",
                 "raspberry pi", "stm32"],
        "related": ["c", "c++", "sensors", "mqtt"],
    },
    "mobile": {
        "triggers": ["mobile", "android", "ios", "react native", "flutter"],
        "core": ["android", "ios", "react native", "flutter", "kotlin", "swift", "mobile app"],
        "related": ["expo"],
    },
}

_EXP_PATTERNS = [
    re.compile(r"(?:at\s+least|minimum(?:\s+of)?|min\.?|over|more\s+than)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:-\s*\d+(?:\.\d+)?\s*)?(?:years?|yrs?)", re.I),
]


@dataclass
class Competency:
    """One facet of the recruiter's query that a candidate should evidence."""

    name: str
    core: List[str]
    related: List[str] = field(default_factory=list)
    weight: float = 1.0
    kind: str = "concept"  # concept | skill | keyword

    @property
    def all_terms(self) -> List[str]:
        return self.core + self.related


@dataclass
class QueryPlan:
    """Structured interpretation of a natural-language search query."""

    raw: str
    min_years: Optional[float]
    competencies: List[Competency]
    keywords: List[str]
    expansion_terms: List[str]


@dataclass
class _Chunk:
    idx: int
    resume_idx: int
    candidate_id: str
    candidate_name: str
    section: str
    text: str
    lower: str = ""
    tokens: List[str] = field(default_factory=list)


_CORE_SECTIONS = {"skills", "experience", "projects"}
_SECTION_FACTOR = {"skills": 1.0, "experience": 1.0, "projects": 1.0, "summary": 0.85, "education": 0.7,
                   "certifications": 0.8, "general": 0.85}


# --------------------------------------------------------------------------------------
# Chunking
# --------------------------------------------------------------------------------------
def _split_text(text: str, max_chars: int = 650) -> List[str]:
    """Split on blank lines, then pack lines into chunks of <= max_chars, keeping bullet groups together."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text or "") if b.strip()]
    if len(blocks) <= 1:
        blocks = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    chunks: List[str] = []
    cur = ""
    for block in blocks:
        block = re.sub(r"[ \t]+", " ", block)
        if len(block) > max_chars:
            if cur:
                chunks.append(cur)
                cur = ""
            for sent in re.split(r"(?<=[.;])\s+|\n", block):
                if cur and len(cur) + len(sent) + 1 > max_chars:
                    chunks.append(cur)
                    cur = ""
                cur = f"{cur} {sent}".strip()
            continue
        if cur and len(cur) + len(block) + 1 > max_chars:
            chunks.append(cur)
            cur = block
        else:
            cur = f"{cur}\n{block}".strip()
    if cur:
        chunks.append(cur)
    return [c for c in chunks if len(c) >= 12]


def _resume_id(resume: Dict[str, Any], idx: int) -> str:
    for key in ("id", "resume_id", "candidate_id", "file_name", "candidate_name"):
        if resume.get(key):
            return str(resume[key])
    return f"resume-{idx}"


def _years_of(resume: Dict[str, Any]) -> Optional[float]:
    exp = resume.get("experience")
    try:
        if isinstance(exp, dict) and exp.get("years_of_experience") is not None:
            return float(exp["years_of_experience"])
        if isinstance(exp, (int, float)):
            return float(exp)
        if resume.get("years_of_experience") is not None:
            return float(resume["years_of_experience"])
    except (TypeError, ValueError):
        return None
    return None


def chunk_resume(resume: Dict[str, Any], resume_idx: int) -> List[_Chunk]:
    """Convert one parsed resume into Skills / Experience / Projects (+ light summary, education, cert) chunks."""
    cid = _resume_id(resume, resume_idx)
    name = str(resume.get("candidate_name") or resume.get("name") or cid)
    sections = resume.get("sections") if isinstance(resume.get("sections"), dict) else {}
    pieces: List[Tuple[str, str]] = []

    skills = [str(s) for s in (resume.get("skills") or []) if str(s).strip()]
    for i in range(0, len(skills), 30):
        pieces.append(("skills", "Skills: " + ", ".join(skills[i:i + 30])))
    skills_text = sections.get("skills")
    if isinstance(skills_text, str) and skills_text.strip() and not skills:
        pieces.append(("skills", "Skills: " + re.sub(r"\s+", " ", skills_text.strip())[:700]))

    years = _years_of(resume)
    exp = resume.get("experience") if isinstance(resume.get("experience"), dict) else {}
    titles = ", ".join(str(t) for t in (exp.get("detected_titles") or []))
    header = "Experience"
    if years:
        header += f" ({years:g} years)"
    if titles:
        header += f" as {titles}"
    exp_text = sections.get("experience")
    if isinstance(exp_text, str) and exp_text.strip():
        for i, part in enumerate(_split_text(exp_text)):
            pieces.append(("experience", f"{header}: {part}" if i == 0 else part))
    elif years or titles:
        pieces.append(("experience", header + "."))

    projects = [p for p in (resume.get("projects") or []) if isinstance(p, dict)]
    for p in projects:
        used = ", ".join(str(s) for s in (p.get("skills_used") or []))
        text = f"Project: {p.get('title', '').strip()}. " + (f"Technologies: {used}. " if used else "") + str(p.get("description", "")).strip()
        pieces.append(("projects", text[:900]))
    proj_text = sections.get("projects")
    if not projects and isinstance(proj_text, str) and proj_text.strip():
        pieces.extend(("projects", part) for part in _split_text(proj_text))

    summary = sections.get("summary")
    if isinstance(summary, str) and summary.strip():
        pieces.append(("summary", re.sub(r"\s+", " ", summary.strip())[:600]))
    edu = resume.get("education")
    if isinstance(edu, dict):
        edu_bits = [str(v) for k, v in edu.items() if isinstance(v, (str, int, float)) and v]
        if edu_bits:
            pieces.append(("education", "Education: " + ", ".join(edu_bits)))
    certs = [str(c) for c in (resume.get("certifications") or []) if str(c).strip()]
    if certs:
        pieces.append(("certifications", "Certifications: " + "; ".join(certs)[:600]))

    if not any(sec in _CORE_SECTIONS for sec, _ in pieces):
        raw = resume.get("raw_text")
        if isinstance(raw, str) and raw.strip():
            pieces.extend(("general", part) for part in _split_text(raw, 600))

    chunks: List[_Chunk] = []
    for sec, text in pieces:
        text = text.strip()
        if text:
            chunks.append(_Chunk(idx=-1, resume_idx=resume_idx, candidate_id=cid, candidate_name=name, section=sec, text=text))
    return chunks


# --------------------------------------------------------------------------------------
# Dense backends
# --------------------------------------------------------------------------------------
_ST_LOCK = threading.Lock()
_ST_MODEL: Any = None
_ST_FAILED = False
_EMBED_CACHE: "OrderedDict[str, np.ndarray]" = OrderedDict()
_EMBED_CACHE_MAX = 50_000


def _load_sentence_model(model_name: str) -> Any:
    """Load the SentenceTransformer once per process. Returns ``None`` (and remembers) if unavailable."""
    global _ST_MODEL, _ST_FAILED
    if _ST_FAILED or os.environ.get("TALENT_RAG_DISABLE_ST", "").lower() in {"1", "true", "yes"}:
        return None
    with _ST_LOCK:
        if _ST_MODEL is not None and getattr(_ST_MODEL, "_talent_rag_name", None) == model_name:
            return _ST_MODEL
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            model = SentenceTransformer(model_name)
            model._talent_rag_name = model_name  # type: ignore[attr-defined]
            _ST_MODEL = model
            return model
        except Exception as exc:  # ImportError, offline model download failure, etc.
            _ST_FAILED = True
            logger.info("sentence-transformers unavailable (%s); using TF-IDF dense fallback", exc)
            return None


class _EmbeddingBackend:
    """Dense similarity with sentence embeddings (cosine on normalised vectors)."""

    name = "sentence-transformers"
    lo, hi = 0.15, 0.65  # MiniLM cosine range that maps to relevance 0 -> 1

    def __init__(self, embed: Callable[[List[str]], np.ndarray], label: str):
        self._embed = embed
        self.label = label
        self.matrix: Optional[np.ndarray] = None

    def fit(self, texts: List[str]) -> None:
        keys = [hashlib.sha1(t.encode("utf-8")).hexdigest() for t in texts]
        missing = [(i, t) for i, (k, t) in enumerate(zip(keys, texts)) if k not in _EMBED_CACHE]
        if missing:
            vectors = np.asarray(self._embed([t for _, t in missing]), dtype=np.float32)
            for (i, _), vec in zip(missing, vectors):
                _EMBED_CACHE[keys[i]] = vec
            while len(_EMBED_CACHE) > _EMBED_CACHE_MAX:
                _EMBED_CACHE.popitem(last=False)
        self.matrix = np.vstack([_EMBED_CACHE[k] for k in keys]) if keys else np.zeros((0, 1), dtype=np.float32)

    def similarities(self, query: str, expansion: str) -> np.ndarray:
        q = np.asarray(self._embed([query]), dtype=np.float32)[0]
        norm = np.linalg.norm(q) or 1.0
        return (self.matrix @ (q / norm)).astype(np.float64)

    def normalise(self, sims: np.ndarray) -> np.ndarray:
        return np.clip((sims - self.lo) / (self.hi - self.lo), 0.0, 1.0)


class _TfidfBackend:
    """TF-IDF (unigram + bigram) cosine fallback. The query is enriched with competency synonyms."""

    name = "tfidf"
    lo, hi = 0.0, 0.45

    def __init__(self) -> None:
        self.vectorizer: Any = None
        self.matrix: Any = None
        self.label = "tfidf-cosine"

    def fit(self, texts: List[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(analyzer=_tokenize, sublinear_tf=True, norm="l2")
        try:
            self.matrix = self.vectorizer.fit_transform(texts)
        except ValueError:  # empty vocabulary
            self.vectorizer, self.matrix = None, None

    def similarities(self, query: str, expansion: str) -> np.ndarray:
        if self.vectorizer is None or self.matrix is None:
            return np.zeros(0)
        qvec = self.vectorizer.transform([f"{query} {expansion}".strip()])
        return np.asarray((self.matrix @ qvec.T).todense()).ravel().astype(np.float64)

    def normalise(self, sims: np.ndarray) -> np.ndarray:
        return np.clip((sims - self.lo) / (self.hi - self.lo), 0.0, 1.0)


# --------------------------------------------------------------------------------------
# BM25 (sparse)
# --------------------------------------------------------------------------------------
class _BM25:
    """Okapi BM25 over chunk tokens with an inverted index."""

    def __init__(self, token_lists: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.n = len(token_lists)
        self.doc_len = np.array([len(t) for t in token_lists], dtype=np.float64)
        self.avgdl = float(self.doc_len.mean()) if self.n else 1.0
        self.postings: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        for i, toks in enumerate(token_lists):
            counts: Dict[str, int] = defaultdict(int)
            for t in toks:
                counts[t] += 1
            for t, c in counts.items():
                self.postings[t].append((i, c))
        self.idf = {t: math.log(1.0 + (self.n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.postings.items()}

    def score(self, weighted_terms: Dict[str, float]) -> Tuple[np.ndarray, float]:
        """Return (raw scores per chunk, theoretical max for the terms present in the corpus)."""
        scores = np.zeros(self.n, dtype=np.float64)
        max_possible = 0.0
        for term, qw in weighted_terms.items():
            plist = self.postings.get(term)
            if not plist:
                continue
            idf = self.idf[term]
            max_possible += qw * idf * (self.k1 + 1.0)
            for i, tf in plist:
                norm = self.k1 * (1.0 - self.b + self.b * self.doc_len[i] / self.avgdl)
                scores[i] += qw * idf * tf * (self.k1 + 1.0) / (tf + norm)
        return scores, max_possible


# --------------------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------------------
@dataclass
class TalentIndex:
    """Searchable index over a resume pool (build once, query many times)."""

    chunks: List[_Chunk]
    by_resume: Dict[int, List[int]]
    resumes: List[Dict[str, Any]]
    bm25: _BM25
    dense: Any
    fingerprint: str

    @property
    def dense_backend(self) -> str:
        return self.dense.label


class TalentRAG:
    """Hybrid (dense + BM25) talent-pool search engine.

    Args:
        embedding_backend: ``"auto"`` (sentence-transformers if loadable, else TF-IDF), ``"sentence-transformers"``
            (still falls back if the model cannot load) or ``"tfidf"``.
        model_name: SentenceTransformer model id (env ``TALENT_RAG_MODEL``; default ``all-MiniLM-L6-v2``).
        alpha: Weight of the dense score in the fusion; ``1 - alpha`` goes to BM25.
        embedder: Optional custom ``list[str] -> np.ndarray`` embedding function (overrides the model; useful for
            reusing an already-loaded model or for tests).
        cache_size: Number of resume-pool indexes kept in memory.
    """

    def __init__(self, embedding_backend: str = "auto", model_name: Optional[str] = None, alpha: float = 0.55,
                 embedder: Optional[Callable[[List[str]], np.ndarray]] = None, cache_size: int = 4):
        if embedding_backend not in {"auto", "sentence-transformers", "tfidf"}:
            raise ValueError("embedding_backend must be 'auto', 'sentence-transformers' or 'tfidf'")
        self.embedding_backend = embedding_backend
        self.model_name = model_name or os.environ.get("TALENT_RAG_MODEL") or DEFAULT_MODEL
        self.alpha = min(1.0, max(0.0, alpha))
        self._embedder = embedder
        self._cache: "OrderedDict[str, TalentIndex]" = OrderedDict()
        self._cache_size = max(1, cache_size)
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ query understanding
    def parse_query(self, query: str) -> QueryPlan:
        """Extract the experience requirement, competencies (concepts, skills, keywords) and expansion terms."""
        text = (query or "").strip()
        lower = text.lower()
        consumed: List[Tuple[int, int]] = []

        min_years: Optional[float] = None
        for pat in _EXP_PATTERNS:
            m = pat.search(lower)
            if m:
                min_years = float(m.group(1))
                consumed.append(m.span())
                break

        def free(span: Tuple[int, int]) -> bool:
            return all(span[1] <= s or span[0] >= e for s, e in consumed)

        competencies: List[Competency] = []
        seen: Set[str] = set()
        # Concept lexicon: longest trigger first so "distributed systems" beats "systems".
        triggers = sorted(((trig, name) for name, spec in _LEXICON.items() for trig in spec["triggers"]),
                          key=lambda x: -len(x[0]))
        for trig, name in triggers:
            if name in seen:
                continue
            m = re.search(r"(?<![a-z0-9])" + re.escape(trig) + r"(?![a-z0-9])", lower)
            if m and free(m.span()):
                spec = _LEXICON[name]
                competencies.append(Competency(name=name, core=list(spec["core"]), related=list(spec["related"]), kind="concept"))
                seen.add(name)
                consumed.append(m.span())

        # Ontology skills not already covered by a concept.
        if _extract_skills is not None:
            for skill in _extract_skills(text):
                key = skill.lower()
                if key in seen or any(key == c.name for c in competencies):
                    continue
                aliases = [a.lower() for a in _ONTOLOGY.get(skill, {}).get("aliases", [])] + [key]
                alias_hit = [a for a in aliases if re.search(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])", lower)]
                spans = [m.span() for a in alias_hit for m in re.finditer(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])", lower)]
                if spans and not all(not free(s) for s in spans):
                    seen.add(key)
                    competencies.append(Competency(name=skill, core=sorted(set(aliases), key=len, reverse=True), kind="skill"))
                    consumed.extend(spans)

        # Leftover content words become low-weight keyword competencies.
        keywords: List[str] = []
        for m in _TOKEN_RE.finditer(lower):
            if not free(m.span()):
                continue
            tok = _TOKEN_ALIASES.get(m.group(0), m.group(0))
            if tok in _STOPWORDS or len(tok) < 2 or tok.isdigit():
                continue
            stem = _stem(tok)
            if stem not in keywords:
                keywords.append(stem)
        known_terms = {t for c in competencies for term in c.core for t in _tokenize(term, with_bigrams=False)}
        for kw in keywords:
            if kw not in known_terms:
                competencies.append(Competency(name=kw, core=[kw], weight=0.5, kind="keyword"))

        expansion: List[str] = []
        for c in competencies:
            if c.kind == "concept":
                expansion.extend(c.core + c.related)
        return QueryPlan(raw=text, min_years=min_years, competencies=competencies, keywords=keywords,
                         expansion_terms=list(dict.fromkeys(expansion)))

    # ------------------------------------------------------------------ indexing
    def build_index(self, resumes: Sequence[Dict[str, Any]]) -> TalentIndex:
        """Chunk and index a resume pool. Results are cached by content fingerprint."""
        chunks: List[_Chunk] = []
        for r_idx, resume in enumerate(resumes):
            if isinstance(resume, dict):
                chunks.extend(chunk_resume(resume, r_idx))
        for i, ch in enumerate(chunks):
            ch.idx = i
            ch.lower = ch.text.lower()
            ch.tokens = _tokenize(ch.text)
        digest = hashlib.sha1(
            (self.embedding_backend + self.model_name + "\x00".join(f"{c.resume_idx}|{c.section}|{c.text}" for c in chunks)).encode("utf-8")
        ).hexdigest()
        with self._lock:
            hit = self._cache.get(digest)
            if hit is not None:
                self._cache.move_to_end(digest)
                hit.resumes = list(resumes)
                return hit

        dense = self._make_dense_backend()
        texts = [c.text for c in chunks]
        if chunks:
            try:
                dense.fit(texts)
            except Exception as exc:  # model failure mid-flight -> degrade gracefully
                logger.warning("Dense backend failed (%s); falling back to TF-IDF", exc)
                dense = _TfidfBackend()
                dense.fit(texts)
        by_resume: Dict[int, List[int]] = defaultdict(list)
        for c in chunks:
            by_resume[c.resume_idx].append(c.idx)
        index = TalentIndex(chunks=chunks, by_resume=dict(by_resume), resumes=list(resumes),
                            bm25=_BM25([c.tokens for c in chunks]), dense=dense, fingerprint=digest)
        with self._lock:
            self._cache[digest] = index
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return index

    def _make_dense_backend(self) -> Any:
        if self.embedding_backend == "tfidf":
            return _TfidfBackend()
        if self._embedder is not None:
            return _EmbeddingBackend(self._embedder, "custom-embedder")
        model = _load_sentence_model(self.model_name)
        if model is None:
            return _TfidfBackend()

        def embed(texts: List[str]) -> np.ndarray:
            return model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)

        return _EmbeddingBackend(embed, f"sentence-transformers:{self.model_name}")

    # ------------------------------------------------------------------ search
    def search_talent_pool(self, query: str, resumes: List[Dict[str, Any]], top_k: int = 5, *,
                           strict_experience: bool = False, min_score: float = 1.0,
                           index: Optional[TalentIndex] = None) -> List[Dict[str, Any]]:
        """Rank resumes for a natural-language recruiter query.

        Args:
            query: e.g. "Find engineers with 3+ years in distributed systems who know Docker and deployed
                microservices on AWS".
            resumes: Parsed resume dicts (``ResumeParser.parse`` output).
            top_k: Number of candidates to return.
            strict_experience: Drop candidates whose total years are below the query's requirement
                (default: they stay but are penalised and flagged ``meets_experience_requirement=False``).
            min_score: Hide candidates scoring below this relevance (0-100).
            index: A prebuilt ``TalentIndex`` (from ``build_index``) to skip fingerprinting.

        Returns:
            Ranked list of dicts with ``rank``, ``candidate_name``, ``relevance_score`` (0-100),
            ``semantic_score`` / ``keyword_score`` (0-100, best matching chunk), ``competency_coverage`` (0-1),
            ``matched_competencies`` (name, evidence section, matched terms, strength), ``partial_competencies``
            (only supporting/related evidence), ``missing_competencies`` (no evidence at all),
            ``years_of_experience``, ``meets_experience_requirement``, ``snippets`` (each with ``text``,
            ``markdown`` and ``html`` highlighted forms), ``score_breakdown`` and ``retrieval`` info.
        """
        if top_k <= 0 or not resumes or not (query or "").strip():
            return []
        idx = index or self.build_index(resumes)
        if not idx.chunks:
            return []
        plan = self.parse_query(query)
        n = len(idx.chunks)

        # Dense scores (cosine -> 0..1).
        sims = idx.dense.similarities(plan.raw, " ".join(plan.expansion_terms))
        dense_norm = idx.dense.normalise(sims) if len(sims) == n else np.zeros(n)

        # Sparse scores: query tokens at weight 1, synonym expansion at 0.4.
        weighted: Dict[str, float] = {}
        for tok in _tokenize(plan.raw):
            weighted[tok] = 1.0
        for term in plan.expansion_terms:
            for tok in _tokenize(term, with_bigrams=True):
                weighted.setdefault(tok, 0.4)
        raw_bm25, max_possible = idx.bm25.score(weighted)
        bm25_norm = np.clip(raw_bm25 / (0.45 * max_possible), 0.0, 1.0) if max_possible > 0 else np.zeros(n)

        factors = np.array([_SECTION_FACTOR.get(c.section, 0.85) for c in idx.chunks])
        hybrid = (self.alpha * dense_norm + (1.0 - self.alpha) * bm25_norm) * factors

        matchers = {c.name: _compile_terms(c.core) for c in plan.competencies}
        related_matchers = {c.name: _compile_terms(c.related) for c in plan.competencies}
        highlight_rx = _compile_terms(sorted({t for c in plan.competencies for t in c.all_terms} | set(plan.keywords), key=len, reverse=True))

        total_w = sum(c.weight for c in plan.competencies)
        results: List[Dict[str, Any]] = []
        for r_idx, chunk_ids in idx.by_resume.items():
            resume = idx.resumes[r_idx]
            scores = hybrid[chunk_ids]
            order = np.argsort(-scores)
            top = scores[order[:3]]
            semantic = float(0.6 * top[0] + 0.4 * top.mean())

            # Competency evidence across the candidate's chunks.
            matched: List[Dict[str, Any]] = []
            missing: List[str] = []
            partial: List[Dict[str, Any]] = []
            strength_sum = 0.0
            evidence_chunk: Dict[int, float] = defaultdict(float)
            for comp in plan.competencies:
                best = {"strength": 0.0}
                for cid in chunk_ids:
                    ch = idx.chunks[cid]
                    sec_mult = 1.0 if ch.section in {"experience", "projects"} else (0.7 if ch.section == "skills" else 0.6)
                    core_hits = sorted({m.group(0).lower() for m in matchers[comp.name].finditer(ch.lower)}) if matchers[comp.name] else []
                    rel_hits = sorted({m.group(0).lower() for m in related_matchers[comp.name].finditer(ch.lower)}) if related_matchers[comp.name] else []
                    if core_hits:
                        strength = sec_mult
                    elif rel_hits:  # supporting evidence only: counts as *partial*, never as a full match
                        strength = (0.45 if len(rel_hits) >= 2 else 0.25) * (1.0 if sec_mult == 1.0 else 0.8)
                    else:
                        continue
                    if strength > best["strength"]:
                        best = {"strength": strength, "section": ch.section, "terms": core_hits or rel_hits, "chunk": cid,
                                "via": "direct" if core_hits else "related"}
                if best["strength"] >= 0.5:
                    matched.append({"competency": comp.name, "evidence_section": best["section"],
                                    "matched_terms": best["terms"][:6], "strength": round(best["strength"], 2),
                                    "evidence_type": best["via"]})
                    evidence_chunk[best["chunk"]] += comp.weight
                    strength_sum += comp.weight * best["strength"]
                elif best["strength"] > 0:
                    partial.append({"competency": comp.name, "evidence_section": best["section"],
                                    "related_terms": best["terms"][:6], "strength": round(best["strength"], 2)})
                    evidence_chunk[best["chunk"]] += 0.5 * comp.weight
                    strength_sum += comp.weight * best["strength"] * 0.8
                else:
                    missing.append(comp.name)
            coverage = (strength_sum / total_w) if total_w else 0.0

            years = _years_of(resume)
            meets: Optional[bool] = None
            exp_fit = 1.0
            if plan.min_years:
                if years is None:
                    exp_fit = 0.5
                else:
                    meets = years >= plan.min_years
                    exp_fit = min(1.0, years / plan.min_years)
            if strict_experience and meets is False:
                continue

            if plan.competencies:
                base = 0.40 * semantic + 0.60 * coverage
            else:
                base = semantic
            relevance = base * ((0.65 + 0.35 * exp_fit) if plan.min_years else 1.0)
            relevance = float(min(1.0, relevance))
            score100 = round(100.0 * relevance, 1)
            if score100 < min_score:
                continue

            best_cid = chunk_ids[int(order[0])]
            snippets = self._snippets(idx, chunk_ids, hybrid, evidence_chunk, highlight_rx)
            results.append({
                "candidate_id": idx.chunks[best_cid].candidate_id,
                "candidate_name": idx.chunks[best_cid].candidate_name,
                "resume_index": r_idx,
                "file_name": resume.get("file_name"),
                "relevance_score": score100,
                "semantic_score": round(100.0 * float(dense_norm[chunk_ids].max()), 1),
                "keyword_score": round(100.0 * float(bm25_norm[chunk_ids].max()), 1),
                "competency_coverage": round(coverage, 3),
                "matched_competencies": matched,
                "partial_competencies": partial,
                "missing_competencies": missing,
                "years_of_experience": years,
                "meets_experience_requirement": meets,
                "snippets": snippets,
                "score_breakdown": {
                    "hybrid_chunk_score": round(semantic, 3), "competency_coverage": round(coverage, 3),
                    "experience_fit": round(exp_fit, 3), "fusion_alpha": self.alpha,
                },
                "retrieval": {"dense_backend": idx.dense_backend, "min_years_in_query": plan.min_years},
            })

        results.sort(key=lambda r: (-r["relevance_score"], -r["competency_coverage"], str(r["candidate_name"])))
        for rank, r in enumerate(results[:top_k], start=1):
            r["rank"] = rank
        return results[:top_k]

    # ------------------------------------------------------------------ snippets
    @staticmethod
    def _snippets(idx: TalentIndex, chunk_ids: List[int], hybrid: np.ndarray, evidence: Dict[int, float],
                  highlight_rx: Optional[re.Pattern], limit: int = 3, width: int = 260) -> List[Dict[str, Any]]:
        ranked = sorted(chunk_ids, key=lambda cid: (-(hybrid[cid] + 0.15 * evidence.get(cid, 0.0)), cid))
        chosen: List[int] = []
        seen_sections: Set[str] = set()
        for cid in ranked:  # first pass: one chunk per section for variety
            if idx.chunks[cid].section not in seen_sections and (hybrid[cid] > 0 or evidence.get(cid)):
                chosen.append(cid)
                seen_sections.add(idx.chunks[cid].section)
            if len(chosen) == limit:
                break
        for cid in ranked:
            if len(chosen) >= limit:
                break
            if cid not in chosen and (hybrid[cid] > 0 or evidence.get(cid)):
                chosen.append(cid)

        out: List[Dict[str, Any]] = []
        for cid in chosen:
            ch = idx.chunks[cid]
            text = re.sub(r"\s+", " ", ch.text).strip()
            spans = [m.span() for m in highlight_rx.finditer(text)] if highlight_rx else []
            start, end = 0, len(text)
            prefix = suffix = ""
            if len(text) > width:
                focus = spans[0][0] if spans else 0
                start = max(0, min(focus - 60, len(text) - width))
                end = min(len(text), start + width)
                if start > 0:
                    sp = text.find(" ", start)
                    start = sp + 1 if 0 <= sp < start + 25 else start
                    prefix = "…"
                if end < len(text):
                    sp = text.rfind(" ", start, end)
                    end = sp if sp > start + width // 2 else end
                    suffix = "…"
            window = text[start:end]
            win_spans = _merge_spans([(max(s, start) - start, min(e, end) - start) for s, e in spans if e > start and s < end])
            out.append({
                "section": ch.section,
                "score": round(float(hybrid[cid]), 3),
                "text": f"{prefix}{window}{suffix}",
                "markdown": prefix + _wrap(window, win_spans, "**", "**", lambda s: s) + suffix,
                "html": html.escape(prefix) + _wrap(window, win_spans, "<mark>", "</mark>", html.escape) + html.escape(suffix),
                "highlights": [window[s:e] for s, e in win_spans],
            })
        return out


# --------------------------------------------------------------------------------------
# Highlight helpers
# --------------------------------------------------------------------------------------
def _compile_terms(terms: Sequence[str]) -> Optional[re.Pattern]:
    cleaned = sorted({t.strip().lower() for t in terms if t and t.strip()}, key=len, reverse=True)
    if not cleaned:
        return None
    body = "|".join(re.escape(t) for t in cleaned)
    return re.compile(rf"(?<![A-Za-z0-9])(?:{body})(?:s|es)?(?![A-Za-z0-9])", re.IGNORECASE)


def _merge_spans(spans: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    merged: List[Tuple[int, int]] = []
    for s, e in sorted(x for x in spans if x[1] > x[0]):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _wrap(text: str, spans: List[Tuple[int, int]], open_tag: str, close_tag: str, escape: Callable[[str], str]) -> str:
    out, pos = [], 0
    for s, e in spans:
        out.append(escape(text[pos:s]))
        out.append(open_tag + escape(text[s:e]) + close_tag)
        pos = e
    out.append(escape(text[pos:]))
    return "".join(out)


# --------------------------------------------------------------------------------------
# Module-level convenience
# --------------------------------------------------------------------------------------
_DEFAULT_ENGINE: Optional[TalentRAG] = None
_DEFAULT_LOCK = threading.Lock()


def get_default_engine() -> TalentRAG:
    """Process-wide shared engine (keeps the model and index caches warm between Streamlit reruns)."""
    global _DEFAULT_ENGINE
    with _DEFAULT_LOCK:
        if _DEFAULT_ENGINE is None:
            _DEFAULT_ENGINE = TalentRAG()
        return _DEFAULT_ENGINE


def search_talent_pool(query: str, resumes: List[Dict[str, Any]], top_k: int = 5, **kwargs: Any) -> List[Dict[str, Any]]:
    """Search a resume pool with the shared ``TalentRAG`` engine. See ``TalentRAG.search_talent_pool``."""
    return get_default_engine().search_talent_pool(query, resumes, top_k=top_k, **kwargs)

"""Chapter 2: Literature Survey"""
from refs_stub import AUTH, TITLE, YEAR


def lit(r, key, text):
    r.h3(f"{TITLE[key]} ({YEAR[key]})")
    p = r.p(f"Authors: {AUTH[key]}", indent=False, space_after=3, line=1.2, size=11, italic=True, keep=True)
    r.p(text, indent=True)


def build(r):
    r.chapter("Literature Survey")
    r.p("This chapter reviews the research that is closest to the problem addressed by the project. The survey is organised by theme: person-job fit and resume understanding, extraction of skills from text, semantic and hybrid retrieval, bias and fairness in algorithmic hiring, explainability, and multi-agent evaluation. Each reviewed paper is summarised with its authors, its contribution and the limitation that is relevant to this project. A summary table and the research gaps that the project addresses close the chapter. Surveys of the wider area of talent analytics and job recommendation are given by [@qin_survey] and [@ruijt].")

    r.theme("Person-job fit and resume understanding")
    lit(r, "qin_pjf", "The authors proposed an ability-aware neural network for person-job fit. Job requirements and the experiences of a job seeker are encoded at word level with recurrent networks, and a hierarchical attention mechanism measures how important each requirement is and how much each past experience contributes to each requirement. The attention weights make the matching partly interpretable. The model, however, is trained on historical hiring outcomes, and it does not check whether an ability claimed in a resume is backed by evidence in the rest of the document [@qin_pjf].")
    lit(r, "zhu_pjf", "This work learns a joint representation of job postings and resumes with a convolutional neural network, so that a matching score can be computed directly from the text of both documents. The approach shows that semantic representations improve on keyword matching, but the output is a score without a human-readable explanation, and it requires a large collection of labelled matches [@zhu_pjf].")
    lit(r, "le_pjf", "The authors addressed the lack of interpretability of neural person-job fitting models. Their model aligns the individual requirements of a job with the experiences of a candidate and allows the contribution of each pair to the prediction to be inspected. The study confirms that interpretability is a recognised requirement of recruitment models, although the explanation is limited to attention over text and does not cover skill gaps or bias [@le_pjf].")
    lit(r, "bhatia", "This paper combined a resume parser with BERT-based sentence-pair classification to rank candidates for a job description, and reported 73 percent accuracy for candidate suitability. It demonstrates an end-to-end pipeline from parsing to matching. The result is a single similarity score; there is no skill-gap breakdown, no handling of uncertainty and no check for bias [@bhatia,@bert].")
    lit(r, "jiechieu", "The authors framed the prediction of skills from a resume as a multi-label classification problem solved with a convolutional neural network, and added an explanation of the model predictions. This is useful for inferring skills that are not stated explicitly, but the inferred skills are probabilistic, whereas a screening decision must be traceable to explicit evidence [@jiechieu].")
    lit(r, "qin_survey", "This survey reviews artificial-intelligence techniques across the life cycle of talent management, including recruitment, matching and ranking. It records the shift from handcrafted features to deep models and discusses open challenges such as fairness and interpretability, which motivate the design of the present system [@qin_survey].")
    lit(r, "ruijt", "This review classifies job recommender systems into content-based, collaborative and hybrid approaches and discusses their data, evaluation and ethical problems. It shows that most recommenders optimise matching accuracy and give little attention to explanation or to the verification of claims [@ruijt].")

    r.theme("Extraction of skills from text")
    lit(r, "bhola", "The authors cast the retrieval of skills from job descriptions as an extreme multi-label classification problem solved with a language-model based framework. The method handles a large skill vocabulary, but it is probabilistic and requires training data, whereas the present system uses an explicit, auditable ontology so that every credited skill can be traced to a rule [@bhola].")
    lit(r, "jobbert", "JobBERT learns representations of job titles by using the skills mentioned in job postings as supervision, which helps to normalise the many ways in which the same role is named. It shows the value of skills as a bridge between titles and requirements [@jobbert].")
    lit(r, "skillspan", "SkillSpan provides an annotated collection of English job postings in which hard and soft skills are marked as spans, and evaluates transformer models on the extraction task. It shows that skill extraction is a hard task even for strong models and that annotated data is scarce [@skillspan].")
    lit(r, "clavie", "The authors showed that a large language model can map job-posting text to the skills of the ESCO taxonomy without task-specific training, by generating synthetic data and re-ranking candidates, and reported R-precision at ten of 61.0 and 68.9 on two evaluation sets. The approach is powerful but probabilistic and dependent on an external model, so a generative model could assert a skill that is not in the text [@clavie].")

    r.theme("Semantic and hybrid retrieval")
    lit(r, "sbert", "Sentence-BERT adds siamese and triplet network structures to BERT so that sentences are mapped to fixed-size vectors that can be compared with cosine similarity. The authors report that finding the most similar pair in a collection of ten thousand sentences, which takes about 65 hours with a standard BERT cross-encoder, takes about five seconds with Sentence-BERT. This efficiency makes sentence embeddings practical for matching resumes with job descriptions [@sbert,@minilm].")
    lit(r, "dpr", "Dense passage retrieval encodes questions and passages into dense vectors and retrieves by inner product. On open-domain question answering it outperformed a strong BM25 system by 9 to 19 percentage points in top-20 passage retrieval accuracy. Dense retrieval therefore handles paraphrase well, while sparse methods remain strong for rare exact terms, which motivates the hybrid search of the present system [@dpr,@bm25].")
    lit(r, "rag", "Retrieval-augmented generation combines a pre-trained sequence-to-sequence model with a non-parametric memory, a dense index of documents, so that generated text is grounded in retrieved passages. The idea underlies the retrieval-grounded recruiter chatbot of this project, which answers from retrieved and scored resume evidence instead of free generation [@rag].")
    lit(r, "hauff", "The authors matched the public GitHub profiles of developers with job advertisements by extracting concepts from both and measuring their similarity. In that work, repository evidence is used to recommend developers; the present system uses it differently, to audit the languages that a candidate claims on a resume [@hauff].")

    r.theme("Bias and fairness in algorithmic hiring")
    lit(r, "bertrand", "In a field experiment, the authors sent fictitious resumes of equal quality to real job advertisements and randomly assigned white-sounding or African-American-sounding names. Resumes with white-sounding names received about 50 percent more call-backs for interviews. This study is the model for the name-swap test used in this project to measure name invariance [@bertrand].")
    lit(r, "wilson", "The authors audited three text-embedding models used for resume retrieval with a large set of resumes in which only the name was changed. Resumes with white-associated names were preferred in up to 85.1 percent of the tests, and male-associated names were favoured over female-associated names in most comparisons. The study measures bias in embedding-based screening but does not propose a screening design that removes it [@wilson].")
    lit(r, "armstrong", "This audit examined how a GPT model ranks resumes when only the name signals race and gender. It found stereotype-driven differences in the ranking of candidates for several occupations. As in the previous study, the result is an audit and not a mitigation built into a working pipeline [@armstrong].")
    lit(r, "chen_rank", "The authors audited resume search engines and examined whether the inferred gender of a candidate influences the rank of the resume when other features are controlled. The study shows that bias can arise in the ranking function of a search tool even when gender is never an explicit input [@chen_rank].")
    lit(r, "raghavan", "The authors analysed the public claims of eighteen vendors of algorithmic pre-employment assessments about bias mitigation. They found limited transparency about methods and a heavy reliance on outcome-based criteria such as the four-fifths rule. The paper is a review of practice and does not provide a reference implementation [@raghavan]. A related report examines hiring algorithms across the whole pipeline, from sourcing to selection, and discusses equity and bias at each stage [@bogen].")
    lit(r, "sanchez", "This study compared how vendors of automated hiring systems define and reduce discrimination with the requirements of the legal framework of the United Kingdom. It shows that technical notions of fairness and legal notions of discrimination do not coincide, which supports the need for transparency and human oversight in screening tools [@sanchez].")
    lit(r, "kochling", "The authors carried out a systematic review of research on discrimination and fairness in algorithmic decision-making for recruitment and personnel development. The review documents the sources of discrimination in algorithmic HR decisions, such as biased training data, and calls for further research on fair design. Overviews of AI-enabled recruiting for managers make the same point from a practice perspective [@kochling,@black].")
    lit(r, "albaroudi", "This review examines the sources of algorithmic bias in job hiring and the artificial-intelligence techniques that have been proposed to detect and reduce it. Acting on the data before a model sees it, which is what blind screening does in this project, is in line with the data-level mitigation discussed in such reviews, and the ethical risks of AI-enabled recruitment are discussed further in [@albaroudi,@chen_ethics].")
    lit(r, "fair", "FA*IR formalises fairness of a top-k ranking as a statistical test of whether a protected group is represented sufficiently in every prefix of the ranking, and gives an algorithm that re-ranks a list to satisfy the test. The method requires protected attributes at ranking time and does not explain why a candidate received a score [@fair].")
    lit(r, "hardt", "The authors defined equality of opportunity, a criterion that requires equal true-positive rates across protected groups, and showed how to adjust a trained predictor to satisfy it. Together with the notion of individual fairness, which requires that similar individuals are treated similarly [@dwork], these criteria form the vocabulary for discussing fairness in screening. They need demographically labelled outcomes, which the synthetic pools of this project do not have [@hardt,@kleinberg,@mehrabi].")

    r.theme("Multi-agent evaluation")
    lit(r, "debate", "In this work several language-model instances propose answers, read one another's answers and revise them over multiple rounds. The procedure improves factuality and reasoning, for instance on arithmetic tasks where accuracy rose from 67.0 to 81.8 percent. The study concerns benchmark question answering, not hiring decisions [@debate].")
    lit(r, "chateval", "ChatEval uses a team of language-model referees that debate the quality of generated text, and obtains judgements that are closer to human annotation than a single referee. A related study of language models used as judges documents biases such as a preference for the answer that appears in a given position [@chateval,@mtbench]. These findings motivate the use of several specialised and independent evaluators, and of an auditor that checks the others, in the council of this project.")

    r.h1("2.1", "Literature Survey Summary")
    r.p(f"{r.ref_next_tab()} summarises the main reviewed papers, their key focus and what they leave open for the present work. The table is followed by the research gaps that were identified.", keep=True)
    rows = [
        ["1", f"{TITLE['qin_pjf']} ({YEAR['qin_pjf']})", "Ability-aware neural person-job fit with hierarchical attention", "Skill claims are not checked for evidence; no fairness stage"],
        ["2", f"{TITLE['bhatia']} ({YEAR['bhatia']})", "Resume parser with BERT sentence-pair classification", "Single score; no skill gap, no bias or uncertainty handling"],
        ["3", f"{TITLE['sbert']} ({YEAR['sbert']})", "Fast sentence embeddings compared by cosine similarity", "General similarity tool; needs skill, experience and fairness logic"],
        ["4", f"{TITLE['dpr']} ({YEAR['dpr']})", "Dense retrieval beats BM25 on paraphrased queries", "Sparse methods still needed for rare exact terms"],
        ["5", f"{TITLE['clavie']} ({YEAR['clavie']})", "LLM mapping of postings to ESCO skills", "Probabilistic and API-dependent; no screening decision"],
        ["6", f"{TITLE['hauff']} ({YEAR['hauff']})", "GitHub profiles matched to job advertisements", "Used for recommendation, not for auditing resume claims"],
        ["7", f"{TITLE['bertrand']} ({YEAR['bertrand']})", "Field experiment on name-based discrimination in call-backs", "Measures bias; proposes no screening system"],
        ["8", f"{TITLE['wilson']} ({YEAR['wilson']})", "Name bias in embedding-based resume retrieval", "Audit only; no mitigation design"],
        ["9", f"{TITLE['armstrong']} ({YEAR['armstrong']})", "Race and gender bias in GPT resume ranking", "Audit only; no mitigation in a pipeline"],
        ["10", f"{TITLE['raghavan']} ({YEAR['raghavan']})", "Review of vendor claims about bias mitigation", "No reference implementation"],
        ["11", f"{TITLE['fair']} ({YEAR['fair']})", "Statistical test and algorithm for fair top-k rankings", "Needs protected attributes; gives no explanation"],
        ["12", f"{TITLE['debate']} ({YEAR['debate']})", "Multi-agent debate improves reasoning", "Benchmarks, not gated hiring decisions"],
        ["13", f"{TITLE['chateval']} ({YEAR['chateval']})", "Multi-agent referees closer to human judgement", "Text evaluation, not candidate screening"],
    ]
    r.table(["Sl. No.", "Paper (year)", "Key focus", "Left open for this work"], rows, "Summary of Reviewed Literature", [0.7, 3.4, 2.8, 2.8], size=9.5, align=["center", "left", "left", "left"])

    r.h1("2.2", "Research Gaps")
    r.p("Reading the literature against the practical requirements of a defensible screening tool, the following gaps were identified. They are a synthesis of the reviewed works and not a claim that no other work exists.", keep=True)
    r.numbered([
        "**G1, evidence:** matching models optimise similarity and treat a listed skill as if it were evidence [@qin_pjf,@bhatia,@zhu_pjf].",
        "**G2, bias:** neural and language-model screeners show name and gender bias, while vendor mitigation is mostly outcome-based and opaque [@wilson,@armstrong,@raghavan].",
        "**G3, oversight:** regulation requires transparency and human oversight [@euaiact], but few tools expose disagreement or uncertainty to the recruiter.",
        "**G4, deliberation:** multi-agent debate is studied for benchmarks and text evaluation, not for gated hiring decisions [@debate,@chateval].",
        "**G5, skills:** language-model skill mapping is probabilistic and depends on an external service [@clavie,@bhola].",
        "**G6, external evidence:** public repository evidence is used for matching, not for auditing the claims made on a specific resume [@hauff].",
        "**G7, structure:** edited or generated resumes can contain temporal and structural tricks, such as inverted dates, overlapping full-time jobs or missing education, that similarity scoring cannot see.",
    ])
    r.p(f"{r.ref_next_tab()} maps each gap to the response of the present system.", keep=True)
    r.table(["Gap", "Response in this project"], [
        ["G1", "Evidence-weighted skill coverage gives half credit to a skill that is listed but not demonstrated"],
        ["G2", "Data-layer blind screening, auditor agent and counterfactual name-swap test"],
        ["G3", "Verdict with red flags, dissent, confidence and human-review triggers"],
        ["G4", "Deterministic four-agent council with knock-out gates; the language model is optional and writes narrative only"],
        ["G5", "Auditable 79-skill ontology with explicit 0.5 credit for related skills and offline fallbacks"],
        ["G6", "GitHub inspector verifies claimed languages and reports insufficient data instead of guessing"],
        ["G7", "Month-aware timeline parsing, inverted-date, concurrent-employment and missing-education gates"],
    ], "Research Gaps and the Response of the Proposed System", [0.6, 5.5], size=10.5, align=["center", "left"])

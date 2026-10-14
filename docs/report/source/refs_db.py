"""Build formatted IEEE-style references (full author lists) from verified metadata in refs_raw.json."""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(HERE, "refs_raw.json"), encoding="utf8"))

PARTICLES = {"van", "von", "de", "der", "den", "da", "di", "del", "la", "le"}


def initials(given: str) -> str:
    given = given.strip()
    if not given:
        return ""
    parts = []
    for tok in re.split(r"\s+", given):
        if "-" in tok:
            parts.append("-".join(p[0].upper() + "." for p in tok.split("-") if p))
        elif re.fullmatch(r"[A-Z]\.?", tok):
            parts.append(tok.rstrip(".") + ".")
        elif re.fullmatch(r"([A-Z]\.)+", tok):
            parts.append(tok)
        elif tok.lower() in PARTICLES and False:
            continue
        else:
            parts.append(tok[0].upper() + ".")
    return " ".join(parts)


def fmt_author(given: str, family: str) -> str:
    ini = initials(given)
    return f"{ini} {family}".strip()


def join_authors(names):
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def authors_from(source, ident):
    rec = RAW["crossref" if source == "doi" else source][ident]
    return [fmt_author(g, f) for g, f in rec["authors"]], rec


def clean(t):
    t = html.unescape(t).replace("\n", " ")
    return " ".join(t.split())


# Each spec: key, source ('arxiv'|'doi'|'manual'), id, and format fields.
#   kind: journal | conf | arxiv | book | misc
SPECS = []


def S(key, source, ident, kind, **kw):
    SPECS.append(dict(key=key, source=source, id=ident, kind=kind, **kw))


# ---------- arXiv-sourced entries (venue added where certain)
S("sbert", "arxiv", "1908.10084", "conf", venue="Proc. Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP)", year=2019, pp="3982-3992")
S("bert", "arxiv", "1810.04805", "conf", venue="Proc. Conf. North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", year=2019, pp="4171-4186")
S("transformer", "arxiv", "1706.03762", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), vol. 30", year=2017, pp="5998-6008")
S("dpr", "arxiv", "2004.04906", "conf", venue="Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP)", year=2020, pp="6769-6781")
S("rag", "arxiv", "2005.11401", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), vol. 33", year=2020, pp="9459-9474")
S("debate", "arxiv", "2305.14325", "conf", venue="Proc. 41st Int. Conf. Machine Learning (ICML)", year=2024, extra="arXiv:2305.14325")
S("chateval", "arxiv", "2308.07201", "conf", venue="Proc. Int. Conf. Learning Representations (ICLR)", year=2024, extra="arXiv:2308.07201")
S("mtbench", "arxiv", "2306.05685", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks Track, vol. 36", year=2023, extra="arXiv:2306.05685")
S("bhatia", "arxiv", "1910.03089", "arxiv", year=2019)
S("qin_survey", "arxiv", "2307.03195", "arxiv", year=2023)
S("ruijt", "arxiv", "2111.13576", "arxiv", year=2021)
S("clavie", "arxiv", "2307.03539", "arxiv", year=2023)
S("armstrong", "arxiv", "2405.04412", "arxiv", year=2024)
S("shap", "arxiv", "1705.07874", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), vol. 30", year=2017, pp="4765-4774")
S("doshivelez", "arxiv", "1702.08608", "arxiv", year=2017)
S("rudin", "arxiv", "1811.10154", "journal", venue="Nature Machine Intelligence", vol="1", no="5", pp="206-215", year=2019, extra="arXiv:1811.10154")
S("hardt", "arxiv", "1610.02413", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), vol. 29", year=2016, pp="3315-3323")
S("dwork", "arxiv", "1104.3913", "conf", venue="Proc. 3rd Innovations in Theoretical Computer Science Conf. (ITCS)", year=2012, pp="214-226")
S("modelcards", "arxiv", "1810.03993", "conf", venue="Proc. Conf. Fairness, Accountability, and Transparency (FAT*)", year=2019, pp="220-229")
S("kleinberg", "arxiv", "1609.05807", "conf", venue="Proc. 8th Innovations in Theoretical Computer Science Conf. (ITCS)", year=2017, extra="arXiv:1609.05807")
S("bolukbasi", "arxiv", "1607.06520", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), vol. 29", year=2016, pp="4349-4357")
S("datasheets", "arxiv", "1803.09010", "arxiv", year=2018)
S("raji", "arxiv", "2001.00973", "conf", venue="Proc. Conf. Fairness, Accountability, and Transparency (FAT*)", year=2020, pp="33-44", extra="arXiv:2001.00973")
S("word2vec", "arxiv", "1301.3781", "arxiv", year=2013)
S("roberta", "arxiv", "1907.11692", "arxiv", year=2019)
S("minilm", "arxiv", "2002.10957", "conf", venue="Advances in Neural Information Processing Systems (NeurIPS), vol. 33", year=2020, pp="5776-5788")
S("hftransformers", "arxiv", "1910.03771", "conf", venue="Proc. Conf. Empirical Methods in Natural Language Processing: System Demonstrations", year=2020, pp="38-45")
S("autogen", "arxiv", "2308.08155", "arxiv", year=2023)
S("metagpt", "arxiv", "2308.00352", "conf", venue="Proc. Int. Conf. Learning Representations (ICLR)", year=2024, extra="arXiv:2308.00352")
S("selfconsistency", "arxiv", "2203.11171", "conf", venue="Proc. Int. Conf. Learning Representations (ICLR)", year=2023, extra="arXiv:2203.11171")
S("react", "arxiv", "2210.03629", "conf", venue="Proc. Int. Conf. Learning Representations (ICLR)", year=2023, extra="arXiv:2210.03629")
S("nogueira", "arxiv", "1901.04085", "arxiv", year=2019)
S("linrank", "arxiv", "2010.06467", "arxiv", year=2020)
S("zhu_pjf", "arxiv", "1810.04040", "arxiv", year=2018)
S("sklearn", "arxiv", "1201.0490", "journal", venue="Journal of Machine Learning Research", vol="12", pp="2825-2830", year=2011)
S("liang_mad", "arxiv", "2305.19118", "arxiv", year=2023)
S("jobbert", "arxiv", "2109.09605", "arxiv", year=2021)
S("skillspan", "arxiv", "2204.12811", "arxiv", year=2022)
S("wilson", "arxiv", "2407.20371", "conf", venue="Proc. AAAI/ACM Conf. AI, Ethics, and Society (AIES)", year=2024, extra="arXiv:2407.20371")

# ---------- DOI-sourced entries
S("lime", "doi", "10.1145/2939672.2939778", "conf", title_override="‘Why should I trust you?’: Explaining the predictions of any classifier", venue="Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining", year=2016, pp="1135-1144")
S("mehrabi", "doi", "10.1145/3457607", "journal", venue="ACM Computing Surveys", vol="54", no="6", year=2021, pp="1-35")
S("caliskan", "doi", "10.1126/science.aal4230", "journal", venue="Science", vol="356", no="6334", pp="183-186", year=2017)
S("raghavan", "doi", "10.1145/3351095.3372828", "conf", title_override="Mitigating bias in algorithmic hiring: Evaluating claims and practices", venue="Proc. Conf. Fairness, Accountability, and Transparency (FAT*)", year=2020, pp="469-481")
S("fair", "doi", "10.1145/3132847.3132938", "conf", title_override="FA*IR: A fair top-k ranking algorithm", venue="Proc. ACM Conf. Information and Knowledge Management (CIKM)", year=2017, pp="1569-1578")
S("qin_pjf", "doi", "10.1145/3209978.3210025", "conf", title_override="Enhancing person-job fit for talent recruitment: An ability-aware neural network approach", venue="Proc. 41st Int. ACM SIGIR Conf. Research and Development in Information Retrieval", year=2018, pp="25-34")
S("bertrand", "doi", "10.1257/0002828042002561", "journal", venue="American Economic Review", vol="94", no="4", pp="991-1013", year=2004)
S("hauff", "doi", "10.1109/MSR.2015.41", "conf", venue="Proc. 12th IEEE/ACM Working Conf. Mining Software Repositories (MSR)", year=2015, pp="362-366")
S("bm25", "doi", "10.1561/1500000019", "journal", venue="Foundations and Trends in Information Retrieval", vol="3", no="4", pp="333-389", year=2009)
S("tfidf", "doi", "10.1016/0306-4573(88)90021-0", "journal", venue="Information Processing & Management", vol="24", no="5", pp="513-523", year=1988)
S("kendall", "doi", "10.2307/2332226", "journal", venue="Biometrika", vol="30", no="1/2", pp="81-93", year=1938)
S("jones", "doi", "10.1108/eb026526", "journal", title_override="A statistical interpretation of term specificity and its application in retrieval", venue="Journal of Documentation", vol="28", no="1", pp="11-21", year=1972)
S("rrf", "doi", "10.1145/1571941.1572114", "conf", title_override="Reciprocal rank fusion outperforms Condorcet and individual rank learning methods", venue="Proc. 32nd Int. ACM SIGIR Conf. Research and Development in Information Retrieval", year=2009, pp="758-759")
S("ndcg", "doi", "10.1145/582415.582418", "journal", title_override="Cumulated gain-based evaluation of IR techniques", venue="ACM Transactions on Information Systems", vol="20", no="4", pp="422-446", year=2002)
S("glove", "doi", "10.3115/v1/D14-1162", "conf", title_override="GloVe: Global vectors for word representation", venue="Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP)", year=2014, pp="1532-1543")
S("kochling", "doi", "10.1007/s40685-020-00134-w", "journal", venue="Business Research", vol="13", no="3", pp="795-848", year=2020)
S("black", "doi", "10.1016/j.bushor.2019.12.001", "journal", venue="Business Horizons", vol="63", no="2", pp="215-226", year=2020)
S("albaroudi", "doi", "10.3390/ai5010019", "journal", venue="AI", vol="5", no="1", pp="383-404", year=2024)
S("chen_ethics", "doi", "10.1057/s41599-023-02079-x", "journal", venue="Humanities and Social Sciences Communications", vol="10", year=2023, extra="Art. no. 567")
S("arrieta", "doi", "10.1016/j.inffus.2019.12.012", "journal", title_override="Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI", venue="Information Fusion", vol="58", pp="82-115", year=2020)
S("miller", "doi", "10.1016/j.artint.2018.07.007", "journal", venue="Artificial Intelligence", vol="267", pp="1-38", year=2019)
S("guidotti", "doi", "10.1145/3236009", "journal", venue="ACM Computing Surveys", vol="51", no="5", year=2018, pp="1-42")
S("tesseract", "doi", "10.1109/ICDAR.2007.4376991", "conf", venue="Proc. 9th Int. Conf. Document Analysis and Recognition (ICDAR)", year=2007, pp="629-633")
S("sanchez", "doi", "10.1145/3351095.3372849", "conf", venue="Proc. Conf. Fairness, Accountability, and Transparency (FAT*)", year=2020, pp="458-468")
S("matplotlib", "doi", "10.1109/MCSE.2007.55", "journal", venue="Computing in Science & Engineering", vol="9", no="3", pp="90-95", year=2007)
S("pandas", "doi", "10.25080/Majora-92bf1922-00a", "conf", venue="Proc. 9th Python in Science Conf. (SciPy)", year=2010, pp="56-61")
S("jiechieu", "doi", "10.1007/s00521-020-05302-x", "journal", venue="Neural Computing and Applications", vol="33", no="10", pp="5069-5087", year=2021)
S("le_pjf", "doi", "10.1145/3357384.3357949", "conf", venue="Proc. 28th ACM Int. Conf. Information and Knowledge Management (CIKM)", year=2019, pp="1883-1892")
S("chen_rank", "doi", "10.1145/3173574.3174225", "conf", venue="Proc. CHI Conf. Human Factors in Computing Systems", year=2018, pp="1-14")
S("vanesch", "doi", "10.1016/j.chb.2018.09.009", "journal", venue="Computers in Human Behavior", vol="90", pp="215-222", year=2019)
S("upadhyay", "doi", "10.1108/SHR-07-2018-0051", "journal", venue="Strategic HR Review", vol="17", no="5", pp="255-258", year=2018)
S("langer", "doi", "10.1111/ijsa.12246", "journal", venue="International Journal of Selection and Assessment", vol="27", no="3", pp="217-234", year=2019)
S("tambe", "doi", "10.1177/0008125619867910", "journal", venue="California Management Review", vol="61", no="4", pp="15-42", year=2019)
S("manning", "doi", "10.1017/CBO9780511809071", "book", publisher="Cambridge University Press", place="Cambridge, U.K.", year=2008)
S("fielding", "doi", "10.1145/514183.514185", "journal", venue="ACM Transactions on Internet Technology", vol="2", no="2", pp="115-150", year=2002)
S("bhola", "doi", "10.18653/v1/2020.coling-main.513", "conf", venue="Proc. 28th Int. Conf. Computational Linguistics (COLING)", year=2020, pp="5832-5842")

# ---------- Manual entries (documents without a DOI record)
MANUAL = {
    "euaiact": "European Parliament and Council of the European Union, “Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act),” Official Journal of the European Union, Jun. 2024.",
    "gdpr": "European Parliament and Council of the European Union, “Regulation (EU) 2016/679 on the protection of natural persons with regard to the processing of personal data (General Data Protection Regulation),” Official Journal of the European Union, Apr. 2016.",
    "dastin": "J. Dastin, “Amazon scraps secret AI recruiting tool that showed bias against women,” Reuters, Oct. 10, 2018.",
    "levenshtein": "V. I. Levenshtein, “Binary codes capable of correcting deletions, insertions, and reversals,” Soviet Physics Doklady, vol. 10, no. 8, pp. 707–710, 1966.",
    "bogen": "M. Bogen and A. Rieke, “Help wanted: An examination of hiring algorithms, equity, and bias,” Upturn, Washington, DC, USA, Dec. 2018.",
}


def pages(pp):
    return pp.replace("-", "–") if pp else None


AUTH, TITLE, YEAR = {}, {}, {}


def build():
    out = {}
    for s in SPECS:
        names, rec = authors_from(s["source"], s["id"])
        names = [n.replace("K. SPARCK JONES", "K. Spärck Jones") for n in names]
        title = clean(s.get("title_override") or rec["title"])
        a = join_authors(names)
        k = s["kind"]
        yr = s["year"]
        if k == "arxiv":
            text = f"{a}, “{title},” arXiv:{s['id']}, {yr}."
        elif k == "journal":
            bits = [s["venue"]]
            if s.get("vol"):
                bits.append(f"vol. {s['vol']}")
            if s.get("no"):
                bits.append(f"no. {s['no']}")
            if s.get("pp"):
                bits.append(f"pp. {pages(s['pp'])}")
            if s.get("extra"):
                bits.append(s["extra"])
            bits.append(str(yr))
            text = f"{a}, “{title},” {', '.join(bits)}."
            if s["source"] == "doi":
                text += f" doi: {s['id']}."
        elif k == "conf":
            bits = [f"in {s['venue']}", str(yr)]
            if s.get("pp"):
                bits.append(f"pp. {pages(s['pp'])}")
            if s.get("extra"):
                bits.append(s["extra"])
            text = f"{a}, “{title},” {', '.join(bits)}."
            if s["source"] == "doi":
                text += f" doi: {s['id']}."
        elif k == "book":
            text = f"{a}, {title}. {s['place']}: {s['publisher']}, {yr}. doi: {s['id']}."
        out[s["key"]] = text
        AUTH[s["key"]] = a
        TITLE[s["key"]] = title
        YEAR[s["key"]] = yr
    out.update(MANUAL)
    return out


REFS = build()

if __name__ == "__main__":
    for k, v in REFS.items():
        print(f"[{k}] {v}\n")
    print(len(REFS), "references")

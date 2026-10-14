"""Fetch real metadata for candidate references from arXiv and Crossref, save raw JSON."""
import json, re, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

ARXIV = {
    "1908.10084": "Sentence-BERT",
    "1810.04805": "BERT",
    "1706.03762": "Attention",
    "2004.04906": "Dense Passage",
    "2005.11401": "Retrieval-Augmented",
    "2305.14325": "Multiagent Debate",
    "2308.07201": "ChatEval",
    "2306.05685": "Judging LLM",
    "1910.03089": "resume parsing",
    "2307.03195": "talent analytics",
    "2111.13576": "recommender",
    "2307.03539": "ESCO",
    "2405.04412": "Silicon Ceiling",
    "1906.09208": "algorithmic hiring",
    "1706.06368": "FA*IR",
    "1602.04938": "Trust You",
    "1705.07874": "Unified Approach",
    "1702.08608": "interpretable machine learning",
    "1811.10154": "black box",
    "1908.09635": "Bias and Fairness",
    "1610.02413": "Equality of Opportunity",
    "1104.3913": "Awareness",
    "1810.03993": "Model Cards",
    "1609.05807": "Trade-Offs",
    "1607.06520": "computer programmer",
    "1608.07187": "Semantics derived",
    "1803.09010": "Datasheets",
    "2001.00973": "accountability gap",
    "1301.3781": "Word Representations",
    "1907.11692": "RoBERTa",
    "2002.10957": "MiniLM",
    "1910.03771": "Transformers",
    "2308.08155": "AutoGen",
    "2308.00352": "MetaGPT",
    "2203.11171": "Self-Consistency",
    "2210.03629": "ReAct",
    "1901.04085": "Passage Re-ranking",
    "2010.06467": "Text Ranking",
    "1810.04040": "Person-Job Fit",
    "1201.0490": "Scikit-learn",
    "2305.19118": "Divergent Thinking",
    "2109.09605": "JobBERT",
    "2204.12811": "SkillSpan",
    "2407.20371": "Gender, Race",
}

DOIS = [
    "10.1145/3209978.3210025",
    "10.1257/0002828042002561",
    "10.1109/MSR.2015.41",
    "10.1561/1500000019",
    "10.1016/0306-4573(88)90021-0",
    "10.2307/2332226",
    "10.1108/eb026526",
    "10.1145/1571941.1572114",
    "10.1145/582415.582418",
    "10.3115/v1/D14-1162",
    "10.1007/s40685-020-00134-w",
    "10.1016/j.bushor.2019.12.001",
    "10.3390/ai5010019",
    "10.1057/s41599-023-02079-x",
    "10.1016/j.inffus.2019.12.012",
    "10.1016/j.artint.2018.07.007",
    "10.1145/3236009",
    "10.1109/ICDAR.2007.4376991",
    "10.1145/3351095.3372849",
    "10.1126/science.aal4230",
    "10.1109/MCSE.2007.55",
    "10.25080/Majora-92bf1922-00a",
    "10.1007/s00521-020-05302-x",
    "10.1145/3357384.3357949",
    "10.1145/3173574.3174225",
    "10.1016/j.chb.2018.09.009",
    "10.1108/SHR-07-2018-0051",
    "10.1111/ijsa.12246",
    "10.1177/0008125619867910",
    "10.1609/aaai.v34i08.7021",
    "10.1017/CBO9780511809071",
    "10.1145/514183.514185",
    "10.1145/3351095.3372828",
    "10.1145/3132847.3132938",
    "10.1145/2939672.2939778",
    "10.18653/v1/2020.coling-main.513",
    "10.1145/3457607",
    "10.1145/3292500.3330699",
]

out = {"arxiv": {}, "crossref": {}}

# ---- arXiv via DataCite (arXiv DOIs: 10.48550/arXiv.<id>)
ids = list(ARXIV)
for i in ids:
    u = "https://api.datacite.org/dois/10.48550/arxiv." + i
    ok = False
    for attempt in range(4):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "report-ref-check/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                at = json.load(r)["data"]["attributes"]
            out["arxiv"][i] = {
                "title": " ".join(at["titles"][0]["title"].split()),
                "authors": [(c.get("givenName", ""), c.get("familyName", c.get("name", ""))) for c in at["creators"]],
                "published": str(at.get("publicationYear")),
                "journal_ref": None, "doi": None,
            }
            ok = True
            break
        except Exception as ex:
            time.sleep(3)
    if not ok:
        print("  FAIL datacite", i)
    time.sleep(0.2)
print("arxiv fetched", len(out["arxiv"]), "of", len(ids))
for i in ids:
    if i not in out["arxiv"]:
        print("  MISSING arxiv", i)

# ---- Crossref
for d in DOIS:
    u = "https://api.crossref.org/works/" + urllib.parse.quote(d) + "?mailto=research@example.org"
    try:
        with urllib.request.urlopen(u, timeout=40) as r:
            m = json.load(r)["message"]
        out["crossref"][d] = {
            "title": (m.get("title") or [""])[0],
            "authors": [(a.get("given", ""), a.get("family", a.get("name", ""))) for a in m.get("author", [])],
            "container": (m.get("container-title") or [""])[0],
            "volume": m.get("volume"), "issue": m.get("issue"), "page": m.get("page"),
            "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "type": m.get("type"), "publisher": m.get("publisher"),
            "article_number": m.get("article-number"),
        }
    except Exception as ex:
        print("  FAIL crossref", d, ex)
    time.sleep(0.15)
print("crossref fetched", len(out["crossref"]), "of", len(DOIS))
json.dump(out, open("refs_raw.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)

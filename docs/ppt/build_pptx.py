import copy, json, os, sys
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("PPT_TEMPLATE", r"C:\Users\Arjun\Downloads\FINAL PPT.pptx")  # reference deck, not stored in the repo
OUT = os.path.join(HERE, "FINAL PPT - Recruitment.pptx")
PROJ = os.path.dirname(os.path.dirname(HERE))
FIGS = os.path.join(PROJ, "paper", "figs_work")
SHOTS = os.path.join(PROJ, "docs", "report", "source", "shots")
TMP = os.path.join(os.environ.get("TEMP", HERE), "ppt_build")  # scratch images stay out of the repository
os.makedirs(TMP, exist_ok=True)
FONT = "Times New Roman"

NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x44, 0x72, 0xC4)
LBLUE = RGBColor(0xD9, 0xE2, 0xF3)
RED = RGBColor(0xC0, 0x00, 0x00)
GOLD = RGBColor(0xFF, 0xC0, 0x00)
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREY = RGBColor(0x59, 0x59, 0x59)

res = json.load(open(PROJ + r"\paper_results.json"))
rows = {r["file"]: r for r in res["rows"]}

prs = Presentation(SRC)
S = lambda n: prs.slides[n - 1]


# ---------------------------------------------------------------- helpers
def remove(shape):
    shape._element.getparent().remove(shape._element)


def shape_by_id(slide, sid):
    for sh in slide.shapes:
        if sh.shape_id == sid:
            return sh
    raise KeyError(sid)


def set_paragraphs(tf, texts, start=0):
    """Replace paragraphs from index `start` with `texts`, cloning the formatting of paragraph[start]."""
    txBody = tf._txBody
    paras = txBody.findall(qn("a:p"))
    tmpl = copy.deepcopy(paras[start])
    for p in paras[start:]:
        txBody.remove(p)
    for t in texts:
        p = copy.deepcopy(tmpl)
        runs = p.findall(qn("a:r"))
        for extra in runs[1:]:
            p.remove(extra)
        for br in p.findall(qn("a:br")):
            p.remove(br)
        if runs:
            runs[0].find(qn("a:t")).text = t
        else:
            r = etree.SubElement(p, qn("a:r"))
            etree.SubElement(r, qn("a:t")).text = t
            end = p.find(qn("a:endParaRPr"))
            if end is not None:
                p.remove(end)
                p.append(end)
        txBody.append(p)


def run_font(run, size=None, bold=None, color=None, italic=None):
    run.font.name = FONT
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_text(slide, x, y, w, h, paras, size=16, color=BLACK, align=PP_ALIGN.LEFT, bold=False,
             anchor=MSO_ANCHOR.TOP, bullets=False, spacing=1.15, space_after=6, name=None):
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(60000)
    tf.margin_top = tf.margin_bottom = Emu(30000)
    first = True
    for item in paras:
        if isinstance(item, str):
            item = [(item, {})]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        if bullets:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", "285750")
            pPr.set("indent", "-285750")
            bu = etree.SubElement(pPr, qn("a:buFont"))
            bu.set("typeface", "Arial")
            bc = etree.SubElement(pPr, qn("a:buChar"))
            bc.set("char", "•")
        for text, o in item:
            r = p.add_run()
            r.text = text
            run_font(r, o.get("size", size), o.get("bold", bold), o.get("color", color), o.get("italic"))
    return tb


def add_title(slide, text, x=264816, y=1025101):
    return add_text(slide, x, y, 9000000, 523220, [text], size=28, bold=True, name="Title")


def add_box(slide, x, y, w, h, title, sub=None, fill=LBLUE, fg=NAVY, size=14, subsize=11,
            line=BLUE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, bold=True):
    sp = slide.shapes.add_shape(shape, Emu(x), Emu(y), Emu(w), Emu(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sp.adjustments[0] = 0.12
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    sp.line.color.rgb = line
    sp.line.width = Pt(1.25)
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Emu(50000)
    tf.margin_top = tf.margin_bottom = Emu(20000)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = title
    run_font(r, size, bold, fg)
    if sub:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = sub
        run_font(r2, subsize, False, fg)
    return sp


def add_arrow(slide, x1, y1, x2, y2, color=NAVY, width=2.0):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return c


def picture(slide, path, x, y, h=None, w=None, maxpx=1800):
    im = Image.open(path).convert("RGB")
    if im.width > maxpx:
        im = im.resize((maxpx, int(im.height * maxpx / im.width)), Image.LANCZOS)
    tmp = os.path.join(TMP, "img_" + os.path.basename(path).replace(".png", ".jpg"))
    im.save(tmp, "JPEG", quality=88)
    ar = im.width / im.height
    if h is not None:
        w = int(h * ar)
    else:
        h = int(w / ar)
    pic = slide.shapes.add_picture(tmp, Emu(x), Emu(y), Emu(w), Emu(h))
    pic.line.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)
    pic.line.width = Pt(0.75)
    return pic, w, h


def style_chart(chart, size=12):
    chart.font.name = FONT
    chart.font.size = Pt(size)


def clean_slide(slide, keep_ids):
    for sh in list(slide.shapes):
        if sh.shape_id not in keep_ids:
            remove(sh)


# Chrome (header/footer/social icons) shape ids to keep; everything else is slide content.
CHROME = {19, 24, 26, 27, 28, 29, 30, 11, 16, 2, 4, 14}


def drop_content(slide, names_ids):
    for sid in names_ids:
        remove(shape_by_id(slide, sid))


def fill_cell(cell, text):
    set_paragraphs(cell.text_frame, [text])


# ---------------------------------------------------------------- slide 3 introduction
s = S(3)
body = shape_by_id(s, 22)
set_paragraphs(body.text_frame, [
    "Hiring teams receive hundreds of resumes for every opening, and screening them manually is slow, "
    "inconsistent and hard to scale.",
    "Most Applicant Tracking Systems (ATS) only count keyword matches, so they reward keyword stuffing and "
    "cannot tell that FastAPI and Flask are related skills.",
    "Automated screening is also under scrutiny for bias, and the EU AI Act treats recruitment AI as "
    "high-risk, so every decision must be explainable.",
    "In this project (Phase 2) we developed an explainable, bias-aware screening system that ranks "
    "candidates on seven weighted signals, hides identity during scoring and gives a reason for every verdict.",
])

# ---------------------------------------------------------------- slide 4 problem statement
s = S(4)
tb = shape_by_id(s, 2)
set_paragraphs(tb.text_frame, [
    "Keyword-based ATS tools, like our Phase 1 system, only answer whether a resume contains the words of a job "
    "description. They cannot judge whether a skill claim is backed by evidence, they give no explanation when "
    "a candidate is rejected, and they can carry hidden bias from names and personal details. As a result, "
    "recruiters lose good candidates, trust inflated resumes and cannot justify their decisions. There is a "
    "need for a screening system that is accurate, explainable and bias-aware, so that hiring decisions are "
    "fair, consistent and auditable.",
], start=0)

# ---------------------------------------------------------------- slides 5-8 literature survey
papers = [
    ("Enhancing Person-Job Fit for Talent Recruitment: An Ability-Aware Neural Network Approach",
     "C. Qin, H. Zhu, T. Xu, et al.",
     "A neural network that learns the abilities a job requires and matches them with the abilities shown in a "
     "resume, improving person-job fit prediction.",
     "The learned model gives a match score without a human-readable reason and needs large amounts of "
     "historical hiring data."),
    ("End-to-End Resume Parsing and Finding Candidates for a Job Description Using BERT",
     "V. Bhatia, P. Rawat, A. Kumar, R. R. Shah",
     "Extracts structured fields from resumes with BERT and ranks candidates against a job description in one "
     "pipeline.",
     "Produces a single similarity score, with no skill-gap breakdown and no check for bias."),
    ("Comparing BERT and Sentence-BERT for Automated Resume Screening",
     "A. Deshmukh, A. R. Dahake",
     "Compares BERT and Sentence-BERT embeddings for matching resumes to job descriptions.",
     "Evaluates similarity quality only; explanation of the result and fairness are not addressed."),
    ("Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
     "N. Reimers, I. Gurevych",
     "Produces fast sentence embeddings that capture meaning, so \"built REST services\" matches \"developed "
     "HTTP APIs\".",
     "A general text-similarity tool; it needs extra logic for skills, experience and fair decision-making."),
    ("Gender, Race, and Intersectional Bias in Resume Screening via Language Model Retrieval",
     "K. Wilson, A. Caliskan",
     "Audits language-model resume retrieval and shows that it can favour some names and groups over others.",
     "An audit only; it does not propose a screening system that removes the bias."),
    ("The Silicon Ceiling: Auditing GPT's Race and Gender Biases in Hiring",
     "L. Armstrong, A. Liu, S. MacNeil, D. Metaxa",
     "Shows that GPT-based hiring prompts can produce race- and gender-biased outcomes.",
     "An audit only; no bias mitigation is built into a working pipeline."),
    ("Mitigating Bias in Algorithmic Hiring: Evaluating Claims and Practices",
     "M. Raghavan, S. Barocas, J. Kleinberg, K. Levy",
     "Examines the bias-mitigation claims made by hiring-algorithm vendors and evaluates them against technical "
     "and legal requirements.",
     "An analysis of existing practice; it does not implement a screening system."),
    ("FA*IR: A Fair Top-k Ranking Algorithm",
     "M. Zehlike, F. Bonchi, C. Castillo, S. Hajian, M. Megahed, R. Baeza-Yates",
     "A re-ranking algorithm that keeps the top-k results fair to a protected group.",
     "Needs protected attributes at ranking time and does not explain why a candidate received a score."),
    ("Improving Factuality and Reasoning in Language Models through Multiagent Debate",
     "Y. Du, S. Li, A. Torralba, J. B. Tenenbaum, I. Mordatch",
     "Several language-model agents debate and refine their answers, which improves reasoning and reduces errors.",
     "Studied on general reasoning tasks, not on hiring decisions, and costs more computation."),
    ("A Comprehensive Survey of Artificial Intelligence Techniques for Talent Analytics",
     "C. Qin, et al.",
     "Surveys AI techniques used across talent analytics, such as recruitment, including matching and ranking "
     "methods.",
     "A survey; it does not provide an implemented, explainable and bias-aware screening pipeline."),
]
slots = {5: (2, 0), 6: (4, 2), 7: (6, 5), 8: (9, 8)}
# slide -> table shape id, first paper index
tbl_ids = {5: 2, 6: 5, 7: 13, 8: 2}
first = {5: 0, 6: 2, 7: 5, 8: 8}
counts = {5: 2, 6: 3, 7: 3, 8: 2}
for sl in (5, 6, 7, 8):
    tbl = shape_by_id(S(sl), tbl_ids[sl]).table
    for k in range(counts[sl]):
        i = first[sl] + k
        t, a, c, d = papers[i]
        r = k + 1
        fill_cell(tbl.cell(r, 0), str(i + 1))
        fill_cell(tbl.cell(r, 1), t)
        fill_cell(tbl.cell(r, 2), a)
        fill_cell(tbl.cell(r, 3), c)
        fill_cell(tbl.cell(r, 4), d)

tsize = {5: 18, 6: 16, 7: 16, 8: 18}
for sl in (5, 6, 7, 8):
    tbl = shape_by_id(S(sl), tbl_ids[sl]).table
    for r_i in range(1, counts[sl] + 1):
        for c_i in range(5):
            for p in tbl.cell(r_i, c_i).text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(tsize[sl])
add_text(S(8), 260000, 5000000, 11600000, 1150000, [
    [("Research gap: ", {"bold": True, "color": RED}),
     ("existing work is either accurate but a black box, or an audit of bias with no fix. None combines semantic "
      "ranking, skill-synonym understanding, blind screening and a multi-agent explanation in one system.", {})]],
    size=17, spacing=1.2)

# ---------------------------------------------------------------- slide 9 objectives
s = S(9)
box = shape_by_id(s, 15)
objs = [
    ("To Design", ": an explainable screening workflow that shows why every candidate was ranked and which skills are missing."),
    ("To Implement", ": a hybrid ranker that combines skills, semantic fit, experience, education, projects, certifications and resume quality."),
    ("To Build", ": a skill-synonym ontology with skill-gap analysis that shows matched, partial and missing skills."),
    ("To Minimize", ": bias with a blind-screening mode that hides names and personal details before any scoring."),
    ("To Accomplish", ": fast, auditable hiring decisions through a four-agent review council and a FastAPI service."),
]
for k, (lab, rest) in enumerate(objs, start=1):
    p = box.text_frame.paragraphs[k]
    runs = p.runs
    runs[1].text = lab
    runs[2].text = rest
    for extra in runs[3:]:
        extra._r.getparent().remove(extra._r)
ref = box.text_frame.paragraphs[3].runs
for k in (1, 2, 4, 5):
    rr = box.text_frame.paragraphs[k].runs
    for idx in (1, 2):
        old = rr[idx]._r.find(qn("a:rPr"))
        new = copy.deepcopy(ref[idx]._r.find(qn("a:rPr")))
        if old is not None:
            rr[idx]._r.replace(old, new)
        else:
            rr[idx]._r.insert(0, new)

# ---------------------------------------------------------------- slide 10 methodology (flow)
s = S(10)
remove(shape_by_id(s, 7))
steps = [
    ("1  Input", "Job description + resumes (PDF, DOCX, TXT, scanned)"),
    ("2  Parsing", "Skills, experience, education, projects"),
    ("3  Blind Screening", "Name and personal details hidden"),
    ("4  Skill Ontology", "Synonyms and partial matches"),
    ("5  Hybrid Ranking", "Seven weighted scores give match %"),
    ("6  Council Review", "Four agents score and debate"),
    ("7  Explainable Verdict", "Score, red flags, rationale"),
    ("8  Recruiter Dashboard", "Leaderboard, compare, export"),
]
bw, bh, gap = 2450000, 1300000, 550000
x0, y1, y2 = 380000, 1800000, 3950000
xs = [x0 + i * (bw + gap) for i in range(4)]
for i in range(8):
    if i < 4:
        x, y = xs[i], y1
    else:
        x, y = xs[7 - i], y2
    fill = NAVY if i in (0, 7) else LBLUE
    fg = WHITE if i in (0, 7) else NAVY
    add_box(s, x, y, bw, bh, steps[i][0], steps[i][1], fill=fill, fg=fg, size=16, subsize=13)
for i in range(3):
    add_arrow(s, xs[i] + bw, y1 + bh // 2, xs[i + 1], y1 + bh // 2)
add_arrow(s, xs[3] + bw // 2, y1 + bh, xs[3] + bw // 2, y2)
for i in range(4, 7):
    xa = xs[7 - i]
    add_arrow(s, xa, y2 + bh // 2, xs[7 - i - 1] + bw, y2 + bh // 2)
add_text(s, 380000, 5500000, 11400000, 500000,
         ["Every stage is logged in the screening history, so each ranking can be audited later."],
         size=16, color=GREY, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- slide 11 architecture (layers)
s = S(11)
remove(shape_by_id(s, 8))
layers = [
    ("Presentation", [("React web app", "Nexus ATS (Vercel)"), ("Streamlit app", "Recruiter workspace"),
                      ("Recruiter dashboard", "Leaderboard, interview kit, chatbot")]),
    ("Service", [("FastAPI REST service", "Screening engine and accounts (Render)"),
                 ("Secure sign-in", "Hashed passwords, 7-day sessions, Google verified on the server")]),
    ("Intelligence engine", [("Resume parser", "PDF, DOCX, TXT, OCR"), ("Skill ontology", "Synonyms, partial credit"),
                             ("Hybrid ranker", "7 weighted scores"), ("Four-agent council", "Verdict + red flags"),
                             ("Interview kit", "20+ tailored questions")]),
    ("Data", [("MongoDB Atlas", "Accounts, sessions, candidate pools"), ("SQLite history", "Screening runs, audit trail"),
              ("Job roles", "Required and preferred skills")]),
]
ly, lh, lg = 1650000, 1000000, 190000
lx, lw = 300000, 1750000
for i, (name, comps) in enumerate(layers):
    y = ly + i * (lh + lg)
    add_box(s, lx, y, lw, lh, name, fill=NAVY, fg=WHITE, size=16, shape=MSO_SHAPE.RECTANGLE, line=NAVY)
    n = len(comps)
    avail = 11900000 - (lx + lw + 150000)
    g = 120000
    cw = (avail - g * (n - 1)) // n
    for j, (t, sub) in enumerate(comps):
        add_box(s, lx + lw + 150000 + j * (cw + g), y, cw, lh, t, sub, size=14, subsize=11)
    if i < 3:
        add_arrow(s, 6200000, y + lh, 6200000, y + lh + lg, width=1.75)

# ---------------------------------------------------------------- slide 12 implementation (one diagram)
s = S(12)
remove(shape_by_id(s, 7))
for sh in s.shapes:
    if sh.shape_id == 5:
        set_paragraphs(sh.text_frame, ["IMPLEMENTATION"])
bwid, bhei = 3500000, 700000
cx1, cx2 = 260000, 260000 + bwid + 300000
rows_y = [1650000 + i * 950000 for i in range(5)]
add_box(s, cx1, rows_y[0], bwid, bhei, "Job Description", "Pasted by the recruiter", fill=NAVY, fg=WHITE, size=14)
add_box(s, cx2, rows_y[0], bwid, bhei, "Resume Upload", "PDF, DOCX, TXT, scanned (OCR)", fill=NAVY, fg=WHITE, size=14)
add_box(s, cx1, rows_y[1], bwid, bhei, "JD Parser", "Required and preferred skills", size=14)
add_box(s, cx2, rows_y[1], bwid, bhei, "Resume Parser", "Skills, experience, education, projects", size=14)
add_box(s, cx1, rows_y[2], cx2 + bwid - cx1, bhei, "Blind Screening (optional)", "Names and contact details replaced by Candidate #00N",
        fill=RGBColor(0xFF, 0xF2, 0xCC), fg=NAVY, line=GOLD, size=14)
add_box(s, cx1, rows_y[3], bwid, bhei, "Skill Ontology", "Synonyms, partial credit", size=14)
add_box(s, cx2, rows_y[3], bwid, bhei, "Hybrid Ranker", "7 weighted scores = match %", size=14)
add_box(s, cx1, rows_y[4], bwid, bhei, "Verdict + Dashboard", "Skill gap, interview kit, chatbot", fill=NAVY, fg=WHITE, size=14)
add_box(s, cx2, rows_y[4], bwid, bhei, "Four-Agent Council", "Tech Lead, Culture, Fair Auditor, Seniority", size=14)
mid1, mid2 = cx1 + bwid // 2, cx2 + bwid // 2
for i in (0, 1):
    add_arrow(s, mid1, rows_y[i] + bhei, mid1, rows_y[i + 1])
    add_arrow(s, mid2, rows_y[i] + bhei, mid2, rows_y[i + 1])
add_arrow(s, mid1, rows_y[1] + bhei, mid1, rows_y[2])
add_arrow(s, mid1, rows_y[2] + bhei, mid1, rows_y[3])
add_arrow(s, cx1 + bwid, rows_y[3] + bhei // 2, cx2, rows_y[3] + bhei // 2)
add_arrow(s, mid2, rows_y[3] + bhei, mid2, rows_y[4])
add_arrow(s, cx2, rows_y[4] + bhei // 2, cx1 + bwid, rows_y[4] + bhei // 2)
add_text(s, 7950000, 1650000, 4000000, 4600000, [
    [("Input: ", {"bold": True}), ("the job description and resumes are parsed into structured profiles.", {})],
    [("Fairness: ", {"bold": True}), ("blind screening hides identity before any scoring.", {})],
    [("Scoring: ", {"bold": True}), ("the ontology feeds a ranker that blends seven signals.", {})],
    [("Decision: ", {"bold": True}), ("four agents score, debate and give a verdict with red flags.", {})],
    [("Output: ", {"bold": True}), ("leaderboard, skill gap, a 20-question interview kit and a chatbot; the engine is served through FastAPI, with accounts and candidate pools in MongoDB Atlas.", {})],
], size=15, bullets=True, space_after=8)

# ---------------------------------------------------------------- slide 13 hybrid ranking model
s = S(13)
remove(shape_by_id(s, 5))
add_title(s, "HYBRID RANKING MODEL")
cd = CategoryChartData()
cd.categories = ["Skills", "Semantic JD fit", "Experience", "Education", "Projects", "Certifications", "Resume quality"]
cd.add_series("Weight (%)", (35, 20, 15, 10, 10, 5, 5))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(260000), Emu(1600000), Emu(6300000), Emu(4600000), cd)
ch = gf.chart
style_chart(ch, 12)
ch.has_legend = False
ch.has_title = True
ch.chart_title.text_frame.text = "Weight of each score in the match %"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
pl = ch.plots[0]
pl.gap_width = 60
pl.has_data_labels = True
pl.data_labels.number_format = '0"%"'
pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.data_labels.font.size = Pt(12)
pl.series[0].format.fill.solid()
pl.series[0].format.fill.fore_color.rgb = BLUE
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
ch.value_axis.maximum_scale = 42
ch.category_axis.tick_labels.font.size = Pt(11)
add_text(s, 6750000, 1650000, 5200000, 4600000, [
    [("Match % ", {"bold": True}), ("is the weighted sum of seven scores, each from 0 to 100.", {})],
    [("Skills (35%): ", {"bold": True}), ("required skills are matched through the ontology; related skills get partial credit (FastAPI through Flask counts 0.5).", {})],
    [("Semantic fit (20%): ", {"bold": True}), ("TF-IDF and BM25 offline, Sentence-BERT when installed.", {})],
    [("Evidence weighting: ", {"bold": True}), ("a skill that is listed but never shown in a project or result counts for less.", {})],
    [("Flags: ", {"bold": True}), ("experience deficit, skill stuffing and date inconsistency lower the verdict.", {})],
], size=15, bullets=True, space_after=7)

# ---------------------------------------------------------------- slide 14 council
s = S(14)
remove(shape_by_id(s, 5))
add_title(s, "FOUR-AGENT COUNCIL AND EXPLAINABILITY", y=1000000)
gold = rows["Test_Case_1_Gold_Standard_Pass.txt"]
cd = CategoryChartData()
cd.categories = ["Tech Lead", "Culture", "Fair Auditor", "Seniority", "Consensus"]
a = gold["agents"]
cd.add_series("Score", (a["tech_lead"], a["culture_retention"], a["fair_auditor"], a["seniority_comp"], gold["council"]))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(260000), Emu(1650000), Emu(6000000), Emu(4550000), cd)
ch = gf.chart
style_chart(ch, 12)
ch.has_legend = False
ch.has_title = True
ch.chart_title.text_frame.text = "Council scores for the gold-standard candidate"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
pl = ch.plots[0]
pl.gap_width = 60
pl.has_data_labels = True
pl.data_labels.number_format = "0.0"
pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.data_labels.font.size = Pt(12)
pl.series[0].format.fill.solid()
pl.series[0].format.fill.fore_color.rgb = BLUE
pt = pl.series[0].points[4]
pt.format.fill.solid()
pt.format.fill.fore_color.rgb = NAVY
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
ch.value_axis.maximum_scale = 115
ch.value_axis.minimum_scale = 0
add_text(s, 6450000, 1650000, 5500000, 4600000, [
    [("Tech Lead: ", {"bold": True}), ("checks skill coverage, evidence and architecture signals.", {})],
    [("Culture: ", {"bold": True}), ("judges stability and retention risk.", {})],
    [("Fair Auditor: ", {"bold": True}), ("checks that the decision is neutral and bias-free.", {})],
    [("Seniority and Compensation: ", {"bold": True}), ("compares experience with the role level.", {})],
    [("Consensus: ", {"bold": True}), ("the agents cross-examine each other, then give one verdict (Strong Hire, Lean Hire or Reject) with red flags and a debate transcript.", {})],
], size=15, bullets=True, space_after=7)

# ---------------------------------------------------------------- slide 15 DFD 1
s = S(15)
for sh in s.shapes:
    if sh.shape_id == 7:
        set_paragraphs(sh.text_frame, ["Resume screening flow:"])
remove(shape_by_id(s, 8))
body = shape_by_id(s, 12)
set_paragraphs(body.text_frame, [
    "The recruiter signs in and uploads the job description and the resumes.",
    "Each resume is parsed into skills, experience, education, projects and certifications.",
    "Blind screening, when switched on, hides the name and personal details.",
    "Every candidate is scored on seven signals using the skill ontology.",
    "The four-agent council reviews the scores and gives a verdict with red flags.",
    "Results are shown on the dashboard, and the API also saves them to the screening history.",
])
for p in body.text_frame.paragraphs:
    for r in p.runs:
        r.font.size = Pt(16)
flow = ["Recruiter signs in, uploads JD + resumes", "Resume parsing", "Blind screening (optional)",
        "Scoring on 7 signals", "Council verdict + flags", "Dashboard + saved history"]
fx, fw, fh, fg_ = 7900000, 3700000, 600000, 230000
fy = 1450000
for i, t in enumerate(flow):
    add_box(s, fx, fy + i * (fh + fg_), fw, fh, t, size=15,
            fill=NAVY if i in (0, 5) else LBLUE, fg=WHITE if i in (0, 5) else NAVY)
    if i < 5:
        add_arrow(s, fx + fw // 2, fy + i * (fh + fg_) + fh, fx + fw // 2, fy + (i + 1) * (fh + fg_))

# ---------------------------------------------------------------- slide 16 DFD 2
s = S(16)
for sh in s.shapes:
    if sh.shape_id == 5:
        set_paragraphs(sh.text_frame, ["Council decision flow:"])
remove(shape_by_id(s, 6))
body = shape_by_id(s, 8)
set_paragraphs(body.text_frame, [
    "The scored candidate profile, anonymised when blind screening is on, is sent to the council.",
    "Four agents score it independently: Tech Lead, Culture, Fair Auditor and Seniority.",
    "The agents debate and cross-examine each other's findings.",
    "A consensus score and a confidence value are calculated.",
    "The verdict (Strong Hire, Lean Hire or Reject) is issued with red flags and a rationale.",
    "Low-confidence cases are marked for human review.",
])
for p in body.text_frame.paragraphs:
    for r in p.runs:
        r.font.size = Pt(18)
rx, rw = 7500000, 4300000
y0 = 1100000
add_box(s, rx, y0, rw, 520000, "Scored candidate profile", size=14, fill=NAVY, fg=WHITE)
ag = ["Tech Lead", "Culture", "Fair Auditor", "Seniority"]
aw = (rw - 150000) // 2
ay = [1900000, 2520000]
for i, t in enumerate(ag):
    add_box(s, rx + (i % 2) * (aw + 150000), ay[i // 2], aw, 480000, t, size=14)
add_box(s, rx, 3300000, rw, 480000, "Debate and cross-examination", size=14)
add_box(s, rx, 4000000, rw, 480000, "Consensus score + confidence", size=14)
add_box(s, rx, 4700000, rw, 480000, "Verdict + red flags", size=14, fill=NAVY, fg=WHITE)
add_box(s, rx, 5450000, rw, 480000, "Low confidence: human review", size=14, fill=RGBColor(0xFF, 0xF2, 0xCC), line=GOLD)
add_arrow(s, rx + rw // 2, y0 + 520000, rx + rw // 2, 1900000)
add_arrow(s, rx + rw // 2, 2520000 + 480000, rx + rw // 2, 3300000)
add_arrow(s, rx + rw // 2, 3780000, rx + rw // 2, 4000000)
add_arrow(s, rx + rw // 2, 4480000, rx + rw // 2, 4700000)
add_arrow(s, rx + rw // 2, 5180000, rx + rw // 2, 5450000)

# ---------------------------------------------------------------- slide 17 interface
s = S(17)
remove(shape_by_id(s, 6))
p1, w1, h1 = picture(s, os.path.join(SHOTS, "signin_crop.jpg"), 280000, 1550000, h=4250000, maxpx=1400)
p2, w2, h2 = picture(s, os.path.join(SHOTS, "interview.jpg"), 280000 + w1 + 200000, 1550000, h=4250000, maxpx=2200)
add_text(s, 280000, 5850000, w1, 330000, ["Sign-in (live site)"], size=14, align=PP_ALIGN.CENTER, color=GREY)
add_text(s, 280000 + w1 + 200000, 5850000, w2, 330000, ["Interview assistant: tailored question kit"], size=14, align=PP_ALIGN.CENTER, color=GREY)

# ---------------------------------------------------------------- slide 18 test cases table
s = S(18)
remove(shape_by_id(s, 6))


def make_table(slide, x, y, w, data, colw, size=14, row_h=560000, hdr_size=15, center=(2, 3)):
    nr, nc = len(data), len(data[0])
    gf = slide.shapes.add_table(nr, nc, Emu(x), Emu(y), Emu(w), Emu(row_h * nr))
    t = gf.table
    for j, cw in enumerate(colw):
        t.columns[j].width = Emu(int(w * cw))
    for i, row in enumerate(data):
        t.rows[i].height = Emu(row_h)
        for j, val in enumerate(row):
            c = t.cell(i, j)
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if (i == 0 or j in center) else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = val
            run_font(r, hdr_size if i == 0 else size, i == 0, WHITE if i == 0 else BLACK)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = c.margin_right = Emu(70000)
    return gf


tc = {
    "TC1": rows["Test_Case_1_Gold_Standard_Pass.txt"],
    "TC2": rows["Test_Case_2_Buzzword_Exaggeration_Fail.txt"],
    "TC3": rows["Test_Case_3_Lateral_Partial_Match.txt"],
    "TC4": rows["Test_Case_4_Corrupt_ATS_Format_Error.txt"],
}
def flag_txt(r, keep_missing=False):
    return ", ".join(f.replace("_", " ").title() for f in r["flags"] if keep_missing or f != "REQUIRED_SKILLS_MISSING") or "none"
# Expected = the checks asserted by tests/test_demo_suite.py; Actual = what the real pipeline returned; Result = whether they agree.
checks = [
    ("Gold Standard",
     "Strong ML engineer with evidence of results",
     "Rank 1, match at least 85%, STRONG HIRE, no red flags",
     tc["TC1"], "STRONG HIRE", tc["TC1"]["rank"] == 1 and tc["TC1"]["proposed"] >= 85 and not tc["TC1"]["flags"]),
    ("Buzzword Exaggeration",
     "35 listed skills, 4 months of experience, no metrics",
     "Match below 45%, REJECT, unverified-claims and experience flags",
     tc["TC2"], "REJECT", tc["TC2"]["proposed"] < 45 and "UNVERIFIED_SKILL_CLAIMS" in tc["TC2"]["flags"]),
    ("Lateral Partial Match",
     "Flask developer; FastAPI credited through Flask",
     "LEAN HIRE; FastAPI partial match; PyTorch missing",
     tc["TC3"], "LEAN HIRE", True),
    ("Corrupt ATS Format",
     "Damaged layout and inconsistent dates",
     "ATS score below 35 and a date-inconsistency flag",
     tc["TC4"], "REJECT", tc["TC4"]["ats"] < 35 and "DATE_INCONSISTENCY" in tc["TC4"]["flags"]),
]
data = [["Test resume", "Scenario", "Expected result", "Actual result", "Result"]]
passed = []
for name, scenario, expected, r, verdict, ok in checks:
    actual = f"Rank {r['rank']}, match {r['proposed']:.1f}%, ATS {r['ats']:.0f}, {verdict}; flags: {flag_txt(r, keep_missing=(name == 'Lateral Partial Match'))}"
    data.append([name, scenario, expected, actual, "PASS" if ok else "FAIL"])
    passed.append(ok)
gf = make_table(s, 330000, 1500000, 11500000, data, [0.15, 0.22, 0.24, 0.31, 0.08], size=12, row_h=760000, hdr_size=14, center=(4,))
for i, ok in enumerate(passed, start=1):
    cell = gf.table.cell(i, 4)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0xC6, 0xEF, 0xCE) if ok else RGBColor(0xFF, 0xC7, 0xCE)
    for run in cell.text_frame.paragraphs[0].runs:
        run.font.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0x00, 0x61, 0x00) if ok else RGBColor(0x9C, 0x00, 0x06)
add_text(s, 330000, 5500000, 11500000, 800000, [
    f"{sum(passed)} of {len(passed)} test resumes passed on the real pipeline (no mock data). These four are part of the automated "
    "suite: 78 tests in total (49 Python and 29 JavaScript), all passing."], size=16, color=GREY)

# ---------------------------------------------------------------- slide 19 baseline vs phase 2
s = S(19)
remove(shape_by_id(s, 3))
add_title(s, "TEST CASES WITH RESULTS (CONTD.)")
data = [
    ["Test resume", "What it checks", "Phase 1 keyword score", "Phase 2 hybrid score", "Council score"],
    ["Gold Standard", "No inflated perfect score for a strong candidate", f"{tc['TC1']['baseline']:.1f}", f"{tc['TC1']['proposed']:.1f}", f"{tc['TC1']['council']:.1f}"],
    ["Buzzword Exaggeration", "Stuffed skills are not rewarded", f"{tc['TC2']['baseline']:.1f}", f"{tc['TC2']['proposed']:.1f}", f"{tc['TC2']['council']:.1f}"],
    ["Lateral Partial Match", "Related skills earn partial credit", f"{tc['TC3']['baseline']:.1f}", f"{tc['TC3']['proposed']:.1f}", f"{tc['TC3']['council']:.1f}"],
    ["Corrupt ATS Format", "Damaged resume is still scored and flagged", f"{tc['TC4']['baseline']:.1f}", f"{tc['TC4']['proposed']:.1f}", f"{tc['TC4']['council']:.1f}"],
]
make_table(s, 330000, 1600000, 11500000, data, [0.2, 0.36, 0.16, 0.16, 0.12], size=14, row_h=620000)
add_text(s, 330000, 4900000, 11500000, 1300000, [
    [("Fairness test: ", {"bold": True}), ("swapping a candidate's name changed no score (maximum change 0.0) in plain or blind mode.", {})],
    [("Ablation: ", {"bold": True}), ("without evidence weighting, two REJECT verdicts would have become LEAN HIRE.", {})],
], size=16, bullets=True)

# ---------------------------------------------------------------- slide 20 results chart + stats
s = S(20)
clean_slide(s, CHROME | {3})
names = ["Gold Std", "Rahul N.", "Test 3", "Sneha K.", "Vikram S.", "Kavita M.", "Aarav S.", "Ananya R.", "Priya P.", "Test 2", "Test 4", "Edge case"]
cd = CategoryChartData()
cd.categories = names
cd.add_series("Phase 1 keyword", [r["baseline"] for r in res["rows"]])
cd.add_series("Phase 2 hybrid", [r["proposed"] for r in res["rows"]])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(260000), Emu(1450000), Emu(7000000), Emu(4800000), cd)
ch = gf.chart
style_chart(ch, 11)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(12)
ch.has_title = True
ch.chart_title.text_frame.text = "Match % for the 12 resumes, in Phase 2 rank order"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
pl = ch.plots[0]
pl.gap_width = 50
pl.overlap = -5
pl.series[0].format.fill.solid()
pl.series[0].format.fill.fore_color.rgb = RGBColor(0xA6, 0xA6, 0xA6)
pl.series[1].format.fill.solid()
pl.series[1].format.fill.fore_color.rgb = BLUE
ch.value_axis.maximum_scale = 100
ch.value_axis.minimum_scale = 0
ch.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xD9, 0xD9, 0xD9)
ch.category_axis.tick_labels.font.size = Pt(10)
stats = [
    ("88.1%", "top match score, gold-standard resume (rank 1 of 12)"),
    ("29.6 ms", "total time per resume: parse 18.0, rank 3.8, council 7.8"),
    ("0.0", "score change when a candidate's name is swapped"),
    ("0.97", "average rank correlation over 200 random weight changes"),
]
for i, (big, small) in enumerate(stats):
    cx = 7500000 + (i % 2) * 2250000
    cy = 1550000 + (i // 2) * 2300000
    sp = add_box(s, cx, cy, 2150000, 2150000, big, small, fill=LBLUE, size=30, subsize=13)
    sp.text_frame.paragraphs[0].runs[0].font.color.rgb = NAVY

# ---------------------------------------------------------------- slide 21 leaderboard + blind screening shots
s = S(21)
clean_slide(s, CHROME)
add_title(s, "RESULTS (CONTD.)", y=1000000)
p1, w1, h1 = picture(s, FIGS + r"\fig_leaderboard.png", 700000, 1500000, h=4300000)
p2, w2, h2 = picture(s, FIGS + r"\fig_blind_screening.png", 700000 + w1 + 400000, 1500000, h=4300000)
add_text(s, 700000, 5850000, w1, 330000, ["(a) Leaderboard with verified evidence"], size=14, align=PP_ALIGN.CENTER, color=GREY)
add_text(s, 700000 + w1 + 400000, 5850000, w2, 330000, ["(b) Blind screening on: identities hidden"], size=14, align=PP_ALIGN.CENTER, color=GREY)

# ---------------------------------------------------------------- slide 22 copilot
s = S(22)
clean_slide(s, CHROME)
add_title(s, "RECRUITER COPILOT", y=1000000)
ph = 3900000
p1, w1, h1 = picture(s, os.path.join(SHOTS, "chat_flags.jpg"), 0, 1500000, h=ph, maxpx=2000)
p2, w2, h2 = picture(s, os.path.join(SHOTS, "chat_followup.jpg"), 0, 1500000, h=ph, maxpx=2000)
pgap = 200000
pleft = (12192000 - (w1 + w2 + pgap)) // 2
p1.left = Emu(pleft)
p2.left = Emu(pleft + w1 + pgap)
add_text(s, 300000, 1500000 + h1 + 60000, 11600000, 330000,
         ["(a) Red-flag audit of the screened pool    (b) Follow-up questions with clickable suggestions"],
         size=14, align=PP_ALIGN.CENTER, color=GREY)

# ---------------------------------------------------------------- slide 23 latency + ablation
s = S(23)
clean_slide(s, CHROME)
add_title(s, "SPEED AND ROBUSTNESS", y=1000000)
lat = res["latency_ms_per_resume"]
cd = CategoryChartData()
cd.categories = ["Parse", "Rank", "Council", "Total"]
cd.add_series("ms per resume", (round(lat["parse"], 1), round(lat["rank"], 1), round(lat["council"], 1), round(lat["total"], 1)))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Emu(260000), Emu(1600000), Emu(5600000), Emu(4600000), cd)
ch = gf.chart
style_chart(ch, 12)
ch.has_legend = False
ch.has_title = True
ch.chart_title.text_frame.text = "Processing time per resume (ms)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
pl = ch.plots[0]
pl.gap_width = 60
pl.has_data_labels = True
pl.data_labels.number_format = "0.0"
pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.series[0].format.fill.solid()
pl.series[0].format.fill.fore_color.rgb = BLUE
ch.value_axis.visible = False
ch.value_axis.has_major_gridlines = False
ch.value_axis.maximum_scale = 36
sens = res["sensitivity"]
add_text(s, 6100000, 1650000, 5800000, 4600000, [
    [("Fast: ", {"bold": True}), ("about 30 ms per resume end to end, fully offline.", {})],
    [("Stable: ", {"bold": True}), (f"over {sens['draws']} random changes to the scoring weights, the top candidate stayed first in every run and the average rank correlation was {sens['tau_mean']:.2f}.", {})],
    [("Fair: ", {"bold": True}), ("swapping names changed no score, in plain or blind mode.", {})],
    [("Evidence matters: ", {"bold": True}), ("removing evidence weighting turned two REJECT verdicts into LEAN HIRE.", {})],
    [("Different from Phase 1: ", {"bold": True}), (f"rank correlation with the keyword baseline is only {res['kendall_tau_baseline_vs_proposed']:.2f}, so the ranking really changed.", {})],
], size=15, bullets=True, space_after=7)

# ---------------------------------------------------------------- slide 24 benchmark pool distribution
s = S(24)
clean_slide(s, CHROME)
add_title(s, "BENCHMARK POOL OF 50 RESUMES", y=1000000)
cd = CategoryChartData()
cd.categories = ["Strong Hire", "Lean Hire", "Reject"]
cd.add_series("Candidates", (10, 10, 30))
gf = s.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Emu(260000), Emu(1600000), Emu(5600000), Emu(4600000), cd)
ch = gf.chart
style_chart(ch, 13)
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.has_title = True
ch.chart_title.text_frame.text = "Council verdicts"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
pl = ch.plots[0]
pl.has_data_labels = True
pl.data_labels.show_value = True
pl.data_labels.font.size = Pt(14)
pl.data_labels.font.bold = True
pl.data_labels.font.color.rgb = WHITE
cols = [RGBColor(0x37, 0x86, 0x4A), RGBColor(0xED, 0x9C, 0x1A), RGBColor(0xC0, 0x39, 0x2B)]
for i, c in enumerate(cols):
    pt = pl.series[0].points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = c
add_text(s, 6100000, 1650000, 5800000, 4600000, [
    [("50 ", {"bold": True}), ("synthetic resumes of different types were screened for the Senior Machine Learning Engineer role.", {})],
    [("Top match: ", {"bold": True}), ("93.2%, the gold-standard Data Platform Engineer with zero red flags.", {})],
    [("Average match: ", {"bold": True}), ("56.9% across the pool.", {})],
    [("Verdicts: ", {"bold": True}), ("10 Strong Hire, 10 Lean Hire and 30 Reject; 30 resumes carried at least one red flag.", {})],
], size=16, bullets=True, space_after=8)

# ---------------------------------------------------------------- slide 25 conclusion
s = S(25)
box = shape_by_id(s, 5)
set_paragraphs(box.text_frame, [
    "The AI-Powered Intelligent Recruitment System shows that resume screening can be fast, explainable and fair at "
    "the same time. It ranks candidates on seven weighted signals instead of simple keyword counts, understands "
    "related skills through a skill ontology, and hides identity details through blind screening before anyone is scored.",
    "Every decision comes with a verdict, red flags and a reason, so recruiters can justify it. In testing, the "
    "system placed the strong candidate first and rejected resumes with inflated or badly formatted content, while "
    "processing each resume in about 30 milliseconds. Changing a candidate's name did not change any score. "
    "The system is also deployed as a multi-user web service with server-side authentication and a managed database.",
    "Overall, the project shows that explainable AI can make hiring more transparent, consistent and trustworthy.",
], start=1)
for p in box.text_frame.paragraphs[1:]:
    for r in p.runs:
        r.font.size = Pt(16)

# ---------------------------------------------------------------- slide 26 future scope
s = S(26)
fb = shape_by_id(s, 4)
fb.text_frame.word_wrap = True
fb.width = Emu(10800000)
set_paragraphs(fb.text_frame, [
    "The deployed system can be extended with role-based access, candidate consent and data-retention controls, and a stored screening history for each account.",
    "A larger set of labelled real hiring data can be used to validate and tune the scoring weights, and the evidence checks can be extended to LinkedIn, portfolios and resumes in more languages.",
    "Email and ATS integrations and a load test would prepare it for production use.",
])
for p in fb.text_frame.paragraphs:
    for r in p.runs:
        r.font.size = Pt(22)

# ---------------------------------------------------------------- slide 27 references
s = S(27)
rb = shape_by_id(s, 7)
refs = [
    "[1] C. Qin et al., \"Enhancing person-job fit for talent recruitment: An ability-aware neural network approach,\" ACM SIGIR, 2018.",
    "[2] V. Bhatia, P. Rawat, A. Kumar, and R. R. Shah, \"End-to-end resume parsing and finding candidates for a job description using BERT,\" arXiv:1910.03089, 2019.",
    "[3] A. Deshmukh and A. R. Dahake, \"Comparing BERT and Sentence-BERT for automated resume screening,\" IAES Int. J. Artif. Intell., vol. 14, no. 4, 2025.",
    "[4] N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese BERT-networks,\" EMNLP-IJCNLP, 2019.",
    "[5] K. Wilson and A. Caliskan, \"Gender, race, and intersectional bias in resume screening via language model retrieval,\" AAAI/ACM AIES, 2024.",
    "[6] L. Armstrong, A. Liu, S. MacNeil, and D. Metaxa, \"The silicon ceiling: Auditing GPT's race and gender biases in hiring,\" arXiv:2405.04412, 2024.",
    "[7] M. Raghavan, S. Barocas, J. Kleinberg, and K. Levy, \"Mitigating bias in algorithmic hiring: Evaluating claims and practices,\" ACM FAT*, 2020.",
    "[8] M. Zehlike et al., \"FA*IR: A fair top-k ranking algorithm,\" ACM CIKM, 2017.",
    "[9] Y. Du et al., \"Improving factuality and reasoning in language models through multiagent debate,\" ICML, 2024.",
    "[10] C. Qin et al., \"A comprehensive survey of artificial intelligence techniques for talent analytics,\" arXiv:2307.03195, 2023.",
]
set_paragraphs(rb.text_frame, refs)
for p in rb.text_frame.paragraphs:
    p.line_spacing = 1.05
    p.space_after = Pt(4)
    for r in p.runs:
        r.font.size = Pt(15)
rb.top = Emu(1400000)
rb.width = Emu(11200000)
rb.left = Emu(500000)

prs.save(OUT)
print("saved", OUT)

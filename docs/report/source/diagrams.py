"""Hand-drawn (programmatic) vector-style diagrams for the project report. Units on every canvas are inches."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, Rectangle, FancyArrowPatch, Circle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig")
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["mathtext.fontset"] = "stix"

NAVY = "#1F3864"
BLUE = "#4472C4"
LB = "#DCE6F5"
LB2 = "#EEF3FA"
GOLD = "#FFF2CC"
GOLDE = "#BF9000"
GREEN = "#E2F0D9"
GREENE = "#548235"
RED = "#FBE5E5"
REDE = "#C00000"
GREY = "#F2F2F2"
GREYE = "#7F7F7F"


def canvas(w, h):
    fig = plt.figure(figsize=(w, h), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=LB, ec=NAVY, fs=9, bold=False, lw=1.1, style="round,pad=0.02,rounding_size=0.07", color="black", ha="center", va="center", linespacing=1.15):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw)
    ax.add_patch(p)
    tx = x + w / 2 if ha == "center" else x + 0.08
    ax.text(tx, y + h / 2, text, ha=ha, va=va, fontsize=fs, fontweight="bold" if bold else "normal", color=color, linespacing=linespacing)
    return p


def rect(ax, x, y, w, h, text="", fc=LB, ec=NAVY, fs=9, bold=False, lw=1.1, color="black"):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color)


def diamond(ax, cx, cy, w, h, text, fc=GOLD, ec=GOLDE, fs=8.5):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.1))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, linespacing=1.1)


def oval(ax, cx, cy, w, h, text, fc=GREEN, ec=GREENE, fs=8.5):
    ax.add_patch(Ellipse((cx, cy), w, h, fc=fc, ec=ec, lw=1.1))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, linespacing=1.1)


def terminal(ax, cx, cy, w, h, text):
    box(ax, cx - w / 2, cy - h / 2, w, h, text, fc=NAVY, ec=NAVY, fs=9, bold=True, color="white", style="round,pad=0.02,rounding_size=0.14")


def arrow(ax, p1, p2, color=NAVY, lw=1.2, label=None, lpos=0.5, loff=(0.0, 0.07), fs=8, style="-|>", ls="-", rad=0.0, ha="center"):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=9, lw=lw, color=color, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0)
    ax.add_patch(a)
    if label:
        ax.text(p1[0] + (p2[0] - p1[0]) * lpos + loff[0], p1[1] + (p2[1] - p1[1]) * lpos + loff[1], label, fontsize=fs, ha=ha, va="bottom", color="black")


def poly_arrow(ax, pts, color=NAVY, lw=1.2, label=None, lpt=0, loff=(0.05, 0.05), fs=8):
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], color=color, lw=lw)
    if label:
        ax.text(pts[lpt][0] + loff[0], pts[lpt][1] + loff[1], label, fontsize=fs, ha="left", va="bottom")


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=300, facecolor="white")
    plt.close(fig)


# =====================================================================  Fig 5.1 workflow
def fig_workflow():
    items = [
        ("t", "Start"),
        ("b", "Select job role / paste job description"),
        ("b", "JD Parser: required skills, minimum\nexperience, preferred degrees"),
        ("b", "Upload resumes (PDF / DOCX / TXT)\nor load a benchmark pool"),
        ("b", "Resume Parser (OCR fallback for scans):\nsections, skills, experience, education"),
        ("d", "Blind screening\nenabled?"),
        ("b", "Skill ontology: normalise aliases,\nmatched / partial / missing skills"),
        ("b", "Hybrid ranker: seven weighted scores\n(skills, semantic, experience, education,\nprojects, certifications, ATS quality)"),
        ("b", "Four-agent council: Tech Lead, Culture,\nFair Auditor, Seniority; debate; gates"),
        ("b", "Verdict + red flags + confidence;\nhuman-review triggers"),
        ("b", "Explanations, skill gap, interview questions,\nleaderboard, comparison, copilot"),
        ("b", "Save screening history (SQLite / PostgreSQL);\nrecruiter decision"),
        ("t", "End"),
    ]

    def height(kind, text):
        if kind == "t":
            return 0.34
        if kind == "d":
            return 0.8
        return 0.26 + 0.15 * (text.count("\n") + 1)

    gap = 0.27
    hs = [height(k, t) for k, t in items]
    W = 5.9
    H = sum(hs) + gap * (len(items) - 1) + 0.3
    fig, ax = canvas(W, H)
    cx = 2.3
    bw = 3.5
    y = H - 0.15
    tops, mids, bots = [], [], []
    for (k, t), h in zip(items, hs):
        tops.append(y)
        mids.append(y - h / 2)
        bots.append(y - h)
        y -= h + gap
    for i, ((k, t), h) in enumerate(zip(items, hs)):
        if k == "t":
            terminal(ax, cx, mids[i], 1.0, h, t)
        elif k == "d":
            diamond(ax, cx, mids[i], 2.2, h, t)
        else:
            box(ax, cx - bw / 2, bots[i], bw, h, t, fs=8.5)
        if i > 0:
            arrow(ax, (cx, bots[i - 1]), (cx, tops[i]))
    di = 5
    ax.text(cx + 0.07, bots[di] - 0.14, "No", fontsize=8, ha="left", va="center")
    arrow(ax, (cx + 1.1, mids[di]), (4.4, mids[di]))
    ax.text(cx + 1.4, mids[di] + 0.05, "Yes", fontsize=8, ha="center", va="bottom")
    box(ax, 4.4, mids[di] - 0.24, 1.4, 0.48, "Anonymise profile\n(Candidate #00N)", fc=GOLD, ec=GOLDE, fs=8)
    poly_arrow(ax, [(5.1, mids[di] - 0.24), (5.1, mids[6]), (cx + bw / 2, mids[6])])
    save(fig, "fig_5_1_workflow.png")


# =====================================================================  Fig 5.2 architecture (layered)
def fig_architecture():
    W, H = 5.9, 5.3
    fig, ax = canvas(W, H)
    layers = [
        ("Presentation\nlayer", [("React 19 web app\n(Nexus ATS, Vercel)", 1), ("Streamlit app\n(recruiter workspace)", 1), ("Dashboard views: leaderboard,\ndossier, compare, interview kit,\nchatbot", 1.25)]),
        ("Service\nlayer", [("FastAPI REST API (Render)\n/jobs /resumes /screenings\n/audits /auth /candidates", 1.9), ("Accounts\nPBKDF2 + sessions\nGoogle token check", 1.25), ("Service classes\n(job, resume,\nscreening, audit)", 0.85)]),
        ("Intelligence\nengine", [("Resume\nparser", .8), ("Skill\nontology", .8), ("Hybrid\nranker", .8), ("Council\n(4 agents)", .8), ("Talent\nRAG", .8), ("GitHub\ninspector", .8), ("Interview\ngenerator", .8)]),
        ("Data\nlayer", [("SQLite (SQLAlchemy,\nAlembic): screening\nhistory, audit log", 1.35), ("MongoDB Atlas: users,\nsessions, candidate\npools 12 / 50 / 100", 1.5), ("Job roles and\nskill ontology", 1.0)]),
    ]
    ly, lh, gap = H - 0.2, 1.05, 0.2
    lx, lw = 0.15, 1.15
    for i, (name, comps) in enumerate(layers):
        top = ly - i * (lh + gap)
        rect(ax, lx, top - lh, lw, lh, name, fc=NAVY, ec=NAVY, fs=9, bold=True, color="white")
        total = sum(c[1] for c in comps)
        avail = W - (lx + lw + 0.15) - 0.1
        g = 0.08
        unit = (avail - g * (len(comps) - 1)) / total
        x = lx + lw + 0.15
        for t, wgt in comps:
            w = unit * wgt
            box(ax, x, top - lh + 0.15, w, lh - 0.3, t, fs=8, fc=LB)
            x += w + g
        if i < 3:
            arrow(ax, (W / 2 + 0.6, top - lh), (W / 2 + 0.6, top - lh - gap), lw=1.4)
            arrow(ax, (W / 2 + 0.75, top - lh - gap), (W / 2 + 0.75, top - lh), lw=1.4)
    save(fig, "fig_5_2_architecture.png")


# =====================================================================  Fig 5.3 use case
def stick(ax, x, y, label):
    ax.add_patch(Circle((x, y + 0.42), 0.09, fc="white", ec="black", lw=1))
    ax.plot([x, x], [y + 0.33, y + 0.0], color="black", lw=1)
    ax.plot([x - 0.17, x + 0.17], [y + 0.22, y + 0.22], color="black", lw=1)
    ax.plot([x, x - 0.14], [y, y - 0.22], color="black", lw=1)
    ax.plot([x, x + 0.14], [y, y - 0.22], color="black", lw=1)
    ax.text(x, y - 0.34, label, ha="center", va="top", fontsize=8.5, fontweight="bold")


def fig_usecase():
    W, H = 5.9, 5.6
    fig, ax = canvas(W, H)
    ax.add_patch(Rectangle((1.2, 0.15), 3.55, H - 0.3, fc="white", ec="black", lw=1.2))
    ax.text(2.975, H - 0.33, "AI Recruitment System (Nexus ATS)", ha="center", va="center", fontsize=9.5, fontweight="bold")
    cases = ["Sign in / sign up", "Select or create job role", "Upload resumes / load pool", "Run screening engine", "View screening leaderboard",
             "Inspect candidate dossier", "Compare candidates", "Generate interview questions", "Ask recruiter copilot", "Toggle blind screening",
             "View recruiter analytics", "Record shortlist / reject decision"]
    ys = [H - 0.75 - i * 0.405 for i in range(len(cases))]
    pos = []
    for t, y in zip(cases, ys):
        oval(ax, 2.975, y, 2.7, 0.33, t, fs=8)
        pos.append(y)
    stick(ax, 0.55, H / 2 - 0.1, "Recruiter")
    for y in pos:
        ax.plot([0.72, 1.63], [H / 2 + 0.1, y], color="black", lw=0.7)
    # external actors
    stick(ax, 5.35, 3.55, "GitHub\nAPI")
    stick(ax, 5.35, 1.75, "LLM\nprovider")
    ax.plot([5.2, 4.3], [3.7, pos[5]], color=GREYE, lw=0.8, ls="--")
    ax.plot([5.2, 4.3], [1.95, pos[5] - 0.0], color=GREYE, lw=0.8, ls="--")
    ax.plot([5.2, 4.3], [1.95, pos[8]], color=GREYE, lw=0.8, ls="--")
    ax.text(5.35, 0.62, "optional,\nexternal", ha="center", fontsize=7.5, color=GREYE)
    save(fig, "fig_5_3_usecase.png")


# =====================================================================  Fig 5.4 sequence
def fig_sequence():
    W, H = 6.1, 6.0
    fig, ax = canvas(W, H)
    names = ["Recruiter", "Web UI", "Resume\nParser", "Ranker +\nOntology", "Council", "Database"]
    xs = [0.55, 1.5, 2.45, 3.4, 4.4, 5.45]
    top = H - 0.3
    for n, x in zip(names, xs):
        box(ax, x - 0.4, top - 0.3, 0.8, 0.6, n, fs=8, fc=LB)
        ax.plot([x, x], [top - 0.3, 0.15], color=GREYE, lw=0.9, ls=(0, (4, 3)))
    msgs = [
        (0, 1, "1. choose role, upload resumes", "r"),
        (1, 2, "2. parse(file)", "r"),
        (2, 1, "3. structured profile", "r"),
        (1, 3, "4. rank(profiles, JD)", "r"),
        (3, 3, "5. match skills, score\nseven signals", "self"),
        (3, 1, "6. ranked list + breakdown", "r"),
        (1, 4, "7. evaluate(candidate)", "r"),
        (4, 4, "8. agents score, debate,\napply gates", "selfleft"),
        (4, 1, "9. verdict, flags, confidence", "r"),
        (1, 5, "10. save session and results", "r"),
        (1, 0, "11. leaderboard, dossier, explanations", "r"),
        (0, 1, "12. shortlist / reject decision", "r"),
        (1, 5, "13. store decision, audit log", "r"),
    ]
    y = top - 0.68
    for a, b, t, mode in msgs:
        if mode == "self":
            x = xs[a]
            ax.plot([x, x + 0.4, x + 0.4, x], [y, y, y - 0.3, y - 0.3], color=NAVY, lw=1)
            arrow(ax, (x + 0.1, y - 0.3), (x, y - 0.3), lw=1)
            ax.text(x + 0.48, y - 0.15, t, fontsize=7.5, va="center")
            y -= 0.55
        elif mode == "selfleft":
            x = xs[a]
            ax.plot([x, x - 0.4, x - 0.4, x], [y, y, y - 0.3, y - 0.3], color=NAVY, lw=1)
            arrow(ax, (x - 0.1, y - 0.3), (x, y - 0.3), lw=1)
            ax.text(x - 0.48, y - 0.15, t, fontsize=7.5, va="center", ha="right")
            y -= 0.55
        else:
            arrow(ax, (xs[a], y), (xs[b], y), lw=1.1, ls="-" if b > a else (0, (4, 2)))
            lo, hi = sorted((xs[a], xs[b]))
            ax.text((lo + hi) / 2, y + 0.04, t, fontsize=7.3, ha="center", va="bottom",
                    bbox=dict(fc="white", ec="none", pad=0.6))
            y -= 0.37
    save(fig, "fig_5_4_sequence.png")


# =====================================================================  Fig 5.5 ER
def entity(ax, x, y, w, title, fields):
    h = 0.3 + 0.2 * len(fields)
    rect(ax, x, y - h, w, h, fc="white")
    rect(ax, x, y - 0.3, w, 0.3, title, fc=NAVY, ec=NAVY, fs=9, bold=True, color="white")
    for i, (f, kind) in enumerate(fields):
        yy = y - 0.3 - 0.2 * (i + 0.5)
        col = {"PK": REDE, "FK": GREENE}.get(kind, "black")
        ax.text(x + 0.08, yy, f, fontsize=7.6, va="center", color=col, fontweight="bold" if kind in ("PK", "FK") else "normal")
        if kind:
            ax.text(x + w - 0.08, yy, kind, fontsize=7, va="center", ha="right", color=col)
    return h


def fig_er():
    W, H = 6.0, 5.6
    fig, ax = canvas(W, H)
    entity(ax, 0.1, H - 0.1, 1.75, "jobs", [("id", "PK"), ("title", ""), ("department", ""), ("min_experience", ""), ("required_skills (JSON)", ""), ("preferred_skills (JSON)", ""), ("preferred_degrees (JSON)", ""), ("description_text", ""), ("created_at / updated_at", "")])
    entity(ax, 2.1, H - 0.1, 1.85, "screening_sessions", [("id", "PK"), ("job_id", "FK"), ("session_name", ""), ("recruiter_email", ""), ("weights (JSON)", ""), ("created_at", "")])
    entity(ax, 4.15, H - 0.1, 1.75, "resumes", [("id", "PK"), ("file_name", ""), ("file_hash (SHA-256)", ""), ("raw_text", ""), ("parsed_data (JSON)", ""), ("candidate_name", ""), ("email / phone / location", ""), ("created_at / updated_at", "")])
    entity(ax, 2.1, 3.0, 2.2, "screening_results", [("id", "PK"), ("session_id", "FK"), ("resume_id", "FK"), ("candidate_name", ""), ("overall_score", ""), ("rank", ""), ("breakdown (JSON)", ""), ("gap_results (JSON)", ""), ("candidate_data (JSON)", ""), ("decision, decision_timestamp", "")])
    entity(ax, 0.1, 2.6, 1.6, "audit_logs", [("id", "PK"), ("action", ""), ("actor", ""), ("details (JSON)", ""), ("timestamp", "")])
    arrow(ax, (1.85, 4.75), (2.1, 4.75), style="-", lw=1.2)
    ax.text(1.88, 4.82, "1", fontsize=8, ha="left")
    ax.text(2.07, 4.62, "N", fontsize=8, ha="right")
    arrow(ax, (3.0, 3.95), (3.0, 3.0), style="-|>", lw=1.2)
    ax.text(3.08, 4.02, "1", fontsize=8)
    ax.text(3.08, 3.1, "N", fontsize=8)
    ax.text(3.1, 3.55, "contains", fontsize=7.5, style="italic")
    poly_arrow(ax, [(5.0, 3.55), (5.0, 2.55), (4.3, 2.55)], lw=1.2)
    ax.text(5.08, 3.45, "1", fontsize=8)
    ax.text(4.35, 2.6, "N", fontsize=8)
    ax.text(5.08, 3.0, "scored in", fontsize=7.5, style="italic")
    ax.text(3.0, 0.45, "PK = primary key,   FK = foreign key.   JSON columns hold structured parser and scoring output.", fontsize=7.8, color=GREYE, ha="center", va="center")
    save(fig, "fig_5_5_er.png")


# =====================================================================  Fig 5.6 council orchestration
def fig_council():
    W, H = 5.9, 4.5
    fig, ax = canvas(W, H)
    box(ax, 0.2, 3.7, 1.8, 0.55, "Parsed candidate\n+ parsed job", fc=NAVY, ec=NAVY, color="white", bold=True, fs=8.5)
    box(ax, 2.35, 3.7, 3.35, 0.55, "Feature builder: evidence-weighted coverage, timeline,\nimpact terms, architecture / craft / scope terms", fs=8)
    arrow(ax, (2.0, 3.97), (2.35, 3.97))
    ag = [("Round 1\nTech Lead", 0.2), ("Round 1\nCulture and\nRetention", 1.75), ("Round 1\nSeniority and\nCompensation", 3.3)]
    for t, x in ag:
        box(ax, x, 2.55, 1.45, 0.75, t, fs=8)
        arrow(ax, (4.0, 3.7), (x + 0.72, 3.3), lw=0.9)
    box(ax, 4.85, 2.55, 0.9, 0.75, "Round 1b\noptional LLM\nenrichment", fc=GREY, ec=GREYE, fs=7.5)
    box(ax, 0.2, 1.55, 2.55, 0.62, "Round 2: Fair Hiring Auditor\nmerit-only score, bias flags, integrity", fc=GOLD, ec=GOLDE, fs=8)
    box(ax, 3.1, 1.55, 2.6, 0.62, "Round 3: cross-examination debate\n(deterministic transcript)", fs=8)
    for t, x in ag:
        arrow(ax, (x + 0.72, 2.55), (1.5, 2.17), lw=0.8)
    arrow(ax, (2.75, 1.86), (3.1, 1.86))
    box(ax, 0.2, 0.35, 5.5, 0.85, "Final: executive consensus  C = 0.35 Tech + 0.25 Merit + 0.20 Culture + 0.20 Seniority\nthresholds 80 / 68 / 55, knock-out gates, red flags, confidence, dissent, human-review triggers", fc=GREEN, ec=GREENE, fs=8.2)
    arrow(ax, (4.4, 1.55), (4.4, 1.2))
    save(fig, "fig_5_6_council.png")


# =====================================================================  Fig 3.1 hybrid retrieval
def fig_retrieval():
    W, H = 5.9, 3.2
    fig, ax = canvas(W, H)
    box(ax, 0.1, 1.2, 1.15, 0.8, "Recruiter\nquery", fc=NAVY, ec=NAVY, color="white", bold=True, fs=8.5)
    box(ax, 1.55, 1.2, 1.25, 0.8, "Query plan:\nexperience,\ncompetencies,\nsynonyms", fs=8)
    arrow(ax, (1.25, 1.6), (1.55, 1.6))
    box(ax, 3.1, 2.15, 1.35, 0.6, "Dense similarity\n(MiniLM / TF-IDF)", fs=8)
    box(ax, 3.1, 0.45, 1.35, 0.6, "Okapi BM25\n(k1 = 1.5, b = 0.75)", fs=8)
    arrow(ax, (2.8, 1.75), (3.1, 2.45))
    arrow(ax, (2.8, 1.45), (3.1, 0.75))
    box(ax, 4.7, 1.2, 1.1, 0.8, "Fusion\n0.55 dense +\n0.45 BM25", fc=GOLD, ec=GOLDE, fs=8)
    arrow(ax, (4.45, 2.45), (4.95, 2.0))
    arrow(ax, (4.45, 0.75), (4.95, 1.2))
    box(ax, 1.55, 0.05, 4.25, 0.3, "Per-candidate aggregation with competency coverage and experience fit → ranked evidence", fc=GREEN, ec=GREENE, fs=7.5)
    arrow(ax, (5.25, 1.2), (5.25, 0.35))
    save(fig, "fig_3_1_retrieval.png")


# =====================================================================  Fig 3.2 skill matching flow
def fig_skillmatch():
    W, H = 5.9, 4.2
    fig, ax = canvas(W, H)
    box(ax, 2.2, 3.65, 1.5, 0.4, "Required skill r", fc=NAVY, ec=NAVY, color="white", bold=True, fs=8.5)
    box(ax, 1.95, 2.8, 2.0, 0.5, "Normalise: alias table,\npunctuation strip, fuzzy > 0.88", fs=8)
    arrow(ax, (2.95, 3.65), (2.95, 3.3))
    diamond(ax, 2.95, 2.0, 1.9, 0.8, "r in candidate\nskill set?")
    arrow(ax, (2.95, 2.8), (2.95, 2.4))
    box(ax, 4.45, 1.8, 1.35, 0.4, "Matched (1.0)", fc=GREEN, ec=GREENE, fs=8.5)
    arrow(ax, (3.9, 2.0), (4.45, 2.0), label="Yes", loff=(0, 0.03))
    diamond(ax, 2.95, 0.85, 2.2, 0.8, "related pair\nin table?")
    arrow(ax, (2.95, 1.6), (2.95, 1.25), label="No", lpos=0.45, loff=(0.08, 0))
    box(ax, 4.45, 0.65, 1.35, 0.4, "Partial (0.5)", fc=GOLD, ec=GOLDE, fs=8.5)
    arrow(ax, (4.05, 0.85), (4.45, 0.85), label="Yes", loff=(0, 0.03))
    box(ax, 0.1, 0.65, 1.35, 0.4, "Missing (0)", fc=RED, ec=REDE, fs=8.5)
    arrow(ax, (1.85, 0.85), (1.45, 0.85), label="No", loff=(0, 0.03))
    ax.text(0.1, 3.55, "Coverage = (matched + 0.5 × partial) / required", fontsize=8.2, style="italic")
    save(fig, "fig_3_2_skillmatch.png")


# =====================================================================  Fig 6.1 verdict gating
def fig_gating():
    W, H = 5.9, 4.6
    fig, ax = canvas(W, H)
    box(ax, 0.1, 3.9, 1.7, 0.5, "Consensus C", fc=NAVY, ec=NAVY, color="white", bold=True, fs=9)
    diamond(ax, 3.0, 4.15, 2.0, 0.7, "C ≥ 80 ?")
    arrow(ax, (1.8, 4.15), (2.0, 4.15))
    box(ax, 4.5, 3.95, 1.3, 0.4, "STRONG_HIRE", fc=GREEN, ec=GREENE, fs=8.5)
    arrow(ax, (4.0, 4.15), (4.5, 4.15), label="Yes", loff=(0, 0.03))
    diamond(ax, 3.0, 3.2, 2.0, 0.7, "C ≥ 68 ?")
    arrow(ax, (3.0, 3.8), (3.0, 3.55), label="No", lpos=0.4, loff=(0.07, 0))
    box(ax, 4.5, 3.0, 1.3, 0.4, "HIRE", fc=GREEN, ec=GREENE, fs=8.5)
    arrow(ax, (4.0, 3.2), (4.5, 3.2), label="Yes", loff=(0, 0.03))
    diamond(ax, 3.0, 2.25, 2.0, 0.7, "C ≥ 55 ?")
    arrow(ax, (3.0, 2.85), (3.0, 2.6), label="No", lpos=0.4, loff=(0.07, 0))
    box(ax, 4.5, 2.05, 1.3, 0.4, "LEAN_HIRE", fc=GOLD, ec=GOLDE, fs=8.5)
    arrow(ax, (4.0, 2.25), (4.5, 2.25), label="Yes", loff=(0, 0.03))
    box(ax, 0.1, 2.05, 1.3, 0.4, "REJECT", fc=RED, ec=REDE, fs=8.5)
    arrow(ax, (2.0, 2.25), (1.4, 2.25), label="No", loff=(0, 0.03))
    box(ax, 0.1, 0.25, 5.7, 1.35,
        "Knock-out gates applied after the thresholds\n"
        "• evidence-weighted coverage < 0.25  →  REJECT;   < 0.50  →  cap at LEAN_HIRE\n"
        "• two or more high-severity red flags  →  REJECT;   one high-severity flag  →  cap at LEAN_HIRE\n"
        "• inverted dates or missing education  →  cap at LEAN_HIRE",
        fc=GREY, ec=GREYE, fs=8.4, ha="left")
    save(fig, "fig_6_1_gating.png")


# =====================================================================  Fig 5.7 DFD level 1
def fig_dfd():
    W, H = 6.4, 3.9
    fig, ax = canvas(W, H)
    box(ax, 0.05, 1.55, 0.85, 0.8, "Recruiter", fc=GREY, ec=GREYE, style="square,pad=0.0", bold=True, fs=9)
    xs = [1.6, 2.9, 4.2, 5.5]
    names = ["1.0\nParse JD\nand resumes", "2.0\nAnonymise\n(optional)", "3.0\nSkill match\nand rank", "4.0\nCouncil\nreview"]
    cy = 2.0
    for x, t in zip(xs, names):
        oval(ax, x, cy, 0.92, 0.95, t, fc=LB, ec=NAVY, fs=7.4)
    arrow(ax, (0.9, cy), (xs[0] - 0.46, cy), lw=1.2)
    ax.text(1.0, cy - 0.1, "JD,\nresumes", fontsize=6.6, ha="left", va="top")
    for a, b, lab in [(0, 1, "profiles"), (1, 2, "blind\nprofiles"), (2, 3, "ranked\nscores")]:
        arrow(ax, (xs[a] + 0.46, cy), (xs[b] - 0.46, cy), lw=1.2)
        ax.text((xs[a] + xs[b]) / 2, cy + 0.05, lab, fontsize=6.6, ha="center", va="bottom")

    def store(x, y, t):
        ax.plot([x, x + 1.35], [y + 0.3, y + 0.3], color="black", lw=1)
        ax.plot([x, x + 1.35], [y, y], color="black", lw=1)
        ax.text(x + 0.08, y + 0.15, t, fontsize=7.6, va="center")

    store(0.9, 3.4, "D1  Job roles")
    store(3.3, 3.4, "D2  Resume pool")
    store(4.9, 0.3, "D3  Screening history")
    arrow(ax, (1.7, 3.4), (xs[0], cy + 0.47), ls=(0, (3, 2)), lw=0.9)
    arrow(ax, (3.9, 3.4), (xs[2], cy + 0.47), ls=(0, (3, 2)), lw=0.9)
    arrow(ax, (xs[3] + 0.2, cy - 0.45), (xs[3] + 0.2, 0.6), ls=(0, (3, 2)), lw=0.9)
    poly_arrow(ax, [(xs[3] - 0.25, cy - 0.45), (xs[3] - 0.25, 1.05), (0.7, 1.05), (0.7, 1.55)], lw=1.2)
    store(0.05, 0.3, "D4  Accounts, sessions")
    arrow(ax, (0.25, 0.6), (0.25, 1.55), ls=(0, (3, 2)), lw=0.9, style="<|-|>")
    ax.text(0.32, 1.0, "sign-in", fontsize=6.6, ha="left", va="center")
    ax.text(2.9, 1.1, "verdict, red flags, explanations", fontsize=7.4, ha="center", va="bottom")
    save(fig, "fig_5_7_dfd.png")


def main():
    for f in (fig_workflow, fig_architecture, fig_usecase, fig_sequence, fig_er, fig_council, fig_retrieval, fig_skillmatch, fig_gating, fig_dfd):
        f()
    print("figures:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()

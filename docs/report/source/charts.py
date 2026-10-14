"""Data-driven charts (from paper_results.json) and prepared screenshots for the report."""
import json, os, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fig")
SHOTS_SRC = r"C:\Users\Arjun\AppData\Local\Temp\shots\final"
SHOTS_OUT = os.path.join(HERE, "shots")
os.makedirs(SHOTS_OUT, exist_ok=True)
PROJ = r"C:\DEV\Projects\Experiments\ai_recruitment_system"
res = json.load(open(PROJ + r"\paper_results.json"))
rows = res["rows"]

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
NAVY, BLUE, GREY, GOLD, GREEN, RED = "#1F3864", "#4472C4", "#A6A6A6", "#E0A800", "#548235", "#C00000"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=300, facecolor="white")
    plt.close(fig)


SHORT = {"Test_Case_1_Gold_Standard_Pass.txt": "TC1", "Rahul_Nair_ML_Engineer.pdf": "RN", "Test_Case_3_Lateral_Partial_Match.txt": "TC3",
         "Sneha_Kulkarni_Fullstack_Dev.txt": "SK", "Vikram_Singh_Cloud_DevOps.docx": "VS", "Kavita_Mehta_Buzzword_Flawed.txt": "KM",
         "Aarav_Sharma_Backend_Dev.docx": "AS", "Ananya_Roy_Fresher_Engineer.pdf": "AR", "Priya_Patel_Data_Analyst.pdf": "PP",
         "Test_Case_2_Buzzword_Exaggeration_Fail.txt": "TC2", "Test_Case_4_Corrupt_ATS_Format_Error.txt": "TC4", "Edge_Case_Missing_Sections.txt": "EC"}


def ch_weights():
    labels = ["Technical\nskills", "Semantic\nJD fit", "Experience", "Education", "Projects", "Certifi-\ncations", "Resume\nquality"]
    vals = [35, 20, 15, 10, 10, 5, 5]
    fig, ax = plt.subplots(figsize=(5.9, 2.7))
    b = ax.bar(labels, vals, color=BLUE, width=0.62)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.8, f"{v}%", ha="center", fontsize=9)
    ax.set_ylabel("Weight in match score (%)", fontsize=9)
    ax.set_ylim(0, 42)
    ax.tick_params(labelsize=8.5)
    save(fig, "ch_weights.png")


def ch_baseline():
    names = [SHORT[r["file"]] for r in rows]
    base = [r["baseline"] for r in rows]
    prop = [r["proposed"] for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(5.9, 3.0))
    ax.bar(x - 0.2, base, 0.4, color=GREY, label="Keyword baseline (Phase 1)")
    ax.bar(x + 0.2, prop, 0.4, color=BLUE, label="Proposed hybrid score (Phase 2)")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8.5)
    ax.set_ylim(0, 108)
    ax.set_ylabel("Score (%)", fontsize=9)
    ax.set_xlabel("Resume (in proposed rank order)", fontsize=9)
    ax.legend(fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.13), frameon=False)
    ax.yaxis.grid(True, color="#DDDDDD", lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "ch_baseline.png")


def ch_latency():
    lat = res["latency_ms_per_resume"]
    labs = ["Resume\nparsing", "Hybrid scoring\nand ranking", "Multi-agent\nconsensus", "End-to-end"]
    vals = [lat["parse"], lat["rank"], lat["council"], lat["total"]]
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    b = ax.bar(labs, vals, color=[BLUE, BLUE, BLUE, NAVY], width=0.58)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.6, f"{v:.2f} ms", ha="center", fontsize=9)
    ax.set_ylabel("Latency per resume (ms)", fontsize=9)
    ax.set_ylim(0, 35)
    ax.tick_params(labelsize=8.5)
    save(fig, "ch_latency.png")


def ch_components():
    keys = [("technical_skills", "Skills"), ("semantic_jd", "Semantic"), ("experience", "Experience"), ("education", "Education"), ("projects", "Projects"), ("certifications", "Certs"), ("resume_quality", "ATS quality")]
    pick = ["Test_Case_1_Gold_Standard_Pass.txt", "Test_Case_3_Lateral_Partial_Match.txt", "Test_Case_2_Buzzword_Exaggeration_Fail.txt", "Test_Case_4_Corrupt_ATS_Format_Error.txt"]
    names = ["TC1 Gold standard", "TC3 Lateral match", "TC2 Buzzword", "TC4 Corrupt format"]
    colors = [GREEN, GOLD, RED, GREY]
    byf = {r["file"]: r for r in rows}
    fig, ax = plt.subplots(figsize=(5.9, 3.0))
    x = np.arange(len(keys))
    w = 0.2
    for i, (f, n, c) in enumerate(zip(pick, names, colors)):
        vals = [byf[f]["breakdown"][k] for k, _ in keys]
        ax.bar(x + (i - 1.5) * w, vals, w, color=c, label=n)
    ax.set_xticks(x)
    ax.set_xticklabels([l for _, l in keys], fontsize=8.5)
    ax.set_ylabel("Component score (0\u2013100)", fontsize=9)
    ax.set_ylim(0, 118)
    ax.legend(fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12), frameon=False)
    ax.yaxis.grid(True, color="#DDDDDD", lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "ch_components.png")


def ch_agents():
    pick = ["Test_Case_1_Gold_Standard_Pass.txt", "Test_Case_3_Lateral_Partial_Match.txt", "Test_Case_2_Buzzword_Exaggeration_Fail.txt", "Test_Case_4_Corrupt_ATS_Format_Error.txt"]
    names = ["TC1", "TC3", "TC2", "TC4"]
    byf = {r["file"]: r for r in rows}
    ag = [("tech_lead", "Tech Lead", NAVY), ("culture_retention", "Culture and Retention", BLUE), ("fair_auditor", "Fair Auditor (merit)", GOLD), ("seniority_comp", "Seniority and Comp.", GREEN)]
    fig, ax = plt.subplots(figsize=(5.9, 2.9))
    x = np.arange(len(pick))
    w = 0.2
    for i, (k, lab, c) in enumerate(ag):
        ax.bar(x + (i - 1.5) * w, [byf[f]["agents"][k] for f in pick], w, color=c, label=lab)
    ax.plot(x, [byf[f]["council"] for f in pick], "k_", ms=26, mew=2, label="Consensus C")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylim(0, 118)
    ax.set_ylabel("Agent score (0\u2013100)", fontsize=9)
    ax.legend(fontsize=7.6, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.2), frameon=False)
    ax.yaxis.grid(True, color="#DDDDDD", lw=0.6)
    ax.set_axisbelow(True)
    save(fig, "ch_agents.png")


def ch_bench():
    roles = ["Senior ML engineer", "Cloud DevOps / SRE", "Full-stack AI", "Data platform", "Backend architect", "AI safety", "BI and analytics", "Python / FastAPI"]
    lean = [11, 11, 12, 13, 11, 4, 6, 11]
    rej = [2, 2, 1, 0, 1, 8, 6, 1]
    y = np.arange(len(roles))
    fig, ax = plt.subplots(figsize=(5.9, 3.0))
    ax.barh(y, lean, color=GOLD, label="HIRE / LEAN_HIRE")
    ax.barh(y, rej, left=lean, color=RED, label="REJECT")
    ax.set_yticks(y)
    ax.set_yticklabels(roles, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Number of resumes (verdicts; no STRONG_HIRE was issued)", fontsize=9)
    ax.legend(fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.1), frameon=False)
    for i, (a, b) in enumerate(zip(lean, rej)):
        ax.text(a / 2, i, str(a), ha="center", va="center", fontsize=8)
        if b:
            ax.text(a + b / 2, i, str(b), ha="center", va="center", fontsize=8, color="white")
    save(fig, "ch_bench.png")


def ch_ablation():
    abl = res["ablation"]["no_evidence_weighting"]["scores_changed"]
    byf = {r["file"]: r for r in rows}
    items = sorted(abl.items(), key=lambda kv: -kv[1][0])
    names = [SHORT[k] for k, _ in items]
    full = [v[0] for _, v in items]
    noev = [v[1] for _, v in items]
    x = np.arange(len(items))
    fig, ax = plt.subplots(figsize=(5.9, 2.9))
    ax.bar(x - 0.2, full, 0.4, color=BLUE, label="Full council")
    ax.bar(x + 0.2, noev, 0.4, color=GREY, label="Evidence weighting disabled")
    ax.axhline(55, color=RED, lw=1, ls="--")
    ax.text(len(items) - 0.6, 56.2, "LEAN_HIRE threshold (55)", fontsize=8, color=RED, ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8.5)
    ax.set_ylim(0, 108)
    ax.set_ylabel("Council consensus C", fontsize=9)
    ax.legend(fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.13), frameon=False)
    save(fig, "ch_ablation.png")


def prep_shots():
    for fn in sorted(os.listdir(SHOTS_SRC)):
        if not fn.endswith(".png"):
            continue
        im = Image.open(os.path.join(SHOTS_SRC, fn)).convert("RGB")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        diff = ImageChops.difference(im, bg).convert("L").point(lambda p: 255 if p > 12 else 0)
        bbox = diff.getbbox()
        if bbox:
            bottom = min(im.height, bbox[3] + 30)
            im = im.crop((0, 0, im.width, bottom))
        if im.width > 1800:
            im = im.resize((1800, int(im.height * 1800 / im.width)), Image.LANCZOS)
        im.save(os.path.join(SHOTS_OUT, fn.replace(".png", ".jpg")), quality=90)
    print("shots", sorted(os.listdir(SHOTS_OUT)))


if __name__ == "__main__":
    for f in (ch_weights, ch_baseline, ch_latency, ch_components, ch_agents, ch_bench, ch_ablation, prep_shots):
        f()
    print("charts done")

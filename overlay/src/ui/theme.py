"""
Obsidian Telemetry Theme
========================

Design system for the Talent Intelligence console. Inspired by Linear (dense, quiet, hairline borders), Vercel
(black canvas, mono data chips) and Stripe Radar (risk telemetry, score rings).

* Canvas  : obsidian ``#090d16`` with soft radial glows, panels in ``#0f172a`` glass
* Accents : Electric Cyan ``#38bdf8``, Emerald ``#10b981``, Amber ``#f59e0b``, Rose ``#f43f5e``
* Type    : Plus Jakarta Sans for UI, JetBrains Mono for data chips (Google Fonts, system fallbacks offline)

Usage::

    from src.ui.theme import inject_obsidian_theme, score_bar, verdict_tag, ring, chip
    inject_obsidian_theme()                       # once per script run, after any legacy CSS
    st.markdown(score_bar(87.5), unsafe_allow_html=True)

All helpers return *single-line* HTML strings (no blank lines, no indentation) so Markdown never mistakes them for
code blocks. Every dynamic value is HTML-escaped.
"""

from __future__ import annotations

import html
import re
from typing import Iterable, List, Optional

import streamlit as st

# Palette ------------------------------------------------------------------------------------------------------
OBSIDIAN = "#090d16"
SLATE = "#0f172a"
CYAN = "#38bdf8"
EMERALD = "#10b981"
AMBER = "#f59e0b"
ROSE = "#f43f5e"
MUTED = "#8b9bb4"

VERDICT_COLORS = {"STRONG_HIRE": EMERALD, "HIRE": CYAN, "LEAN_HIRE": AMBER, "REJECT": ROSE}
VERDICT_LABELS = {"STRONG_HIRE": "STRONG HIRE", "HIRE": "HIRE", "LEAN_HIRE": "LEAN HIRE", "REJECT": "REJECT"}
SEVERITY_COLORS = {"high": ROSE, "medium": AMBER, "low": CYAN}

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{
  --ob-bg:#090d16; --ob-slate:#0f172a; --ob-line:rgba(148,163,184,.14); --ob-line-strong:rgba(148,163,184,.26);
  --ob-text:#e6edf7; --ob-muted:#8b9bb4; --ob-dim:#5b6b85;
  --ob-cyan:#38bdf8; --ob-emerald:#10b981; --ob-amber:#f59e0b; --ob-rose:#f43f5e;
  --ob-glass:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.015));
}

/* ---------- Canvas ---------- */
.stApp{
  background:
    radial-gradient(900px 520px at 8% -8%, rgba(56,189,248,.13), transparent 60%),
    radial-gradient(760px 480px at 100% 4%, rgba(16,185,129,.09), transparent 62%),
    radial-gradient(700px 520px at 50% 118%, rgba(244,63,94,.07), transparent 60%),
    #090d16 !important;
  color:var(--ob-text);
}
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select{
  font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;
}
code, pre, .ob-mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace !important;}
header[data-testid="stHeader"]{background:transparent !important;}
.block-container{padding-top:1.4rem !important;max-width:1280px;}
h1,h2,h3,h4{letter-spacing:-.02em;color:var(--ob-text);}
hr{border-color:var(--ob-line) !important;}
::-webkit-scrollbar{width:10px;height:10px} ::-webkit-scrollbar-thumb{background:#1e293b;border-radius:8px}
::selection{background:rgba(56,189,248,.35)}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,rgba(15,23,42,.92),rgba(9,13,22,.96)) !important;
  border-right:1px solid var(--ob-line);
}

/* ---------- Tabs (Linear-style segmented) ---------- */
div[data-baseweb="tab-list"]{gap:2px;background:rgba(15,23,42,.65);border:1px solid var(--ob-line);
  border-radius:12px;padding:4px;backdrop-filter:blur(10px);flex-wrap:wrap;}
button[data-baseweb="tab"]{height:36px;border-radius:9px;padding:0 14px;color:var(--ob-muted);font-weight:600;font-size:.84rem;
  background:transparent;transition:all .18s ease;}
button[data-baseweb="tab"]:hover{color:var(--ob-text);background:rgba(148,163,184,.08);}
button[data-baseweb="tab"][aria-selected="true"]{color:#04121f;background:linear-gradient(180deg,#7dd3fc,#38bdf8);
  box-shadow:0 0 0 1px rgba(56,189,248,.5),0 6px 22px rgba(56,189,248,.28);}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"]{display:none !important;}

/* ---------- Buttons ---------- */
.stButton>button, .stDownloadButton>button{
  background:var(--ob-glass);border:1px solid var(--ob-line-strong);color:var(--ob-text);border-radius:10px;
  font-weight:600;font-size:.84rem;transition:all .16s ease;box-shadow:inset 0 1px 0 rgba(255,255,255,.05);}
.stButton>button:hover, .stDownloadButton>button:hover{border-color:rgba(56,189,248,.65);color:#fff;
  box-shadow:0 0 0 1px rgba(56,189,248,.3),0 8px 24px rgba(56,189,248,.14);transform:translateY(-1px);}
.stButton>button[kind="primary"]{background:linear-gradient(180deg,#38bdf8,#0ea5e9);color:#03121f;border:0;
  box-shadow:0 8px 26px rgba(56,189,248,.32);}
.stButton>button[kind="primary"]:hover{filter:brightness(1.08);}

/* ---------- Inputs ---------- */
.stTextInput input, .stTextArea textarea, div[data-baseweb="select"]>div, .stNumberInput input{
  background:rgba(15,23,42,.72) !important;border:1px solid var(--ob-line-strong) !important;color:var(--ob-text) !important;
  border-radius:10px !important;}
.stTextInput input:focus, .stTextArea textarea:focus{border-color:var(--ob-cyan) !important;box-shadow:0 0 0 3px rgba(56,189,248,.18) !important;}
.stTextInput input::placeholder{color:var(--ob-dim) !important;}
label, .stMarkdown p{color:inherit;}

/* ---------- Expanders / dataframes / alerts ---------- */
div[data-testid="stExpander"]{background:var(--ob-glass);border:1px solid var(--ob-line) !important;border-radius:12px;}
div[data-testid="stExpander"] summary{font-weight:600;}
div[data-testid="stDataFrame"]{border:1px solid var(--ob-line);border-radius:12px;overflow:hidden;}
div[data-testid="stAlert"]{background:rgba(15,23,42,.7);border:1px solid var(--ob-line-strong);border-radius:12px;}

/* ---------- Floating search ---------- */
.ob-search-wrap{position:relative;margin:6px 0 4px 0;}
.ob-search-wrap + div .stTextInput input, .ob-float-search .stTextInput input{
  height:54px;font-size:1rem;padding-left:18px;border-radius:16px !important;
  background:linear-gradient(180deg,rgba(30,41,59,.72),rgba(15,23,42,.8)) !important;
  border:1px solid rgba(56,189,248,.35) !important;
  box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 0 6px rgba(56,189,248,.05),0 0 40px rgba(56,189,248,.10);
  backdrop-filter:blur(18px);}

.st-key-cc_query input, .st-key-copilot_form input{
  height:54px;font-size:1rem;border-radius:16px !important;border:1px solid rgba(56,189,248,.35) !important;
  background:linear-gradient(180deg,rgba(30,41,59,.72),rgba(15,23,42,.8)) !important;
  box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 0 6px rgba(56,189,248,.05),0 0 40px rgba(56,189,248,.10);}
section[data-testid="stSidebar"] *{color:#cbd5e1;}
section[data-testid="stSidebar"] a{opacity:.85}
div[data-testid="stChatMessage"]{background:rgba(15,23,42,.55);border:1px solid var(--ob-line);border-radius:14px;}
div[data-testid="stForm"]{border:0 !important;padding:0 !important;background:transparent !important;}
.ob-pill{max-width:100%;overflow:hidden;text-overflow:ellipsis;}

/* ---------- Cards & primitives ---------- */
.ob-card{background:var(--ob-glass);border:1px solid var(--ob-line);border-radius:16px;padding:16px 18px;
  backdrop-filter:blur(14px);box-shadow:0 14px 40px rgba(0,0,0,.28);position:relative;overflow:hidden;
  transition:border-color .2s ease,transform .2s ease,box-shadow .2s ease;}
.ob-card:hover{border-color:var(--ob-line-strong);}
.ob-card.accent::before{content:"";position:absolute;left:0;top:0;right:0;height:2px;background:var(--acc,var(--ob-cyan));
  box-shadow:0 0 18px var(--acc,var(--ob-cyan));}
.ob-card.rank1{border-color:rgba(16,185,129,.4);box-shadow:0 14px 40px rgba(0,0,0,.28),0 0 40px rgba(16,185,129,.08);}
.ob-eyebrow{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ob-dim);font-weight:700;}
.ob-title{font-size:1.02rem;font-weight:700;color:var(--ob-text);letter-spacing:-.01em;}
.ob-sub{font-size:.8rem;color:var(--ob-muted);}
.ob-num{font-family:'JetBrains Mono',monospace;font-weight:600;letter-spacing:-.03em;}
.ob-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ob-between{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
.ob-grid{display:grid;gap:12px;}
.ob-spacer{height:10px}

/* ---------- Telemetry strip ---------- */
.ob-topbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:14px;}
.ob-brand{display:flex;align-items:center;gap:12px;}
.ob-logo{width:34px;height:34px;border-radius:10px;background:conic-gradient(from 210deg,#38bdf8,#10b981,#f59e0b,#38bdf8);
  display:grid;place-items:center;box-shadow:0 0 28px rgba(56,189,248,.45);}
.ob-logo::after{content:"";width:14px;height:14px;border-radius:50%;background:#090d16;display:block;}
.ob-brand h1{font-size:1.25rem;margin:0;font-weight:800;}
.ob-brand small{display:block;color:var(--ob-muted);font-size:.74rem;font-weight:500;margin-top:1px;}
.ob-pill{display:inline-flex;align-items:center;gap:8px;height:30px;padding:0 12px;border-radius:999px;
  border:1px solid var(--ob-line-strong);background:rgba(15,23,42,.7);font-size:.74rem;font-weight:600;color:var(--ob-text);
  font-family:'JetBrains Mono',monospace;letter-spacing:.01em;white-space:nowrap;}
.ob-dot{width:8px;height:8px;border-radius:50%;background:var(--c,var(--ob-emerald));position:relative;flex:none;}
.ob-dot.pulse::after{content:"";position:absolute;inset:-5px;border-radius:50%;border:2px solid var(--c,var(--ob-emerald));
  animation:ob-ping 1.8s cubic-bezier(0,0,.2,1) infinite;}
@keyframes ob-ping{0%{transform:scale(.6);opacity:.9}80%,100%{transform:scale(1.9);opacity:0}}

.ob-role{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:14px 18px;border-radius:16px;
  border:1px solid rgba(56,189,248,.22);
  background:linear-gradient(100deg,rgba(56,189,248,.12),rgba(16,185,129,.05) 55%,rgba(15,23,42,.2));margin-bottom:12px;}
.ob-role .t{font-size:1.15rem;font-weight:800;letter-spacing:-.02em;}

.ob-tele{padding:14px 16px;}
.ob-tele .v{font-size:2rem;line-height:1.05;margin:6px 0 2px 0;font-family:'JetBrains Mono',monospace;font-weight:600;letter-spacing:-.04em;
  color:var(--acc,var(--ob-text));text-shadow:0 0 26px color-mix(in srgb,var(--acc,#38bdf8) 40%,transparent);}

/* ---------- Chips ---------- */
.ob-chip{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 9px;border-radius:7px;margin:2px 4px 2px 0;
  font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:500;color:var(--c,var(--ob-muted));
  background:color-mix(in srgb,var(--c,#8b9bb4) 11%,transparent);border:1px solid color-mix(in srgb,var(--c,#8b9bb4) 32%,transparent);white-space:nowrap;}
.ob-chip.solid{color:#04121f;background:var(--c);border-color:transparent;font-weight:700;}
.ob-verdict{display:inline-flex;align-items:center;gap:8px;height:28px;padding:0 12px;border-radius:8px;font-family:'JetBrains Mono',monospace;
  font-size:.74rem;font-weight:700;letter-spacing:.06em;color:var(--c);background:color-mix(in srgb,var(--c) 13%,transparent);
  border:1px solid color-mix(in srgb,var(--c) 45%,transparent);box-shadow:0 0 22px color-mix(in srgb,var(--c) 18%,transparent);}

/* ---------- Animated score bars ---------- */
.ob-bar{height:7px;border-radius:99px;background:rgba(148,163,184,.14);overflow:hidden;position:relative;}
.ob-bar>span{display:block;height:100%;border-radius:99px;width:var(--w);
  background:linear-gradient(90deg,color-mix(in srgb,var(--c) 55%,#0b1220),var(--c));box-shadow:0 0 14px color-mix(in srgb,var(--c) 70%,transparent);
  animation:ob-grow 1.15s cubic-bezier(.2,.8,.2,1) both;}
.ob-bar.thin{height:5px}
@keyframes ob-grow{from{width:0}}
.ob-ring text{font-family:'JetBrains Mono',monospace;}
.ob-ring .arc{animation:ob-ring 1.3s cubic-bezier(.2,.8,.2,1) both;filter:drop-shadow(0 0 6px var(--c));}
@keyframes ob-ring{from{stroke-dashoffset:var(--full)}}

/* ---------- Leaderboard cards ---------- */
.ob-rank{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;font-family:'JetBrains Mono',monospace;font-weight:700;
  font-size:.92rem;color:var(--ob-muted);border:1px solid var(--ob-line-strong);background:rgba(15,23,42,.7);flex:none;}
.ob-rank.r1{color:#04121f;background:linear-gradient(180deg,#34d399,#10b981);border:0;box-shadow:0 0 24px rgba(16,185,129,.5);}
.ob-snippet{margin-top:8px;padding:9px 12px;border-left:2px solid var(--ob-cyan);background:rgba(56,189,248,.05);border-radius:0 8px 8px 0;
  font-size:.8rem;color:#c3cfe2;line-height:1.5;}
.ob-snippet mark{background:rgba(56,189,248,.22);color:#e0f2fe;border-radius:4px;padding:0 3px;}

/* ---------- Agents / debate ---------- */
.ob-agent h4{margin:2px 0 0 0;font-size:.95rem;font-weight:700;}
.ob-agent ul{margin:8px 0 0 0;padding-left:16px;color:#b6c3d9;font-size:.78rem;line-height:1.5;}
.ob-agent li{margin-bottom:3px}
.ob-bubble{display:flex;gap:12px;margin:10px 0;animation:ob-rise .5s cubic-bezier(.2,.8,.2,1) both;animation-delay:var(--d,0s);}
.ob-avatar{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;flex:none;font-family:'JetBrains Mono',monospace;
  font-size:.72rem;font-weight:700;color:var(--c);background:color-mix(in srgb,var(--c) 13%,transparent);border:1px solid color-mix(in srgb,var(--c) 40%,transparent);}
.ob-bubble .body{background:var(--ob-glass);border:1px solid var(--ob-line);border-radius:4px 14px 14px 14px;padding:9px 13px;font-size:.84rem;color:#d3deef;line-height:1.5;max-width:100%;}
.ob-bubble .who{font-size:.7rem;color:var(--c);font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:2px;font-family:'JetBrains Mono',monospace;}
.ob-bubble.user{flex-direction:row-reverse}
.ob-bubble.user .body{border-radius:14px 4px 14px 14px;background:linear-gradient(180deg,rgba(56,189,248,.16),rgba(56,189,248,.07));border-color:rgba(56,189,248,.3);}
@keyframes ob-rise{from{opacity:0;transform:translateY(8px)}}

/* ---------- Risk meter ---------- */
.ob-meter{position:relative;height:10px;border-radius:99px;display:flex;gap:3px;margin:14px 0 6px 0;}
.ob-meter i{flex:1;border-radius:99px;opacity:.28}
.ob-meter i.on{opacity:1;box-shadow:0 0 14px currentColor}
.ob-meter .needle{position:absolute;top:-7px;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:8px solid #e6edf7;
  transform:translateX(-50%);transition:left .6s ease;filter:drop-shadow(0 2px 4px rgba(0,0,0,.5));}

/* ---------- Comp band ---------- */
.ob-band{position:relative;height:10px;border-radius:99px;background:rgba(148,163,184,.14);margin:12px 0 4px 0;}
.ob-band .fill{position:absolute;inset:0;border-radius:99px;background:linear-gradient(90deg,rgba(245,158,11,.25),rgba(245,158,11,.85));}
.ob-band .mk{position:absolute;top:-4px;width:4px;height:18px;border-radius:3px;background:#fff;box-shadow:0 0 12px rgba(255,255,255,.8);transform:translateX(-50%);}

/* ---------- Flags ---------- */
.ob-flag{display:flex;gap:10px;align-items:flex-start;padding:9px 12px;border-radius:10px;margin:6px 0;font-size:.82rem;color:#d3deef;
  background:color-mix(in srgb,var(--c) 8%,transparent);border:1px solid color-mix(in srgb,var(--c) 30%,transparent);}
.ob-flag b{color:var(--c);font-family:'JetBrains Mono',monospace;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;display:block;margin-bottom:1px}

/* ---------- Legacy component compatibility (old tabs keep working on the new canvas) ---------- */
.metric-card, .copilot-header-card{background:var(--ob-glass) !important;border:1px solid var(--ob-line) !important;border-radius:16px !important;}
.metric-value{background:linear-gradient(135deg,#7dd3fc,#34d399) !important;-webkit-background-clip:text !important;}

@media (max-width: 760px){ .ob-tele .v{font-size:1.5rem} }
@media (prefers-reduced-motion: reduce){ .ob-bar>span,.ob-ring .arc,.ob-bubble,.ob-dot.pulse::after{animation:none !important} }
"""


def inject_obsidian_theme() -> None:
    """Injects the Obsidian Telemetry stylesheet. Safe to call on every rerun."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------------------------------------------
# HTML helpers (all return single-line strings)
# --------------------------------------------------------------------------------------------------------------
def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _one_line(markup: str) -> str:
    return re.sub(r"\n\s*", "", markup).strip()


def score_color(score: float) -> str:
    if score >= 80:
        return EMERALD
    if score >= 65:
        return CYAN
    if score >= 50:
        return AMBER
    return ROSE


def chip(text: object, color: str = MUTED, solid: bool = False) -> str:
    return f'<span class="ob-chip{" solid" if solid else ""}" style="--c:{color}">{esc(text)}</span>'


def chips(items: Iterable[object], color: str = MUTED, limit: Optional[int] = None) -> str:
    items = list(items)
    shown = items[:limit] if limit else items
    out = "".join(chip(i, color) for i in shown)
    if limit and len(items) > limit:
        out += chip(f"+{len(items) - limit}", MUTED)
    return out


def pill(text: object, color: str = EMERALD, pulse: bool = False) -> str:
    return (f'<span class="ob-pill"><span class="ob-dot{" pulse" if pulse else ""}" style="--c:{color}"></span>{esc(text)}</span>')


def verdict_tag(verdict: str) -> str:
    color = VERDICT_COLORS.get(verdict, MUTED)
    return f'<span class="ob-verdict" style="--c:{color}"><span class="ob-dot" style="--c:{color}"></span>{esc(VERDICT_LABELS.get(verdict, verdict))}</span>'


def score_bar(value: float, color: Optional[str] = None, thin: bool = False) -> str:
    value = max(0.0, min(100.0, float(value or 0)))
    color = color or score_color(value)
    return f'<div class="ob-bar{" thin" if thin else ""}"><span style="--w:{value:.1f}%;--c:{color}"></span></div>'


def labeled_bar(label: str, value: float, color: Optional[str] = None, suffix: str = "%") -> str:
    color = color or score_color(value)
    return _one_line(f"""
    <div style="margin:7px 0">
      <div class="ob-between" style="margin-bottom:5px"><span class="ob-sub">{esc(label)}</span>
      <span class="ob-num" style="color:{color};font-size:.82rem">{value:.0f}{suffix}</span></div>{score_bar(value, color, thin=True)}
    </div>""")


def ring(value: Optional[float], label: str = "", color: Optional[str] = None, size: int = 132, unit: str = "") -> str:
    """Animated score ring (SVG). ``value=None`` renders an empty 'N/A' ring."""
    radius = 44.0
    circumference = 2 * 3.14159265 * radius
    if value is None:
        color, shown, frac = "#475569", "N/A", 0.0
    else:
        value = max(0.0, min(100.0, float(value)))
        color = color or score_color(value)
        shown, frac = f"{value:.0f}", value / 100.0
    offset = circumference * (1 - frac)
    return _one_line(f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:4px">
    <svg class="ob-ring" width="{size}" height="{size}" viewBox="0 0 100 100" role="img" aria-label="{esc(label)} {shown}">
      <circle cx="50" cy="50" r="{radius}" fill="none" stroke="rgba(148,163,184,.16)" stroke-width="8"/>
      <circle class="arc" cx="50" cy="50" r="{radius}" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"
        stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}" transform="rotate(-90 50 50)"
        style="--c:{color};--full:{circumference:.2f}"/>
      <text x="50" y="{'55' if unit else '57'}" text-anchor="middle" fill="#e6edf7" font-size="{'22' if value is not None else '17'}" font-weight="600">{shown}</text>
      {f'<text x="50" y="68" text-anchor="middle" fill="#8b9bb4" font-size="8">{esc(unit)}</text>' if unit else ''}
    </svg>
    <span class="ob-eyebrow">{esc(label)}</span></div>""")


def risk_meter(level: str) -> str:
    """Three-segment exaggeration-risk gauge: LOW / MODERATE / HIGH (UNKNOWN renders neutral)."""
    level = (level or "UNKNOWN").upper()
    colors = [EMERALD, AMBER, ROSE]
    names = ["LOW", "MODERATE", "HIGH"]
    pos = {"LOW": 16.6, "MODERATE": 50.0, "HIGH": 83.4}.get(level)
    segs = "".join(
        f'<i class="{"on" if (level == n) else ""}" style="background:{c};color:{c}"></i>' for n, c in zip(names, colors)
    ) if pos is not None else "".join('<i style="background:#475569"></i>' for _ in names)
    needle = f'<div class="needle" style="left:{pos}%"></div>' if pos is not None else ""
    col = {"LOW": EMERALD, "MODERATE": AMBER, "HIGH": ROSE}.get(level, MUTED)
    return _one_line(f"""
    <div><div class="ob-between"><span class="ob-eyebrow">Exaggeration risk</span>
    <span class="ob-chip solid" style="--c:{col}">{esc(level)}</span></div>
    <div class="ob-meter">{segs}{needle}</div>
    <div class="ob-between ob-sub" style="font-size:.66rem"><span>low</span><span>moderate</span><span>high</span></div></div>""")


def telemetry_card(label: str, value: object, sub: str = "", accent: str = CYAN) -> str:
    return _one_line(f"""
    <div class="ob-card accent ob-tele" style="--acc:{accent}">
      <div class="ob-eyebrow">{esc(label)}</div><div class="v">{esc(value)}</div><div class="ob-sub">{esc(sub)}</div></div>""")


def flag(title: str, detail: str, severity: str = "medium") -> str:
    color = SEVERITY_COLORS.get(severity, AMBER)
    return f'<div class="ob-flag" style="--c:{color}"><div><b>{esc(severity)} · {esc(title)}</b>{esc(detail)}</div></div>'


def bubble(who: str, text: str, color: str = CYAN, delay: float = 0.0, user: bool = False, initials: Optional[str] = None) -> str:
    initials = initials or "".join(w[0] for w in who.replace("Agent", " ").split()[:2]).upper() or "AI"
    return _one_line(f"""
    <div class="ob-bubble{' user' if user else ''}" style="--c:{color};--d:{delay:.2f}s">
      <div class="ob-avatar">{esc(initials[:2])}</div>
      <div class="body"><div class="who">{esc(who)}</div>{esc(text)}</div></div>""")


def card(inner_html: str, accent: Optional[str] = None, extra_class: str = "") -> str:
    style = f' style="--acc:{accent}"' if accent else ""
    cls = "ob-card" + (" accent" if accent else "") + (f" {extra_class}" if extra_class else "")
    return f'<div class="{cls}"{style}>{_one_line(inner_html)}</div>'


def md(markup: str) -> None:
    """Render trusted HTML built from this module's helpers."""
    st.markdown(_one_line(markup), unsafe_allow_html=True)


def spacer(px: int = 10) -> None:
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)

"""
Design system
=============

A quiet, light interface: neutral canvas, white surfaces, hairline borders and a single indigo accent.
Status colours (green / amber / red) are reserved for scores and verdicts only. Stylesheet: ``theme.css``.

* Canvas  : ``#f8fafc``; surfaces ``#ffffff``; borders ``#e2e8f0``
* Text    : ``#0f172a`` (primary), ``#334155`` (secondary), ``#64748b`` (muted)
* Accent  : indigo ``#4f46e5`` (primary actions, links, selected state)
* Type    : Inter for UI, JetBrains Mono for numeric data (Google Fonts, system fallbacks offline)

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
from pathlib import Path
from typing import Iterable, List, Optional

import streamlit as st

# Palette ------------------------------------------------------------------------------------------------------
# Constant names are kept from the previous theme so existing views keep importing them.
OBSIDIAN = "#f8fafc"   # canvas
SLATE = "#ffffff"      # surface
ACCENT = "#4f46e5"
CYAN = ACCENT          # legacy alias: "primary / informational"
EMERALD = "#059669"
AMBER = "#d97706"
ROSE = "#dc2626"
MUTED = "#64748b"

VERDICT_COLORS = {"STRONG_HIRE": EMERALD, "HIRE": ACCENT, "LEAN_HIRE": AMBER, "REJECT": ROSE}
VERDICT_LABELS = {"STRONG_HIRE": "STRONG HIRE", "HIRE": "HIRE", "LEAN_HIRE": "LEAN HIRE", "REJECT": "REJECT"}
SEVERITY_COLORS = {"high": ROSE, "medium": AMBER, "low": MUTED}

_CSS_PATH = Path(__file__).with_name("theme.css")


def inject_obsidian_theme() -> None:
    """Injects the design-system stylesheet. Safe to call on every rerun."""
    st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


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
        color, shown, frac = "#cbd5e1", "N/A", 0.0
    else:
        value = max(0.0, min(100.0, float(value)))
        color = color or score_color(value)
        shown, frac = f"{value:.0f}", value / 100.0
    offset = circumference * (1 - frac)
    return _one_line(f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:4px">
    <svg class="ob-ring" width="{size}" height="{size}" viewBox="0 0 100 100" role="img" aria-label="{esc(label)} {shown}">
      <circle cx="50" cy="50" r="{radius}" fill="none" stroke="#e2e8f0" stroke-width="8"/>
      <circle class="arc" cx="50" cy="50" r="{radius}" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"
        stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}" transform="rotate(-90 50 50)"
        style="--c:{color};--full:{circumference:.2f}"/>
      <text x="50" y="{'55' if unit else '57'}" text-anchor="middle" fill="#0f172a" font-size="{'22' if value is not None else '17'}" font-weight="600">{shown}</text>
      {f'<text x="50" y="68" text-anchor="middle" fill="#64748b" font-size="8">{esc(unit)}</text>' if unit else ''}
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
    ) if pos is not None else "".join('<i style="background:#cbd5e1"></i>' for _ in names)
    needle = f'<div class="needle" style="left:{pos}%"></div>' if pos is not None else ""
    col = {"LOW": EMERALD, "MODERATE": AMBER, "HIGH": ROSE}.get(level, MUTED)
    return _one_line(f"""
    <div><div class="ob-between"><span class="ob-eyebrow">Exaggeration risk</span>
    <span class="ob-chip solid" style="--c:{col}">{esc(level)}</span></div>
    <div class="ob-meter">{segs}{needle}</div>
    <div class="ob-between ob-sub" style="font-size:.66rem"><span>low</span><span>moderate</span><span>high</span></div></div>""")


def telemetry_card(label: str, value: object, sub: str = "", accent: str = ACCENT) -> str:
    return _one_line(f"""
    <div class="ob-card ob-tele">
      <div class="ob-eyebrow">{esc(label)}</div><div class="v">{esc(value)}</div><div class="ob-sub">{esc(sub)}</div></div>""")


def flag(title: str, detail: str, severity: str = "medium") -> str:
    color = SEVERITY_COLORS.get(severity, AMBER)
    return f'<div class="ob-flag" style="--c:{color}"><div><b>{esc(severity)} · {esc(title)}</b>{esc(detail)}</div></div>'


def bubble(who: str, text: str, color: str = ACCENT, delay: float = 0.0, user: bool = False, initials: Optional[str] = None) -> str:
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

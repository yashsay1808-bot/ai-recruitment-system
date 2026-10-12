"""
Reusable UI Components and Plotly Visualizations: metric cards, skill badges, radar and bar charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any


def inject_custom_css():
    """Legacy hook. Component styles (metric cards, skill badges, recommendation badges) now live in theme.css."""
    return None


def render_metric_card(title: str, value: Any, subtext: str = ""):
    """Renders a metric summary tile."""
    sub_html = f"<div style='color: #64748b; font-size: 0.78rem; margin-top: 4px;'>{subtext}</div>" if subtext else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_skill_badges(matched: List[str], partial: List[Dict[str, Any]], missing: List[str]):
    """Renders visual color-coded badges for skill gaps."""
    html = "<div style='margin-bottom: 12px;'>"

    if matched:
        html += "<div style='margin-bottom: 8px;'><strong style='color: #334155; font-size: 0.85rem;'>Matched Skills: </strong><br/>"
        for s in matched:
            html += f"<span class='badge-matched'>✓ {s}</span>"
        html += "</div>"

    if partial:
        html += "<div style='margin-bottom: 8px;'><strong style='color: #334155; font-size: 0.85rem;'>Partially Matched: </strong><br/>"
        for p in partial:
            req = p.get('required_skill')
            rel = p.get('related_candidate_skill')
            html += f"<span class='badge-partial' title='Candidate has {rel}'>≈ {req} <em>({rel})</em></span>"
        html += "</div>"

    if missing:
        html += "<div><strong style='color: #334155; font-size: 0.85rem;'>Missing Skills: </strong><br/>"
        for s in missing:
            html += f"<span class='badge-missing'>✗ {s}</span>"
        html += "</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_recommendation_badge(status_key: str, label: str):
    """Renders styled pill badge for candidate recommendation."""
    css_class = {
        "STRONGLY_RECOMMENDED": "rec-badge-strong",
        "RECOMMENDED": "rec-badge-rec",
        "HR_REVIEW": "rec-badge-review",
        "NOT_RECOMMENDED": "rec-badge-reject"
    }.get(status_key, "rec-badge-review")

    st.markdown(f"<span class='{css_class}'>{label}</span>", unsafe_allow_html=True)


def create_radar_comparison_chart(candidates_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Creates an interactive Plotly Radar Chart comparing multiple candidates
    across all scoring dimensions.
    """
    categories = [
        "Technical Skills", 
        "Semantic JD", 
        "Experience", 
        "Education", 
        "Projects", 
        "Certifications", 
        "Resume Quality"
    ]

    fig = go.Figure()

    colors = ["#4f46e5", "#0f172a", "#059669", "#d97706", "#64748b", "#dc2626"]

    for idx, cand in enumerate(candidates_data):
        b = cand.get("breakdown", {})
        values = [
            b.get("technical_skills", 0),
            b.get("semantic_jd", 0),
            b.get("experience", 0),
            b.get("education", 0),
            b.get("projects", 0),
            b.get("certifications", 0),
            b.get("resume_quality", 0)
        ]
        # Close radar loop
        values_loop = values + [values[0]]
        cat_loop = categories + [categories[0]]

        color = colors[idx % len(colors)]
        fig.add_trace(go.Scatterpolar(
            r=values_loop,
            theta=cat_loop,
            fill='toself',
            name=cand.get("candidate_name", f"Candidate {idx+1}"),
            line=dict(color=color, width=2.5),
            opacity=0.35
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#64748b"),
                gridcolor="#e2e8f0"
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#334155", family="Inter"),
                gridcolor="#e2e8f0"
            ),
            bgcolor="#ffffff"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            font=dict(color="#334155", size=12),
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=25, b=40),
        height=440
    )

    return fig


def create_candidate_breakdown_bar_chart(breakdown: Dict[str, float]) -> go.Figure:
    """Creates a horizontal bar chart displaying candidate dimensional scores."""
    labels = {
        "technical_skills": "Technical Skills Match",
        "semantic_jd": "Semantic Context Match",
        "experience": "Experience Alignment",
        "education": "Education Criteria",
        "projects": "Project Depth",
        "certifications": "Certifications",
        "resume_quality": "ATS Quality Score"
    }

    cats = []
    scores = []
    bar_colors = []

    for k, name in labels.items():
        if k in breakdown:
            val = breakdown[k]
            cats.append(name)
            scores.append(val)
            if val >= 80:
                bar_colors.append("#059669")  # green
            elif val >= 60:
                bar_colors.append("#4f46e5")  # accent
            elif val >= 40:
                bar_colors.append("#d97706")  # amber
            else:
                bar_colors.append("#dc2626")  # red

    fig = go.Figure(go.Bar(
        x=scores,
        y=cats,
        orientation='h',
        marker=dict(
            color=bar_colors, 
            
            cornerradius=4
        ),
        text=[f"{s}%" for s in scores],
        textposition='outside',
        textfont=dict(color="#334155", size=11, family="JetBrains Mono")
    ))

    fig.update_layout(
        xaxis=dict(range=[0, 115], gridcolor="#e2e8f0", tickfont=dict(color="#64748b")),
        yaxis=dict(autorange="reversed", tickfont=dict(color="#334155", size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=35, t=10, b=10),
        height=290
    )

    return fig

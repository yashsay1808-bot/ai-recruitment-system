"""
Candidate Comparison Matrix View
Allows recruiters to compare top candidates side-by-side with Plotly Radar charts,
dimensional score matrices, and skill overlap comparisons.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from src.ui.components import create_radar_comparison_chart


def render_candidate_comparison_view(
    ranked_candidates: List[Dict[str, Any]],
    current_jd: Dict[str, Any]
):
    """Renders multi-candidate comparison radar charts and comparison matrix."""
    st.markdown("## ⚔️ Candidate Comparison Matrix")
    st.markdown("Select 2 to 4 candidates to benchmark side-by-side across all evaluation dimensions.")

    if not ranked_candidates or len(ranked_candidates) < 2:
        st.info("At least 2 screened candidates are required to perform side-by-side comparison.")
        return

    # Multi-select candidates
    cand_dict = {f"#{c.get('rank', 1)} - {c.get('candidate_name')} ({c.get('overall_score')}%)": c for c in ranked_candidates}
    default_selection = list(cand_dict.keys())[:min(3, len(cand_dict))]

    selected_cand_keys = st.multiselect(
        "Select Candidates to Compare",
        list(cand_dict.keys()),
        default=default_selection
    )

    if len(selected_cand_keys) < 2:
        st.warning("Please select at least 2 candidates to generate the comparison matrix.")
        return

    selected_candidates = [cand_dict[k] for k in selected_cand_keys]

    # 1. Interactive Radar Chart
    st.subheader("🕸️ Dimensional Radar Comparison")
    radar_fig = create_radar_comparison_chart(selected_candidates)
    st.plotly_chart(radar_fig, use_container_width=True)

    st.markdown("---")

    # 2. Side-by-Side Comparison Matrix Table
    st.subheader("📋 Side-by-Side Evaluation Matrix")

    criteria = [
        ("Overall Match Score", lambda c: f"{c.get('overall_score', 0)}%"),
        ("Recommendation", lambda c: c.get('explanation', {}).get('status_label', 'N/A')),
        ("Technical Skills Match", lambda c: f"{c.get('breakdown', {}).get('technical_skills', 0)}%"),
        ("Semantic JD Fit", lambda c: f"{c.get('breakdown', {}).get('semantic_jd', 0)}%"),
        ("Experience Alignment", lambda c: f"{c.get('breakdown', {}).get('experience', 0)}%"),
        ("Experience Years", lambda c: f"{c.get('candidate_data', {}).get('experience', {}).get('years_of_experience', 0)} yrs"),
        ("Education Credentials", lambda c: f"{c.get('candidate_data', {}).get('education', {}).get('degree', 'B.E.')}"),
        ("Academic CGPA / Score", lambda c: f"{c.get('candidate_data', {}).get('education', {}).get('cgpa', 'N/A')}"),
        ("Project Depth Score", lambda c: f"{c.get('breakdown', {}).get('projects', 0)}%"),
        ("Certifications Score", lambda c: f"{c.get('breakdown', {}).get('certifications', 0)}%"),
        ("ATS Quality Rating", lambda c: f"{c.get('breakdown', {}).get('resume_quality', 0)}%"),
        ("Matched Skills Count", lambda c: f"{c.get('gap_results', {}).get('matched_count', 0)} / {c.get('gap_results', {}).get('total_required', 0)}"),
        ("Missing Skills Count", lambda c: f"{c.get('gap_results', {}).get('missing_count', 0)}")
    ]

    matrix_data = {"Evaluation Dimension": [item[0] for item in criteria]}
    for c in selected_candidates:
        c_name = c.get("candidate_name", "Candidate")
        matrix_data[c_name] = [item[1](c) for item in criteria]

    df_matrix = pd.DataFrame(matrix_data)
    st.table(df_matrix)

    st.markdown("---")

    # 3. Skill Comparison Breakdown
    st.subheader("🧩 Skill Coverage Breakdown")
    cols = st.columns(len(selected_candidates))

    for idx, c in enumerate(selected_candidates):
        with cols[idx]:
            st.markdown(f"#### {c.get('candidate_name')}")
            gap = c.get("gap_results", {})
            matched = gap.get("matched_skills", [])
            missing = gap.get("missing_skills", [])
            
            st.markdown(f"**✓ Matched Skills ({len(matched)}):**")
            if matched:
                for s in matched:
                    st.markdown(f"<span class='badge-matched'>{s}</span>", unsafe_allow_html=True)
            else:
                st.caption("None matched")

            st.markdown(f"<div style='margin-top: 10px;'><strong>✗ Missing Skills ({len(missing)}):</strong></div>", unsafe_allow_html=True)
            if missing:
                for s in missing:
                    st.markdown(f"<span class='badge-missing'>{s}</span>", unsafe_allow_html=True)
            else:
                st.caption("No missing skills")

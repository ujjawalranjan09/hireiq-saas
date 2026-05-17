"""Reusable chart display component for Streamlit."""

import streamlit as st
import os
import json
from typing import Dict, Optional


def show_charts(chart_paths: Dict[str, str]) -> None:
    """Display all available charts.
    
    Args:
        chart_paths: Dictionary mapping chart names to file paths or JSON strings.
    """
    chart_tabs = st.tabs([
        "📊 Score Bar",
        "📈 Score Line",
        "🌊 Emotion Area",
        "🎯 Skill Radar",
        "🥧 Type Pie",
        "📉 Difficulty Step",
        "📊 Score Components",
    ])

    chart_keys = [
        "score_bar",
        "score_line",
        "emotion_area",
        "skill_radar",
        "type_pie",
        "difficulty_step",
        "comparison_grouped",
    ]

    for tab, key in zip(chart_tabs, chart_keys):
        with tab:
            _display_chart(chart_paths.get(key, ""), key)


def _display_chart(chart_data: str, chart_name: str) -> None:
    """Display a single chart from path or JSON data.
    
    Args:
        chart_data: File path or JSON string.
        chart_name: Name of the chart.
    """
    if not chart_data:
        st.info(f"No data available for {chart_name}.")
        return

    # If it's a file path
    if os.path.exists(chart_data):
        if chart_data.endswith(".html"):
            with open(chart_data, "r") as f:
                html = f.read()
            st.components.v1.html(html, height=500)
            return
        elif chart_data.endswith((".png", ".jpg", ".jpeg")):
            st.image(chart_data, use_container_width=True)
            return

    # If it's JSON data
    try:
        import plotly.graph_objects as go
        fig = go.Figure(json.loads(chart_data))
        st.plotly_chart(fig, use_container_width=True)
        return
    except (json.JSONDecodeError, Exception):
        pass

    # If it's inline HTML
    if chart_data.startswith("<") or "plotly" in chart_data.lower():
        st.components.v1.html(chart_data, height=500)
        return

    st.warning(f"Could not display chart: {chart_name}")


def show_single_chart(chart_data: str, title: str = "") -> None:
    """Display a single chart with optional title.
    
    Args:
        chart_data: File path, JSON, or HTML content.
        title: Optional title.
    """
    if title:
        st.subheader(title)
    _display_chart(chart_data, title)


def show_metric_card(label: str, value: str, delta: Optional[str] = None) -> None:
    """Display a metric card.
    
    Args:
        label: Metric label.
        value: Metric value.
        delta: Optional delta value.
    """
    st.metric(label=label, value=value, delta=delta)


def show_score_gauge(score: float, label: str = "Score") -> None:
    """Display a score as a gauge chart.
    
    Args:
        score: Score value (0-100).
        label: Label for the gauge.
    """
    try:
        import plotly.graph_objects as go
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": label},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": _get_gauge_color(score)},
                "steps": [
                    {"range": [0, 40], "color": "#ffcccc"},
                    {"range": [40, 60], "color": "#fff3cd"},
                    {"range": [60, 80], "color": "#d4edda"},
                    {"range": [80, 100], "color": "#cce5ff"},
                ],
            },
        ))
        fig.update_layout(height=250, margin=dict(t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.metric(label=label, value=f"{score:.0f}/100")


def _get_gauge_color(score: float) -> str:
    """Get color for gauge based on score."""
    if score >= 80:
        return "#2ecc71"
    elif score >= 60:
        return "#f39c12"
    else:
        return "#e74c3c"

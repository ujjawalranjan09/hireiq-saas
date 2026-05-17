"""Plotly chart generator for interview analytics."""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_all_charts(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]] = None,
    metrics: Dict[str, Any] = None,
    output_dir: str = "",
) -> Dict[str, str]:
    """Generate all 7 chart types and save as HTML/JSON.
    
    Args:
        questions: List of question data with scores.
        emotion_timeline: List of emotion snapshots.
        metrics: Performance metrics dictionary.
        output_dir: Directory to save chart files.
        
    Returns:
        Dictionary mapping chart names to file paths.
    """
    charts = {}

    try:
        charts["score_bar"] = generate_score_bar_chart(questions, output_dir)
        charts["score_line"] = generate_score_line_chart(questions, output_dir)
        charts["emotion_area"] = generate_emotion_area_chart(emotion_timeline or [], output_dir)
        charts["skill_radar"] = generate_skill_radar_chart(metrics or {}, output_dir)
        charts["type_pie"] = generate_type_pie_chart(questions, output_dir)
        charts["difficulty_step"] = generate_difficulty_step_chart(questions, output_dir)
        charts["comparison_grouped"] = generate_comparison_grouped_bar(questions, output_dir)
    except Exception as e:
        logger.error(f"Chart generation error: {e}")

    return charts


def generate_score_bar_chart(questions: List[Dict[str, Any]], output_dir: str = "") -> str:
    """Generate a bar chart of question scores.
    
    Args:
        questions: Question data list.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.warning("Plotly not available")
        return _fallback_chart_data("bar", questions)

    labels = [f"Q{i+1}" for i in range(len(questions))]
    scores = [q.get("answer_score", 0) for q in questions]
    colors = [_score_color(s) for s in scores]

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=scores,
            marker_color=colors,
            text=[f"{s:.0f}" for s in scores],
            textposition="auto",
        )
    ])

    fig.update_layout(
        title="Score per Question",
        xaxis_title="Question",
        yaxis_title="Score (0-100)",
        yaxis_range=[0, 100],
        template="plotly_white",
    )

    return _save_chart(fig, "score_bar", output_dir)


def generate_score_line_chart(questions: List[Dict[str, Any]], output_dir: str = "") -> str:
    """Generate a line chart showing score progression.
    
    Args:
        questions: Question data list.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _fallback_chart_data("line", questions)

    labels = [f"Q{i+1}" for i in range(len(questions))]
    scores = [q.get("answer_score", 0) for q in questions]

    # Add rolling average
    rolling_avg = []
    window = 3
    for i in range(len(scores)):
        start = max(0, i - window + 1)
        rolling_avg.append(sum(scores[start:i+1]) / (i - start + 1))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=scores,
        mode="lines+markers",
        name="Score",
        line=dict(color="#3498db", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=rolling_avg,
        mode="lines",
        name=f"Rolling Avg ({window})",
        line=dict(color="#e74c3c", width=2, dash="dash"),
    ))

    fig.update_layout(
        title="Score Progression",
        xaxis_title="Question",
        yaxis_title="Score",
        yaxis_range=[0, 100],
        template="plotly_white",
    )

    return _save_chart(fig, "score_line", output_dir)


def generate_emotion_area_chart(emotion_timeline: List[Dict[str, Any]], output_dir: str = "") -> str:
    """Generate an area chart of confidence over time.
    
    Args:
        emotion_timeline: Emotion snapshot data.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _fallback_chart_data("area", emotion_timeline)

    if not emotion_timeline:
        fig = go.Figure()
        fig.update_layout(title="Emotion Timeline (No Data)")
        return _save_chart(fig, "emotion_area", output_dir)

    timestamps = list(range(len(emotion_timeline)))
    confidences = [e.get("combined_confidence_score", 50) for e in emotion_timeline]
    emotions = [e.get("facial_emotion", "neutral") for e in emotion_timeline]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=confidences,
        fill="tozeroy",
        mode="lines",
        name="Confidence",
        line=dict(color="#2ecc71"),
        fillcolor="rgba(46,204,113,0.3)",
        text=emotions,
        hovertemplate="Time: %{x}<br>Confidence: %{y:.1f}<br>Emotion: %{text}",
    ))

    fig.update_layout(
        title="Confidence Over Time",
        xaxis_title="Time (snapshots)",
        yaxis_title="Confidence Score",
        yaxis_range=[0, 100],
        template="plotly_white",
    )

    return _save_chart(fig, "emotion_area", output_dir)


def generate_skill_radar_chart(metrics: Dict[str, Any], output_dir: str = "") -> str:
    """Generate a radar chart of performance dimensions.
    
    Args:
        metrics: Performance metrics dictionary.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _fallback_chart_data("radar", metrics)

    categories = [
        "Semantic Understanding",
        "Keyword Usage",
        "Concept Coverage",
        "Confidence",
        "Fluency",
        "Overall Score",
    ]
    values = [
        metrics.get("average_semantic", 0),
        metrics.get("average_keyword", 0),
        metrics.get("average_concept", 0),
        metrics.get("average_confidence", 50),
        metrics.get("emotion_stability", 0.8) * 100,
        metrics.get("average_score", 0),
    ]

    # Close the radar
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure(data=go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        line=dict(color="#9b59b6"),
        fillcolor="rgba(155,89,182,0.3)",
    ))

    fig.update_layout(
        title="Performance Radar",
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        template="plotly_white",
    )

    return _save_chart(fig, "skill_radar", output_dir)


def generate_type_pie_chart(questions: List[Dict[str, Any]], output_dir: str = "") -> str:
    """Generate a pie chart of question type distribution and avg scores.
    
    Args:
        questions: Question data list.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _fallback_chart_data("pie", questions)

    type_counts = {}
    type_scores = {}
    for q in questions:
        q_type = q.get("question_type", "unknown")
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
        if q_type not in type_scores:
            type_scores[q_type] = []
        type_scores[q_type].append(q.get("answer_score", 0))

    labels = list(type_counts.keys())
    values = list(type_counts.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo="label+percent",
    )])

    fig.update_layout(
        title="Question Type Distribution",
        template="plotly_white",
    )

    return _save_chart(fig, "type_pie", output_dir)


def generate_difficulty_step_chart(questions: List[Dict[str, Any]], output_dir: str = "") -> str:
    """Generate a step chart showing difficulty changes.
    
    Args:
        questions: Question data list.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _fallback_chart_data("step", questions)

    from app.constants import DifficultyLevel

    labels = [f"Q{i+1}" for i in range(len(questions))]
    difficulties = [DifficultyLevel.LEVELS.get(q.get("difficulty", "medium"), 2) for q in questions]
    scores = [q.get("answer_score", 0) for q in questions]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=difficulties,
        mode="lines",
        line_shape="hv",
        name="Difficulty",
        line=dict(color="#e67e22", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=labels,
        y=[s / 25 for s in scores],  # Scale scores to 0-4
        mode="markers",
        name="Score (scaled)",
        marker=dict(color="#3498db", size=8),
    ))

    fig.update_layout(
        title="Difficulty Progression",
        xaxis_title="Question",
        yaxis_title="Difficulty Level",
        yaxis=dict(
            tickvals=[1, 2, 3, 4],
            ticktext=["Easy", "Medium", "Hard", "Expert"],
            range=[0.5, 4.5],
        ),
        template="plotly_white",
    )

    return _save_chart(fig, "difficulty_step", output_dir)


def generate_comparison_grouped_bar(questions: List[Dict[str, Any]], output_dir: str = "") -> str:
    """Generate a grouped bar chart comparing score components.
    
    Args:
        questions: Question data list.
        output_dir: Output directory.
        
    Returns:
        Path to saved chart file or JSON string.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _fallback_chart_data("grouped_bar", questions)

    labels = [f"Q{i+1}" for i in range(len(questions))]
    semantic = [q.get("semantic_similarity_score", 0) for q in questions]
    keyword = [q.get("keyword_match_score", 0) for q in questions]
    concept = [q.get("concept_coverage_score", 0) for q in questions]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Semantic", x=labels, y=semantic, marker_color="#3498db"))
    fig.add_trace(go.Bar(name="Keywords", x=labels, y=keyword, marker_color="#e74c3c"))
    fig.add_trace(go.Bar(name="Concepts", x=labels, y=concept, marker_color="#2ecc71"))

    fig.update_layout(
        title="Score Component Breakdown",
        xaxis_title="Question",
        yaxis_title="Score",
        barmode="group",
        yaxis_range=[0, 100],
        template="plotly_white",
    )

    return _save_chart(fig, "comparison_grouped", output_dir)


def _save_chart(fig, name: str, output_dir: str) -> str:
    """Save chart to file or return as JSON."""
    if output_dir:
        path = Path(output_dir) / f"{name}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(path))
        return str(path)
    else:
        return fig.to_json()


def _score_color(score: float) -> str:
    """Get color based on score."""
    if score >= 80:
        return "#2ecc71"
    elif score >= 60:
        return "#f39c12"
    else:
        return "#e74c3c"


def _fallback_chart_data(chart_type: str, data: Any) -> str:
    """Return basic JSON data when Plotly is not available."""
    import json
    return json.dumps({"type": chart_type, "data": str(data)[:500]})

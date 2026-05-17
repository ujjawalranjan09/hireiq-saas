"""PDF report generator using FPDF2."""

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_pdf_report(
    candidate_name: str,
    interview_data: Dict[str, Any],
    questions: List[Dict[str, Any]],
    feedback: Dict[str, Any],
    metrics: Dict[str, Any],
    chart_paths: Dict[str, str] = None,
    output_path: str = "",
) -> str:
    """Generate a comprehensive PDF interview report.
    
    Args:
        candidate_name: Name of the candidate.
        interview_data: Interview session data.
        questions: List of question data with scores.
        feedback: Generated feedback dictionary.
        metrics: Performance metrics.
        chart_paths: Paths to generated chart images.
        output_path: Where to save the PDF.
        
    Returns:
        Path to the generated PDF file.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 not installed. Install with: pip install fpdf2")

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = candidate_name.replace(" ", "_").lower()
        output_path = str(Path(__file__).resolve().parent.parent.parent / "outputs" / "reports" / f"report_{safe_name}_{timestamp}.pdf")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ─── Page 1: Title & Summary ─────────────────────────────────────
    pdf.add_page()
    _add_header(pdf, candidate_name, interview_data)

    # Overall score
    avg_score = metrics.get("average_score", 0)
    grade = metrics.get("overall_grade", "N/A")
    _add_score_box(pdf, avg_score, grade)

    # Key metrics
    _add_key_metrics(pdf, metrics)

    # ─── Page 2: Question Details ─────────────────────────────────────
    pdf.add_page()
    _add_section_title(pdf, "Question-by-Question Performance")
    _add_question_table(pdf, questions)

    # ─── Page 3: Feedback ─────────────────────────────────────────────
    pdf.add_page()
    _add_section_title(pdf, "Interview Feedback")
    _add_feedback_section(pdf, feedback)

    # ─── Page 4: Charts (if available) ────────────────────────────────
    if chart_paths:
        pdf.add_page()
        _add_section_title(pdf, "Performance Charts")
        _add_charts(pdf, chart_paths)

    # Save
    pdf.output(output_path)
    logger.info(f"PDF report generated: {output_path}")
    return output_path


def _add_header(pdf, candidate_name: str, interview_data: Dict[str, Any]) -> None:
    """Add report header."""
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "AI Interview Agent", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, "Interview Performance Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Candidate: {candidate_name}", new_x="LMARGIN", new_y="NEXT")

    date_str = interview_data.get("created_at", datetime.now())
    if hasattr(date_str, "strftime"):
        date_str = date_str.strftime("%Y-%m-%d %H:%M")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Date: {date_str}", new_x="LMARGIN", new_y="NEXT")

    status = interview_data.get("status", "completed")
    pdf.cell(0, 6, f"Status: {status}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)


def _add_score_box(pdf, score: float, grade: str) -> None:
    """Add a prominent score box."""
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)

    y = pdf.get_y()
    pdf.rect(15, y, 180, 25, style="F")
    pdf.set_xy(15, y + 3)
    pdf.cell(90, 10, f"Overall Score: {score:.1f}/100", align="C")
    pdf.set_xy(105, y + 3)
    pdf.cell(90, 10, f"Grade: {grade}", align="C")

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + 30)


def _add_key_metrics(pdf, metrics: Dict[str, Any]) -> None:
    """Add key performance metrics."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Key Metrics", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    metrics_list = [
        ("Questions Answered", f"{metrics.get('questions_answered', 0)}/{metrics.get('total_questions', 0)}"),
        ("Average Score", f"{metrics.get('average_score', 0):.1f}/100"),
        ("Highest Score", f"{metrics.get('max_score', 0):.1f}/100"),
        ("Lowest Score", f"{metrics.get('min_score', 0):.1f}/100"),
        ("Score Trend", metrics.get("score_trend", "N/A")),
        ("Confidence Level", f"{metrics.get('average_confidence', 50):.1f}/100"),
        ("Dominant Emotion", metrics.get("dominant_emotion", "neutral")),
    ]

    for label, value in metrics_list:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, f"{label}:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")


def _add_section_title(pdf, title: str) -> None:
    """Add a section title."""
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)


def _add_question_table(pdf, questions: List[Dict[str, Any]]) -> None:
    """Add a table of question performances."""
    # Header
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(52, 73, 94)
    pdf.set_text_color(255, 255, 255)
    col_widths = [10, 30, 25, 20, 20, 20, 65]
    headers = ["#", "Type", "Difficulty", "Score", "Semantic", "Keyword", "Question"]

    for i, (header, width) in enumerate(zip(headers, col_widths)):
        pdf.cell(width, 7, header, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 7)

    for i, q in enumerate(questions[:20]):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(245, 245, 245)

        question_text = q.get("question_text", "")[:60]
        if len(q.get("question_text", "")) > 60:
            question_text += "..."

        row = [
            str(i + 1),
            q.get("question_type", "?")[:10],
            q.get("difficulty", "?"),
            f"{q.get('answer_score', 0):.0f}",
            f"{q.get('semantic_similarity_score', 0):.0f}",
            f"{q.get('keyword_match_score', 0):.0f}",
            question_text,
        ]

        for val, width in zip(row, col_widths):
            pdf.cell(width, 6, val, border=1, fill=fill)
        pdf.ln()


def _add_feedback_section(pdf, feedback: Dict[str, Any]) -> None:
    """Add the feedback section."""
    # Strengths
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 8, "Strengths", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for strength in feedback.get("strengths", []):
        pdf.cell(5, 6, chr(9679))  # bullet
        pdf.multi_cell(0, 6, strength)
        pdf.ln(1)

    pdf.ln(3)

    # Weaknesses
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(231, 76, 60)
    pdf.cell(0, 8, "Areas for Improvement", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for weakness in feedback.get("weaknesses", []):
        pdf.cell(5, 6, chr(9679))
        pdf.multi_cell(0, 6, weakness)
        pdf.ln(1)

    pdf.ln(3)

    # Suggestions
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(52, 152, 219)
    pdf.cell(0, 8, "Suggestions", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    for suggestion in feedback.get("suggestions", []):
        pdf.cell(5, 6, chr(9679))
        pdf.multi_cell(0, 6, suggestion)
        pdf.ln(1)

    pdf.ln(3)

    # Overall assessment
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Overall Assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, feedback.get("overall_assessment", "No assessment available."))


def _add_charts(pdf, chart_paths: Dict[str, str]) -> None:
    """Add chart images to the report."""
    for name, path in chart_paths.items():
        if os.path.exists(path) and path.endswith((".png", ".jpg", ".jpeg")):
            try:
                pdf.image(path, x=10, w=190)
                pdf.ln(5)
            except Exception as e:
                logger.warning(f"Could not add chart {name}: {e}")
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, f"[Chart: {name}]", new_x="LMARGIN", new_y="NEXT")

"""LLM-based feedback generator for interview reports."""

import logging
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def generate_feedback(
    candidate_name: str,
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]] = None,
    metrics: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Generate comprehensive feedback for the interview.
    
    Args:
        candidate_name: Name of the candidate.
        questions: List of question data with scores.
        emotion_timeline: List of emotion snapshots.
        metrics: Performance metrics.
        
    Returns:
        Dictionary with strengths, weaknesses, suggestions, and assessment.
    """
    # Try LLM generation first
    try:
        return _generate_feedback_llm(candidate_name, questions, emotion_timeline, metrics)
    except Exception as e:
        logger.warning(f"LLM feedback generation failed, using rule-based: {e}")
        return _generate_feedback_rule_based(questions, emotion_timeline, metrics)


def _generate_feedback_llm(
    candidate_name: str,
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate feedback using OpenAI API."""
    from app.config import OPENAI_API_KEY, OPENAI_MODEL
    from app.constants import FEEDBACK_PROMPT

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Build prompt inputs
    total_questions = len(questions)
    scores = [q.get("answer_score", 0) for q in questions]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Score breakdown by type
    type_scores = {}
    for q in questions:
        q_type = q.get("question_type", "unknown")
        if q_type not in type_scores:
            type_scores[q_type] = []
        type_scores[q_type].append(q.get("answer_score", 0))

    score_breakdown = "\n".join(
        f"  {q_type}: avg {sum(s)/len(s):.1f}/100 ({len(s)} questions)"
        for q_type, s in type_scores.items()
    )

    # Question details
    question_details = "\n".join(
        f"  Q{i+1} [{q.get('question_type','?')}] ({q.get('difficulty','?')}): "
        f"Score {q.get('answer_score',0):.1f} - "
        f"{q.get('question_text','')[:80]}..."
        for i, q in enumerate(questions[:15])
    )

    # Emotion summary
    if emotion_timeline:
        emotions = [e.get("facial_emotion", "neutral") for e in emotion_timeline]
        from collections import Counter
        emotion_counts = Counter(emotions)
        emotion_summary = ", ".join(f"{e}: {c}" for e, c in emotion_counts.most_common(5))
    else:
        emotion_summary = "No emotion data available"

    prompt = FEEDBACK_PROMPT.format(
        name=candidate_name,
        total_questions=total_questions,
        avg_score=avg_score,
        score_breakdown=score_breakdown,
        question_details=question_details,
        emotion_summary=emotion_summary,
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert interview coach. Return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    feedback = json.loads(content)

    return {
        "strengths": feedback.get("strengths", []),
        "weaknesses": feedback.get("weaknesses", []),
        "suggestions": feedback.get("suggestions", []),
        "overall_assessment": feedback.get("overall_assessment", ""),
        "source": "llm",
    }


def _generate_feedback_rule_based(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate feedback using rule-based analysis."""
    strengths = []
    weaknesses = []
    suggestions = []

    scores = [q.get("answer_score", 0) for q in questions]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Analyze by question type
    type_scores = {}
    for q in questions:
        q_type = q.get("question_type", "unknown")
        if q_type not in type_scores:
            type_scores[q_type] = []
        type_scores[q_type].append(q.get("answer_score", 0))

    type_avgs = {
        q_type: sum(s) / len(s) if s else 0
        for q_type, s in type_scores.items()
    }

    # Strengths
    if avg_score >= 75:
        strengths.append("Consistently strong answers across the interview")
    for q_type, avg in type_avgs.items():
        if avg >= 80:
            strengths.append(f"Excellent performance on {q_type} questions (avg: {avg:.0f})")
    if not strengths:
        strengths.append("Completed the full interview")

    # Weaknesses
    for q_type, avg in type_avgs.items():
        if avg < 50:
            weaknesses.append(f"Struggled with {q_type} questions (avg: {avg:.0f})")
    low_scores = [s for s in scores if s < 40]
    if len(low_scores) > len(scores) * 0.3:
        weaknesses.append("Multiple questions answered below expectations")

    # Suggestions
    if type_avgs.get("technical", 100) < 60:
        suggestions.append("Review core technical concepts and practice explaining them clearly")
    if type_avgs.get("behavioral", 100) < 60:
        suggestions.append("Practice the STAR method (Situation, Task, Action, Result) for behavioral questions")
    if type_avgs.get("resume", 100) < 60:
        suggestions.append("Prepare detailed stories about your past projects and contributions")

    # Emotion analysis
    if emotion_timeline:
        confidences = [e.get("combined_confidence_score", 50) for e in emotion_timeline]
        avg_conf = sum(confidences) / len(confidences)
        if avg_conf < 40:
            weaknesses.append("Low confidence detected throughout the interview")
            suggestions.append("Practice mock interviews to build confidence")
        elif avg_conf > 70:
            strengths.append("Maintained good confidence throughout the interview")

    if not weaknesses:
        weaknesses.append("No major weaknesses identified")
    if not suggestions:
        suggestions.append("Continue practicing and refining your interview skills")

    # Overall assessment
    if avg_score >= 80:
        assessment = "Strong overall performance. The candidate demonstrated solid knowledge and communication skills."
    elif avg_score >= 60:
        assessment = "Good performance with room for improvement in specific areas."
    elif avg_score >= 40:
        assessment = "Below average performance. Several areas need significant improvement."
    else:
        assessment = "Performance needs substantial improvement. Focus on fundamentals and practice."

    return {
        "strengths": strengths[:3],
        "weaknesses": weaknesses[:3],
        "suggestions": suggestions[:3],
        "overall_assessment": assessment,
        "source": "rule_based",
    }

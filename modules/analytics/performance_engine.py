"""Aggregate performance metrics calculation engine."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def calculate_performance_metrics(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate comprehensive performance metrics from interview data.
    
    Args:
        questions: List of question dictionaries with scores.
        emotion_timeline: List of emotion snapshots.
        
    Returns:
        Dictionary of performance metrics.
    """
    metrics = {}

    # Answer scores
    scores = [q.get("answer_score", 0) for q in questions if q.get("answer_score", 0) > 0]
    if scores:
        metrics["average_score"] = round(sum(scores) / len(scores), 1)
        metrics["max_score"] = round(max(scores), 1)
        metrics["min_score"] = round(min(scores), 1)
        metrics["score_std"] = round(_std(scores), 1)
        metrics["questions_answered"] = len(scores)
    else:
        metrics["average_score"] = 0.0
        metrics["max_score"] = 0.0
        metrics["min_score"] = 0.0
        metrics["score_std"] = 0.0
        metrics["questions_answered"] = 0

    metrics["total_questions"] = len(questions)

    # Score by question type
    type_scores = {}
    for q in questions:
        q_type = q.get("question_type", "technical")
        score = q.get("answer_score", 0)
        if q_type not in type_scores:
            type_scores[q_type] = []
        type_scores[q_type].append(score)

    metrics["scores_by_type"] = {
        q_type: round(sum(scores) / len(scores), 1) if scores else 0.0
        for q_type, scores in type_scores.items()
    }

    # Score by difficulty
    diff_scores = {}
    for q in questions:
        diff = q.get("difficulty", "medium")
        score = q.get("answer_score", 0)
        if diff not in diff_scores:
            diff_scores[diff] = []
        diff_scores[diff].append(score)

    metrics["scores_by_difficulty"] = {
        diff: round(sum(scores) / len(scores), 1) if scores else 0.0
        for diff, scores in diff_scores.items()
    }

    # Score trend (improving/declining)
    if len(scores) >= 3:
        first_half = scores[:len(scores) // 2]
        second_half = scores[len(scores) // 2:]
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        diff = second_avg - first_avg
        if diff > 5:
            metrics["score_trend"] = "improving"
        elif diff < -5:
            metrics["score_trend"] = "declining"
        else:
            metrics["score_trend"] = "stable"
        metrics["trend_magnitude"] = round(diff, 1)
    else:
        metrics["score_trend"] = "insufficient_data"
        metrics["trend_magnitude"] = 0.0

    # Semantic / keyword / concept breakdown
    metrics["average_semantic"] = round(
        _avg([q.get("semantic_similarity_score", 0) for q in questions]), 1
    )
    metrics["average_keyword"] = round(
        _avg([q.get("keyword_match_score", 0) for q in questions]), 1
    )
    metrics["average_concept"] = round(
        _avg([q.get("concept_coverage_score", 0) for q in questions]), 1
    )

    # Emotion metrics
    if emotion_timeline:
        emotions = [e.get("facial_emotion", "neutral") for e in emotion_timeline]
        confidences = [e.get("combined_confidence_score", 50) for e in emotion_timeline]

        from collections import Counter
        emotion_counts = Counter(emotions)
        metrics["dominant_emotion"] = emotion_counts.most_common(1)[0][0] if emotions else "neutral"
        metrics["emotion_distribution"] = dict(emotion_counts)
        metrics["average_confidence"] = round(sum(confidences) / len(confidences), 1) if confidences else 50.0
        metrics["emotion_stability"] = round(
            1.0 - (sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i-1]) / max(len(emotions) - 1, 1)),
            3,
        )
    else:
        metrics["dominant_emotion"] = "neutral"
        metrics["emotion_distribution"] = {}
        metrics["average_confidence"] = 50.0
        metrics["emotion_stability"] = 1.0

    # Overall grade
    metrics["overall_grade"] = _score_to_grade(metrics["average_score"])

    return metrics


def calculate_comparison_metrics(
    current_scores: List[float],
    historical_scores: List[List[float]] = None,
) -> Dict[str, Any]:
    """Compare current performance to historical data.
    
    Args:
        current_scores: Scores from the current interview.
        historical_scores: Lists of scores from past interviews.
        
    Returns:
        Comparison metrics.
    """
    result = {}

    if not current_scores:
        return {"percentile": 0, "rank": "N/A"}

    current_avg = sum(current_scores) / len(current_scores)
    result["current_average"] = round(current_avg, 1)

    if historical_scores and len(historical_scores) > 0:
        historical_avgs = []
        for scores in historical_scores:
            if scores:
                historical_avgs.append(sum(scores) / len(scores))

        if historical_avgs:
            overall_avg = sum(historical_avgs) / len(historical_avgs)
            result["historical_average"] = round(overall_avg, 1)
            result["difference"] = round(current_avg - overall_avg, 1)
            result["percentile"] = round(
                sum(1 for avg in historical_avgs if current_avg >= avg) / len(historical_avgs) * 100,
                1,
            )

    return result


def _avg(values: list) -> float:
    """Calculate average of a list."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B-"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 50:
        return "C-"
    elif score >= 40:
        return "D"
    else:
        return "F"

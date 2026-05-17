"""Multimodal confidence model combining facial, voice, and fluency signals."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def calculate_confidence(
    facial_confidence: float = 50.0,
    voice_confidence: float = 50.0,
    fluency_score: float = 50.0,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate combined confidence score from multimodal signals.
    
    Formula: Total = 0.5×(Facial) + 0.3×(Voice Tone) + 0.2×(Fluency)
    
    Args:
        facial_confidence: Facial emotion confidence (0-100).
        voice_confidence: Voice tone confidence (0-100).
        fluency_score: Speech fluency score (0-100).
        weights: Custom weight overrides.
        
    Returns:
        Dictionary with combined score and breakdown.
    """
    from app.config import CONFIDENCE_WEIGHTS

    if weights:
        w = weights
    else:
        w = CONFIDENCE_WEIGHTS

    combined = (
        w["facial"] * facial_confidence +
        w["voice_tone"] * voice_confidence +
        w["fluency"] * fluency_score
    )

    combined = max(0.0, min(100.0, combined))

    return {
        "combined_score": round(combined, 1),
        "facial_score": round(facial_confidence, 1),
        "voice_score": round(voice_confidence, 1),
        "fluency_score": round(fluency_score, 1),
        "weights_used": w,
        "confidence_level": _score_to_level(combined),
    }


def calculate_fluency_score(
    speaking_speed: float,
    pause_ratio: float,
    hesitation_detected: bool,
    word_count: int = 0,
    duration: float = 0.0,
) -> float:
    """Calculate speech fluency score from voice features.
    
    Args:
        speaking_speed: Speaking rate in words per minute.
        pause_ratio: Fraction of audio that is silence.
        hesitation_detected: Whether hesitations were detected.
        word_count: Number of words spoken.
        duration: Duration in seconds.
        
    Returns:
        Fluency score (0-100).
    """
    score = 50.0

    # Speaking speed: ideal range is 120-160 wpm
    if 120 <= speaking_speed <= 160:
        score += 20
    elif 100 <= speaking_speed <= 180:
        score += 10
    elif speaking_speed < 80 or speaking_speed > 200:
        score -= 15

    # Pause ratio: too many pauses indicate lack of fluency
    if pause_ratio < 0.2:
        score += 15
    elif pause_ratio < 0.4:
        score += 5
    elif pause_ratio > 0.6:
        score -= 20

    # Hesitations
    if hesitation_detected:
        score -= 15

    # Answer length relative to duration
    if duration > 0 and word_count > 0:
        actual_wpm = (word_count / duration) * 60
        if 100 <= actual_wpm <= 180:
            score += 10

    return max(0.0, min(100.0, score))


def _score_to_level(score: float) -> str:
    """Convert numeric score to confidence level label."""
    if score >= 80:
        return "very_confident"
    elif score >= 65:
        return "confident"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "uncertain"
    else:
        return "low_confidence"


def aggregate_confidence_timeline(timeline: list) -> Dict[str, Any]:
    """Aggregate confidence scores over an interview timeline.
    
    Args:
        timeline: List of confidence calculation results.
        
    Returns:
        Aggregated statistics.
    """
    if not timeline:
        return {
            "average": 50.0,
            "min": 50.0,
            "max": 50.0,
            "trend": "stable",
        }

    scores = [entry.get("combined_score", 50.0) for entry in timeline]
    avg = sum(scores) / len(scores)

    # Calculate trend
    if len(scores) >= 3:
        first_half = scores[:len(scores) // 2]
        second_half = scores[len(scores) // 2:]
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        diff = second_avg - first_avg
        if diff > 5:
            trend = "improving"
        elif diff < -5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return {
        "average": round(avg, 1),
        "min": round(min(scores), 1),
        "max": round(max(scores), 1),
        "trend": trend,
        "data_points": len(scores),
    }

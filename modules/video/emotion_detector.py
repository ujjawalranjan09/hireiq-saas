"""DeepFace emotion classification from video frames."""

import logging
from typing import Dict, Any, Optional, List
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded DeepFace
_deepface_loaded = False


def _ensure_deepface():
    """Ensure DeepFace is available."""
    global _deepface_loaded
    if not _deepface_loaded:
        try:
            import deepface
            _deepface_loaded = True
        except ImportError:
            raise ImportError("deepface not installed. Install with: pip install deepface")
    return _deepface_loaded


def detect_emotion(frame: np.ndarray) -> Dict[str, Any]:
    """Detect emotion from a single video frame.
    
    Args:
        frame: Video frame as numpy array (BGR or RGB).
        
    Returns:
        Dictionary with:
            - dominant_emotion: The most likely emotion
            - emotion_scores: Scores for all emotions
            - face_detected: Whether a face was found
            - face_region: Bounding box of detected face
    """
    _ensure_deepface()

    try:
        from deepface import DeepFace

        # DeepFace expects BGR
        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )

        if isinstance(result, list):
            result = result[0]

        emotion_data = result.get("emotion", {})
        dominant = result.get("dominant_emotion", "neutral")
        face_region = result.get("region", {})

        # Normalize scores to 0-1
        total = sum(emotion_data.values()) if emotion_data else 1
        normalized_scores = {
            k: round(v / total, 4) if total > 0 else 0
            for k, v in emotion_data.items()
        }

        # Calculate confidence score (0-100)
        confidence = _emotion_to_confidence(dominant, normalized_scores)

        return {
            "dominant_emotion": dominant,
            "emotion_scores": normalized_scores,
            "face_detected": bool(face_region and face_region.get("w", 0) > 0),
            "face_region": face_region,
            "confidence_score": round(confidence, 1),
        }

    except Exception as e:
        logger.warning(f"Emotion detection failed: {e}")
        return {
            "dominant_emotion": "neutral",
            "emotion_scores": {},
            "face_detected": False,
            "face_region": {},
            "confidence_score": 50.0,
            "error": str(e),
        }


def detect_emotions_batch(frames: List[np.ndarray]) -> List[Dict[str, Any]]:
    """Detect emotions from multiple frames.
    
    Args:
        frames: List of video frames.
        
    Returns:
        List of emotion detection results.
    """
    results = []
    for frame in frames:
        result = detect_emotion(frame)
        results.append(result)
    return results


def _emotion_to_confidence(emotion: str, scores: Dict[str, float]) -> float:
    """Convert emotion classification to a confidence score.
    
    Positive emotions (happy, neutral, surprise) map to higher confidence.
    Negative emotions (angry, fear, sad, disgust) map to lower confidence.
    """
    from app.constants import POSITIVE_EMOTIONS, NEGATIVE_EMOTIONS

    base_score = 50.0

    if emotion.lower() in POSITIVE_EMOTIONS:
        base_score += 25
    elif emotion.lower() in NEGATIVE_EMOTIONS:
        base_score -= 20

    # Adjust by confidence of detection
    if emotion.lower() in scores:
        detection_confidence = scores[emotion.lower()]
        base_score *= (0.5 + 0.5 * detection_confidence)

    return max(0.0, min(100.0, base_score))


def get_emotion_summary(emotion_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize emotion detection results over multiple frames.
    
    Args:
        emotion_results: List of detection result dictionaries.
        
    Returns:
        Summary dictionary with dominant emotions, averages, etc.
    """
    if not emotion_results:
        return {"dominant_emotion": "neutral", "face_detection_rate": 0.0}

    emotions = [r.get("dominant_emotion", "neutral") for r in emotion_results]
    confidence_scores = [r.get("confidence_score", 50.0) for r in emotion_results]
    faces_detected = sum(1 for r in emotion_results if r.get("face_detected", False))

    # Count emotion frequencies
    from collections import Counter
    emotion_counts = Counter(emotions)
    most_common_emotion = emotion_counts.most_common(1)[0][0]

    return {
        "dominant_emotion": most_common_emotion,
        "emotion_distribution": dict(emotion_counts),
        "average_confidence": round(sum(confidence_scores) / len(confidence_scores), 1),
        "face_detection_rate": round(faces_detected / len(emotion_results), 3),
        "total_frames": len(emotion_results),
    }

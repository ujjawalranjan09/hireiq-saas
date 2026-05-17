"""Emotion timeline tracker with smoothing."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


class EmotionTracker:
    """Tracks emotions over time with temporal smoothing."""

    def __init__(self, window_size: int = 5):
        """Initialize the emotion tracker.
        
        Args:
            window_size: Number of recent frames for smoothing.
        """
        self.window_size = window_size
        self.timeline: List[Dict[str, Any]] = []
        self._recent_emotions: deque = deque(maxlen=window_size)
        self._recent_confidence: deque = deque(maxlen=window_size)

    def add_emotion(self, emotion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an emotion observation and return smoothed result.
        
        Args:
            emotion_data: Raw emotion detection result.
            
        Returns:
            Smoothed emotion data with timestamp.
        """
        timestamp = datetime.utcnow()
        raw_emotion = emotion_data.get("dominant_emotion", "neutral")
        raw_confidence = emotion_data.get("confidence_score", 50.0)

        self._recent_emotions.append(raw_emotion)
        self._recent_confidence.append(raw_confidence)

        # Smoothed values
        smoothed_emotion = self._smooth_emotion()
        smoothed_confidence = self._smooth_confidence()

        entry = {
            "timestamp": timestamp,
            "raw_emotion": raw_emotion,
            "smoothed_emotion": smoothed_emotion,
            "raw_confidence": raw_confidence,
            "smoothed_confidence": round(smoothed_confidence, 1),
            "face_detected": emotion_data.get("face_detected", False),
            "emotion_scores": emotion_data.get("emotion_scores", {}),
        }

        self.timeline.append(entry)
        return entry

    def _smooth_emotion(self) -> str:
        """Apply majority-vote smoothing to emotion labels."""
        if not self._recent_emotions:
            return "neutral"

        from collections import Counter
        counts = Counter(self._recent_emotions)
        return counts.most_common(1)[0][0]

    def _smooth_confidence(self) -> float:
        """Apply moving average smoothing to confidence scores."""
        if not self._recent_confidence:
            return 50.0
        return sum(self._recent_confidence) / len(self._recent_confidence)

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get the full emotion timeline."""
        return self.timeline

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the tracked emotions."""
        if not self.timeline:
            return {
                "dominant_emotion": "neutral",
                "average_confidence": 50.0,
                "emotion_changes": 0,
                "face_detection_rate": 0.0,
            }

        emotions = [e["smoothed_emotion"] for e in self.timeline]
        confidences = [e["smoothed_confidence"] for e in self.timeline]
        faces_detected = sum(1 for e in self.timeline if e.get("face_detected", False))

        # Count emotion transitions
        changes = sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i - 1])

        from collections import Counter
        emotion_counts = Counter(emotions)
        dominant = emotion_counts.most_common(1)[0][0]

        return {
            "dominant_emotion": dominant,
            "emotion_distribution": dict(emotion_counts),
            "average_confidence": round(sum(confidences) / len(confidences), 1),
            "emotion_changes": changes,
            "face_detection_rate": round(faces_detected / len(self.timeline), 3),
            "total_snapshots": len(self.timeline),
            "first_emotion": emotions[0] if emotions else "neutral",
            "last_emotion": emotions[-1] if emotions else "neutral",
        }

    def get_confidence_over_time(self) -> List[Dict[str, Any]]:
        """Get confidence scores over time for graphing."""
        return [
            {
                "timestamp": e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e["timestamp"]),
                "confidence": e["smoothed_confidence"],
                "emotion": e["smoothed_emotion"],
            }
            for e in self.timeline
        ]

    def reset(self) -> None:
        """Reset the tracker."""
        self.timeline = []
        self._recent_emotions.clear()
        self._recent_confidence.clear()

"""Multi-modal sentiment analyzer fusing facial, voice, and text signals."""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SentimentLabel(str, Enum):
    """Combined sentiment labels for interview context."""
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    ENGAGED = "engaged"
    DISENGAGED = "disengaged"
    NEUTRAL = "neutral"


@dataclass
class SentimentState:
    """Snapshot of the candidate's emotional state at a point in time."""
    label: SentimentLabel
    confidence: float  # 0-1
    facial_score: float  # -1 to 1
    voice_score: float  # -1 to 1
    text_score: float  # -1 to 1
    combined_score: float  # -1 to 1
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label.value,
            "confidence": round(self.confidence, 3),
            "facial_score": round(self.facial_score, 3),
            "voice_score": round(self.voice_score, 3),
            "text_score": round(self.text_score, 3),
            "combined_score": round(self.combined_score, 3),
            "timestamp": self.timestamp,
            "details": self.details,
        }


# Emotion to valence mapping for DeepFace emotions
_EMOTION_VALENCE = {
    "happy": 0.8,
    "surprise": 0.3,
    "neutral": 0.0,
    "sad": -0.5,
    "angry": -0.7,
    "fear": -0.6,
    "disgust": -0.5,
}

# Voice feature thresholds (librosa-derived)
_VOICE_POSITIVE = {"high_energy": 0.3, "varied_pitch": 0.2, "steady_pace": 0.2}
_VOICE_NEGATIVE = {"low_energy": -0.3, "flat_pitch": -0.2, "rushed_pace": -0.2}

# Text sentiment keywords
_POSITIVE_TEXT = [
    "confident", "excited", "happy", "great", "love", "enjoy", "passionate",
    "strong", "achieve", "success", "accomplish", "proud", "eager",
]
_NEGATIVE_TEXT = [
    "difficult", "hard", "struggle", "confused", "unsure", "worried",
    "nervous", "stress", "overwhelmed", "frustrated", "stuck", "lost",
    "don't know", "not sure", "no idea",
]
_CONFUSED_TEXT = [
    "what do you mean", "can you repeat", "i don't understand",
    "could you clarify", "not clear", "confused", "huh",
]
_ENGAGED_TEXT = [
    "interesting", "let me think", "great question", "actually",
    "for example", "specifically", "in my experience", "i'd say",
]
_DISENGAGED_TEXT = [
    "i guess", "maybe", "whatever", "sure", "okay", "i don't know",
    "not really", "nothing", "pass",
]


class SentimentAnalyzer:
    """Fuses facial emotion, voice emotion, and text sentiment into a
    single real-time sentiment assessment.

    Maintains a rolling window of recent sentiment states for trend detection.

    Args:
        window_seconds: Duration of the rolling window in seconds.
        facial_weight: Weight for facial emotion signal.
        voice_weight: Weight for voice emotion signal.
        text_weight: Weight for text sentiment signal.
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        facial_weight: float = 0.4,
        voice_weight: float = 0.3,
        text_weight: float = 0.3,
    ):
        self.window_seconds = window_seconds
        self.weights = {
            "facial": facial_weight,
            "voice": voice_weight,
            "text": text_weight,
        }
        self._history: Deque[SentimentState] = deque()
        self._shifts: List[Dict[str, Any]] = []

    @property
    def history(self) -> List[SentimentState]:
        """Full sentiment history within the window."""
        self._prune_window()
        return list(self._history)

    @property
    def recent_shifts(self) -> List[Dict[str, Any]]:
        """Detected sentiment shifts."""
        return list(self._shifts)

    def analyze(
        self,
        facial_emotion: Optional[str] = None,
        facial_scores: Optional[Dict[str, float]] = None,
        voice_features: Optional[Dict[str, float]] = None,
        text: Optional[str] = None,
    ) -> SentimentState:
        """Analyze current sentiment from available modalities.

        Args:
            facial_emotion: Dominant emotion from DeepFace (e.g., "happy").
            facial_scores: Full emotion score dict from DeepFace.
            voice_features: Voice feature dict (energy, pitch_var, pace).
            text: Candidate's spoken/typed text for sentiment analysis.

        Returns:
            SentimentState with fused sentiment assessment.
        """
        facial_score = self._analyze_facial(facial_emotion, facial_scores)
        voice_score = self._analyze_voice(voice_features)
        text_score = self._analyze_text(text)

        # Weighted fusion — only include available signals
        available = {}
        if facial_emotion is not None:
            available["facial"] = facial_score
        if voice_features is not None:
            available["voice"] = voice_score
        if text is not None:
            available["text"] = text_score

        if not available:
            combined = 0.0
            confidence = 0.0
        else:
            # Normalize weights for available signals
            total_weight = sum(self.weights[k] for k in available)
            combined = sum(
                available[k] * self.weights[k] / total_weight for k in available
            )
            # Confidence = how many modalities agree and are available
            agreement = self._compute_agreement(available)
            coverage = len(available) / 3.0
            confidence = agreement * coverage

        label = self._classify_sentiment(combined, available, text)

        state = SentimentState(
            label=label,
            confidence=round(min(1.0, max(0.0, confidence)), 3),
            facial_score=round(facial_score, 3),
            voice_score=round(voice_score, 3),
            text_score=round(text_score, 3),
            combined_score=round(combined, 3),
            details={
                "modalities_available": list(available.keys()),
                "facial_emotion": facial_emotion,
            },
        )

        # Detect shifts
        self._detect_shift(state)

        # Add to history
        self._history.append(state)
        self._prune_window()

        return state

    def get_trend(self, last_n: int = 5) -> str:
        """Get the sentiment trend over the last N states.

        Returns:
            "improving", "declining", or "stable".
        """
        states = list(self._history)[-last_n:]
        if len(states) < 3:
            return "stable"

        first_half = states[: len(states) // 2]
        second_half = states[len(states) // 2 :]

        avg_first = sum(s.combined_score for s in first_half) / len(first_half)
        avg_second = sum(s.combined_score for s in second_half) / len(second_half)

        diff = avg_second - avg_first
        if diff > 0.15:
            return "improving"
        elif diff < -0.15:
            return "declining"
        return "stable"

    def get_rolling_average(self) -> float:
        """Get the average sentiment score over the rolling window."""
        self._prune_window()
        if not self._history:
            return 0.0
        return sum(s.combined_score for s in self._history) / len(self._history)

    def reset(self) -> None:
        """Reset all state."""
        self._history.clear()
        self._shifts.clear()

    # ── Internal analysis methods ─────────────────────────────────────

    def _analyze_facial(
        self,
        emotion: Optional[str],
        scores: Optional[Dict[str, float]],
    ) -> float:
        """Convert facial emotion to valence score (-1 to 1)."""
        if emotion is None:
            return 0.0

        valence = _EMOTION_VALENCE.get(emotion.lower(), 0.0)

        # Boost with score confidence if available
        if scores and emotion.lower() in scores:
            confidence = scores[emotion.lower()]
            valence *= min(1.0, 0.5 + confidence)

        return valence

    def _analyze_voice(self, features: Optional[Dict[str, float]]) -> float:
        """Convert voice features to valence score (-1 to 1)."""
        if not features:
            return 0.0

        score = 0.0

        energy = features.get("energy", 0.5)
        pitch_var = features.get("pitch_variation", 0.5)
        pace = features.get("speaking_rate", 1.0)  # words per second normalized

        # High energy + varied pitch = confident/engaged
        if energy > 0.6:
            score += 0.3
        elif energy < 0.3:
            score -= 0.3

        if pitch_var > 0.5:
            score += 0.2
        elif pitch_var < 0.2:
            score -= 0.2

        # Normal speaking pace is ~2-3 words/sec
        if 1.5 <= pace <= 3.5:
            score += 0.1  # Natural pace
        elif pace > 4.0:
            score -= 0.2  # Rushing (nervous)
        elif pace < 1.0:
            score -= 0.3  # Very slow (uncertain)

        return max(-1.0, min(1.0, score))

    def _analyze_text(self, text: Optional[str]) -> float:
        """Simple keyword-based text sentiment analysis."""
        if not text:
            return 0.0

        text_lower = text.lower()
        words = text_lower.split()
        if not words:
            return 0.0

        pos_count = sum(1 for kw in _POSITIVE_TEXT if kw in text_lower)
        neg_count = sum(1 for kw in _NEGATIVE_TEXT if kw in text_lower)
        total = pos_count + neg_count

        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _classify_sentiment(
        self,
        combined: float,
        available: Dict[str, float],
        text: Optional[str],
    ) -> SentimentLabel:
        """Classify the combined sentiment into a label."""
        text_lower = (text or "").lower()

        # Check for specific patterns first
        if any(phrase in text_lower for phrase in _CONFUSED_TEXT):
            return SentimentLabel.CONFUSED

        # Check voice-specific nervousness BEFORE disengaged,
        # since rapid/low-energy speech is a stronger nervous signal
        if "voice" in available:
            voice = available["voice"]
            if voice < -0.4:
                return SentimentLabel.NERVOUS

        if any(phrase in text_lower for phrase in _DISENGAGED_TEXT) and combined < 0:
            return SentimentLabel.DISENGAGED

        if any(phrase in text_lower for phrase in _ENGAGED_TEXT):
            return SentimentLabel.ENGAGED

        # Classify by combined score
        if combined >= 0.4:
            return SentimentLabel.CONFIDENT
        elif combined >= 0.15:
            return SentimentLabel.ENGAGED
        elif combined <= -0.5:
            return SentimentLabel.FRUSTRATED
        elif combined <= -0.25:
            return SentimentLabel.NERVOUS
        elif combined <= -0.1:
            return SentimentLabel.DISENGAGED
        else:
            return SentimentLabel.NEUTRAL

    def _compute_agreement(self, available: Dict[str, float]) -> float:
        """Compute how much the available modalities agree (0-1)."""
        if len(available) < 2:
            return 1.0

        scores = list(available.values())
        signs = [1 if s > 0 else -1 if s < 0 else 0 for s in scores]

        if all(s == signs[0] for s in signs):
            return 1.0

        # Partial agreement
        positive_count = sum(1 for s in signs if s > 0)
        negative_count = sum(1 for s in signs if s < 0)
        max_agreement = max(positive_count, negative_count)
        return max_agreement / len(signs)

    def _detect_shift(self, current: SentimentState) -> None:
        """Detect significant sentiment shifts."""
        self._prune_window()
        if not self._history:
            return

        prev = self._history[-1]
        if prev.label == current.label:
            return

        # Only record meaningful shifts
        score_change = current.combined_score - prev.combined_score
        if abs(score_change) < 0.2:
            return

        shift = {
            "from": prev.label.value,
            "to": current.label.value,
            "score_change": round(score_change, 3),
            "timestamp": current.timestamp,
            "description": f"Candidate shifted from {prev.label.value} to {current.label.value}",
        }
        self._shifts.append(shift)

        # Keep only last 20 shifts
        if len(self._shifts) > 20:
            self._shifts = self._shifts[-20:]

        logger.info(f"Sentiment shift: {shift['description']} (Δ{score_change:+.2f})")

    def _prune_window(self) -> None:
        """Remove states outside the rolling window."""
        cutoff = time.time() - self.window_seconds
        while self._history and self._history[0].timestamp < cutoff:
            self._history.popleft()

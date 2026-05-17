"""Adaptive interview pacer — adjusts flow based on real-time sentiment."""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from modules.pacing.sentiment_analyzer import SentimentLabel, SentimentState

logger = logging.getLogger(__name__)


class PacingActionType(str, Enum):
    """Types of pacing adjustments the pacer can recommend."""
    WARM_UP = "warm_up"
    SLOW_DOWN = "slow_down"
    SPEED_UP = "speed_up"
    CHANGE_TOPIC = "change_topic"
    ENCOURAGE = "encourage"
    REPHRASE = "rephrase"
    GIVE_HINT = "give_hint"
    ASK_BEHAVIORAL = "ask_behavioral"
    INCREASE_DIFFICULTY = "increase_difficulty"
    DECREASE_DIFFICULTY = "decrease_difficulty"
    POSITIVE_REINFORCEMENT = "positive_reinforcement"
    NO_CHANGE = "no_change"


@dataclass
class PacingAction:
    """A recommended pacing adjustment."""
    action_type: PacingActionType
    reason: str
    detail: str = ""
    tts_speed_modifier: float = 1.0  # Multiplier: <1 slower, >1 faster
    tone: str = "neutral"  # "encouraging", "neutral", "energetic"
    skip_to_difficulty: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "reason": self.reason,
            "detail": self.detail,
            "tts_speed_modifier": self.tts_speed_modifier,
            "tone": self.tone,
            "skip_to_difficulty": self.skip_to_difficulty,
            "timestamp": self.timestamp,
        }


# Mapping: sentiment → pacing strategies
_SENTIMENT_STRATEGIES: Dict[SentimentLabel, List[Dict[str, Any]]] = {
    SentimentLabel.NERVOUS: [
        {
            "action": PacingActionType.WARM_UP,
            "reason": "Candidate is nervous — insert warm-up question",
            "detail": "Ask a simple, friendly question to build rapport.",
            "tts_speed": 0.85,
            "tone": "encouraging",
        },
        {
            "action": PacingActionType.SLOW_DOWN,
            "reason": "Candidate is nervous — slowing down TTS speed",
            "detail": "Speak more slowly and clearly to reduce pressure.",
            "tts_speed": 0.8,
            "tone": "encouraging",
        },
    ],
    SentimentLabel.CONFIDENT: [
        {
            "action": PacingActionType.INCREASE_DIFFICULTY,
            "reason": "Candidate is confident — skip easy questions",
            "detail": "Move to higher difficulty to get a better assessment.",
            "tts_speed": 1.0,
            "tone": "neutral",
        },
        {
            "action": PacingActionType.INCREASE_DIFFICULTY,
            "reason": "Candidate is confident — increase difficulty faster",
            "detail": "Ramp up difficulty to challenge the candidate.",
            "tts_speed": 1.1,
            "tone": "neutral",
        },
    ],
    SentimentLabel.FRUSTRATED: [
        {
            "action": PacingActionType.CHANGE_TOPIC,
            "reason": "Candidate seems frustrated — change topic",
            "detail": "Switch to a different area to reset the mood.",
            "tts_speed": 0.9,
            "tone": "encouraging",
        },
        {
            "action": PacingActionType.POSITIVE_REINFORCEMENT,
            "reason": "Candidate seems frustrated — give positive reinforcement",
            "detail": "Acknowledge what they got right before moving on.",
            "tts_speed": 0.9,
            "tone": "encouraging",
        },
    ],
    SentimentLabel.CONFUSED: [
        {
            "action": PacingActionType.REPHRASE,
            "reason": "Candidate seems confused — rephrase the question",
            "detail": "Simplify the question or break it into smaller parts.",
            "tts_speed": 0.85,
            "tone": "encouraging",
        },
        {
            "action": PacingActionType.GIVE_HINT,
            "reason": "Candidate seems confused — give a hint",
            "detail": "Provide a subtle hint to guide their thinking.",
            "tts_speed": 0.85,
            "tone": "encouraging",
        },
    ],
    SentimentLabel.DISENGAGED: [
        {
            "action": PacingActionType.ASK_BEHAVIORAL,
            "reason": "Candidate seems disengaged — ask engaging behavioral question",
            "detail": "Use a story-based question to re-engage.",
            "tts_speed": 1.05,
            "tone": "energetic",
        },
        {
            "action": PacingActionType.CHANGE_TOPIC,
            "reason": "Candidate seems disengaged — change energy",
            "detail": "Switch to a more interesting or personal topic.",
            "tts_speed": 1.1,
            "tone": "energetic",
        },
    ],
    SentimentLabel.ENGAGED: [
        {
            "action": PacingActionType.NO_CHANGE,
            "reason": "Candidate is engaged — continue current flow",
            "detail": "Maintain current pacing and topic.",
            "tts_speed": 1.0,
            "tone": "neutral",
        },
    ],
    SentimentLabel.NEUTRAL: [
        {
            "action": PacingActionType.NO_CHANGE,
            "reason": "Candidate is neutral — no adjustment needed",
            "detail": "Continue with the planned interview flow.",
            "tts_speed": 1.0,
            "tone": "neutral",
        },
    ],
}

# Alias for the key used in strategies
_SENTIMENT_STRATEGIES[SentimentLabel.CONFIDENT].append({
    "action": PacingActionType.SPEED_UP,
    "reason": "Candidate is confident — slightly increase pacing",
    "detail": "Candidate can handle a faster pace.",
    "tts_speed": 1.1,
    "tone": "neutral",
})


class AdaptivePacer:
    """Adjusts interview pacing based on real-time sentiment analysis.

    Monitors sentiment trends and recommends pacing actions such as
    slowing TTS, changing topics, or adjusting difficulty.

    Args:
        sentiment_analyzer: A SentimentAnalyzer instance for current state.
        min_interval: Minimum seconds between pacing adjustments.
        on_action: Optional callback invoked with each PacingAction.
    """

    def __init__(
        self,
        sentiment_analyzer: Any,
        min_interval: float = 15.0,
        on_action: Optional[Callable[[PacingAction], None]] = None,
    ):
        self._analyzer = sentiment_analyzer
        self._min_interval = min_interval
        self._on_action = on_action
        self._last_action_time: float = 0.0
        self._action_log: List[PacingAction] = []
        self._current_difficulty: int = 2  # medium
        self._consecutive_negative: int = 0

    @property
    def action_log(self) -> List[PacingAction]:
        """Full log of pacing actions taken."""
        return list(self._action_log)

    @property
    def current_difficulty(self) -> int:
        """Current adjusted difficulty level."""
        return self._current_difficulty

    def evaluate(self) -> Optional[PacingAction]:
        """Evaluate current sentiment and recommend a pacing action.

        Returns:
            A PacingAction if an adjustment is recommended, None otherwise.
        """
        now = time.time()
        if now - self._last_action_time < self._min_interval:
            return None

        # Get current sentiment from analyzer
        if hasattr(self._analyzer, "history"):
            history = self._analyzer.history
        elif hasattr(self._analyzer, "_history"):
            history = list(self._analyzer._history)
        else:
            return None

        if not history:
            return None

        current_state = history[-1]

        # Track consecutive negative sentiments
        if current_state.combined_score < -0.2:
            self._consecutive_negative += 1
        else:
            self._consecutive_negative = 0

        # Get strategy for the current sentiment
        strategies = _SENTIMENT_STRATEGIES.get(current_state.label, [])

        if not strategies:
            return None

        # Select strategy based on trend
        trend = self._analyzer.get_trend() if hasattr(self._analyzer, "get_trend") else "stable"

        strategy = self._select_strategy(strategies, current_state, trend)

        action = PacingAction(
            action_type=PacingActionType(strategy["action"]),
            reason=strategy["reason"],
            detail=strategy["detail"],
            tts_speed_modifier=strategy.get("tts_speed", 1.0),
            tone=strategy.get("tone", "neutral"),
        )

        # Adjust difficulty if applicable
        if action.action_type == PacingActionType.INCREASE_DIFFICULTY:
            self._current_difficulty = min(4, self._current_difficulty + 1)
            action.skip_to_difficulty = self._current_difficulty
        elif action.action_type == PacingActionType.DECREASE_DIFFICULTY:
            self._current_difficulty = max(1, self._current_difficulty - 1)
            action.skip_to_difficulty = self._current_difficulty

        # Log and notify
        self._action_log.append(action)
        self._last_action_time = now

        if self._on_action:
            try:
                self._on_action(action)
            except Exception as exc:
                logger.error(f"Action callback failed: {exc}")

        logger.info(f"Pacing action: {action.action_type.value} — {action.reason}")
        return action

    def force_difficulty(self, level: int) -> None:
        """Manually set the difficulty level.

        Args:
            level: Difficulty 1-4.
        """
        self._current_difficulty = max(1, min(4, level))
        logger.info(f"Difficulty forced to {self._current_difficulty}")

    def get_analytics(self) -> Dict[str, Any]:
        """Get pacing analytics for the interview.

        Returns:
            Dict with action counts, difficulty progression, etc.
        """
        action_counts: Dict[str, int] = {}
        for action in self._action_log:
            key = action.action_type.value
            action_counts[key] = action_counts.get(key, 0) + 1

        tts_modifiers = [a.tts_speed_modifier for a in self._action_log]
        avg_tts = sum(tts_modifiers) / len(tts_modifiers) if tts_modifiers else 1.0

        return {
            "total_actions": len(self._action_log),
            "action_counts": action_counts,
            "average_tts_modifier": round(avg_tts, 2),
            "current_difficulty": self._current_difficulty,
            "consecutive_negative": self._consecutive_negative,
            "actions": [a.to_dict() for a in self._action_log],
        }

    def reset(self) -> None:
        """Reset pacer state for a new interview."""
        self._last_action_time = 0.0
        self._action_log = []
        self._current_difficulty = 2
        self._consecutive_negative = 0

    # ── Internal ──────────────────────────────────────────────────────

    def _select_strategy(
        self,
        strategies: List[Dict[str, Any]],
        state: SentimentState,
        trend: str,
    ) -> Dict[str, Any]:
        """Select the best strategy based on context."""
        # If sentiment is declining, prefer the first (strongest) strategy
        if trend == "declining" and len(strategies) > 1:
            return strategies[0]

        # If multiple consecutive negatives, escalate
        if self._consecutive_negative >= 3 and len(strategies) > 1:
            return strategies[0]

        # Default: first strategy
        return strategies[0]

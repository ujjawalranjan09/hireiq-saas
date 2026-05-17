"""Adaptive difficulty manager with rolling average."""

import logging
from typing import List, Optional
from app.constants import DifficultyLevel, DIFFICULTY_THRESHOLDS, ROLLING_WINDOW_SIZE

logger = logging.getLogger(__name__)


class DifficultyManager:
    """Manages adaptive difficulty based on candidate performance.
    
    Uses a rolling average of recent answer scores to dynamically
    adjust question difficulty.
    """

    def __init__(self, initial_level: int = DifficultyLevel.MEDIUM):
        """Initialize the difficulty manager.
        
        Args:
            initial_level: Starting difficulty level (1-4).
        """
        self.current_level = initial_level
        self.score_history: List[float] = []
        self.level_history: List[int] = [initial_level]

    def add_score(self, score: float) -> int:
        """Add a new answer score and adjust difficulty if needed.
        
        Args:
            score: The answer score (0-100).
            
        Returns:
            The new difficulty level.
        """
        self.score_history.append(score)
        new_level = self._calculate_level()
        if new_level != self.current_level:
            logger.info(
                f"Difficulty changed: {DifficultyLevel.to_name(self.current_level)} -> "
                f"{DifficultyLevel.to_name(new_level)} (avg={self._rolling_average:.1f})"
            )
            self.current_level = new_level
        self.level_history.append(self.current_level)
        return self.current_level

    def _calculate_level(self) -> int:
        """Calculate the appropriate difficulty level based on rolling average."""
        if len(self.score_history) < 1:
            return self.current_level

        avg = self._rolling_average

        if avg >= DIFFICULTY_THRESHOLDS["increase"]:
            # Candidate doing well - increase difficulty
            return min(self.current_level + 1, DifficultyLevel.EXPERT)
        elif avg < DIFFICULTY_THRESHOLDS["decrease_low"]:
            # Candidate struggling - decrease difficulty
            return max(self.current_level - 1, DifficultyLevel.EASY)
        elif avg < DIFFICULTY_THRESHOLDS["maintain_low"]:
            # Below average but not terrible - consider decreasing
            if self.current_level > DifficultyLevel.MEDIUM:
                return self.current_level - 1
            return self.current_level
        else:
            # In the good range - maintain
            return self.current_level

    @property
    def _rolling_average(self) -> float:
        """Calculate the rolling average of the last N scores."""
        window = self.score_history[-ROLLING_WINDOW_SIZE:]
        if not window:
            return 0.0
        return sum(window) / len(window)

    @property
    def difficulty_name(self) -> str:
        """Get the current difficulty level name."""
        return DifficultyLevel.to_name(self.current_level)

    @property
    def average_score(self) -> float:
        """Get the overall average score."""
        if not self.score_history:
            return 0.0
        return sum(self.score_history) / len(self.score_history)

    def get_stats(self) -> dict:
        """Get difficulty management statistics."""
        return {
            "current_level": self.current_level,
            "current_level_name": self.difficulty_name,
            "rolling_average": round(self._rolling_average, 1),
            "average_score": round(self.average_score, 1),
            "total_scores": len(self.score_history),
            "score_history": self.score_history.copy(),
            "level_history": self.level_history.copy(),
        }

    def reset(self, level: int = DifficultyLevel.MEDIUM) -> None:
        """Reset the difficulty manager.
        
        Args:
            level: Starting difficulty level.
        """
        self.current_level = level
        self.score_history = []
        self.level_history = [level]

"""State machine for interview flow control."""

import logging
from typing import List, Optional, Callable, Dict, Any
from app.constants import InterviewState, STATE_TRANSITIONS

logger = logging.getLogger(__name__)


class StateMachine:
    """Finite state machine for interview flow."""

    def __init__(self):
        """Initialize the state machine."""
        self._current_state = InterviewState.IDLE
        self._history: List[str] = []
        self._listeners: Dict[str, List[Callable]] = {}
        self._transition_count = 0

    @property
    def current_state(self) -> str:
        """Get the current state."""
        return self._current_state

    @property
    def history(self) -> List[str]:
        """Get the state history."""
        return self._history.copy()

    def can_transition(self, target_state: str) -> bool:
        """Check if transition to target state is valid.
        
        Args:
            target_state: The target state to check.
            
        Returns:
            True if transition is allowed.
        """
        allowed = STATE_TRANSITIONS.get(self._current_state, [])
        return target_state in allowed

    def transition(self, target_state: str) -> bool:
        """Attempt to transition to a new state.
        
        Args:
            target_state: The target state.
            
        Returns:
            True if transition succeeded.
        """
        if not self.can_transition(target_state):
            logger.warning(
                f"Invalid transition: {self._current_state} -> {target_state}. "
                f"Allowed: {STATE_TRANSITIONS.get(self._current_state, [])}"
            )
            return False

        old_state = self._current_state
        self._history.append(old_state)
        self._current_state = target_state
        self._transition_count += 1

        logger.info(f"State transition: {old_state} -> {target_state}")
        self._notify_listeners(old_state, target_state)
        return True

    def force_transition(self, target_state: str) -> None:
        """Force a transition without validation.
        
        Args:
            target_state: The target state.
        """
        old_state = self._current_state
        self._history.append(old_state)
        self._current_state = target_state
        self._transition_count += 1

        logger.warning(f"Forced state transition: {old_state} -> {target_state}")
        self._notify_listeners(old_state, target_state)

    def reset(self) -> None:
        """Reset to IDLE state."""
        self._current_state = InterviewState.IDLE
        self._history = []
        self._transition_count = 0
        logger.info("State machine reset to IDLE")

    def on_transition(self, from_state: str, callback: Callable) -> None:
        """Register a listener for state transitions.
        
        Args:
            from_state: State to listen for transitions from ("*" for all).
            callback: Function to call with (old_state, new_state).
        """
        key = from_state if from_state != "*" else "__all__"
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def _notify_listeners(self, old_state: str, new_state: str) -> None:
        """Notify registered listeners of a transition."""
        for callback in self._listeners.get(old_state, []):
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Listener error: {e}")
        for callback in self._listeners.get("__all__", []):
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    @property
    def is_terminal(self) -> bool:
        """Check if current state is terminal."""
        return self._current_state in (InterviewState.COMPLETED, InterviewState.ERROR)

    @property
    def is_active(self) -> bool:
        """Check if interview is in an active state."""
        return self._current_state not in (
            InterviewState.IDLE,
            InterviewState.COMPLETED,
            InterviewState.ERROR,
        )

    def get_next_states(self) -> List[str]:
        """Get list of valid next states."""
        return STATE_TRANSITIONS.get(self._current_state, [])

    def get_stats(self) -> Dict[str, Any]:
        """Get state machine statistics."""
        return {
            "current_state": self._current_state,
            "transition_count": self._transition_count,
            "history_length": len(self._history),
            "is_active": self.is_active,
            "is_terminal": self.is_terminal,
            "next_states": self.get_next_states(),
        }

"""Interviewer Copilot Mode module."""

from modules.copilot.suggestion_engine import SuggestionEngine, CopilotSuggestion
from modules.copilot.copilot_dashboard import render_copilot_dashboard

__all__ = [
    "SuggestionEngine",
    "CopilotSuggestion",
    "render_copilot_dashboard",
]

"""Real-time AI suggestion engine for interviewer copilot mode."""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """Categories of copilot suggestions."""
    FOLLOW_UP = "follow_up"
    PROBE_DEEPER = "probe_deeper"
    REPHRASE = "rephrase"
    STAR_METHOD = "star_method"
    GAP_FILL = "gap_fill"
    ENCOURAGE = "encourage"
    REDIRECT = "redirect"
    SKIP = "skip"
    STRONG_AREA = "strong_area"


@dataclass
class CopilotSuggestion:
    """A single copilot suggestion for the human interviewer."""
    suggestion_type: SuggestionType
    message: str
    detail: str = ""
    priority: int = 5  # 1 (highest) to 10 (lowest)
    topic: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.suggestion_type.value,
            "message": self.message,
            "detail": self.detail,
            "priority": self.priority,
            "topic": self.topic,
            "timestamp": self.timestamp,
        }


# Keywords that indicate STAR method usage
_STAR_KEYWORDS = {
    "situation": ["when i was", "the situation was", "at my previous", "in my role", "when we had"],
    "task": ["i needed to", "my responsibility", "my task was", "i was asked to", "my goal was"],
    "action": ["i decided to", "i implemented", "i took", "i created", "i developed", "i led", "i organized"],
    "result": ["as a result", "the outcome", "we achieved", "we reduced", "we improved", "we increased", "this led to", "the result was"],
}

# Filler / vague indicators
_VAGUE_PHRASES = [
    "i don't know", "not sure", "maybe", "i guess", "kind of",
    "sort of", "basically", "like", "um", "uh", "honestly",
    "i think maybe", "probably", "it depends",
]

# Technical depth indicators
_DEPTH_INDICATORS = [
    "the reason is", "this works because", "the trade-off", "compared to",
    "the complexity is", "internally", "under the hood", "the architecture",
    "optimization", "scalability", "bottleneck", "trade-off",
]


class SuggestionEngine:
    """Generates real-time AI suggestions for a human interviewer.

    Tracks topics covered, analyzes candidate responses, and recommends
    follow-up questions, probing strategies, and pacing adjustments.

    Args:
        required_topics: List of topics that must be covered.
        max_suggestions: Maximum suggestions to keep in the active queue.
        llm_callback: Optional async/sync callable for LLM-powered suggestions.
            Signature: (prompt: str) -> str
    """

    def __init__(
        self,
        required_topics: Optional[List[str]] = None,
        max_suggestions: int = 10,
        llm_callback: Optional[callable] = None,
    ):
        self.required_topics = required_topics or []
        self.max_suggestions = max_suggestions
        self._llm = llm_callback

        self._suggestions: List[CopilotSuggestion] = []
        self._topics_covered: List[str] = []
        self._question_count: int = 0
        self._strong_topics: List[str] = []
        self._weak_topics: List[str] = []
        self._flagged_topics: List[str] = []
        self._score_tracker: List[float] = []
        self._last_analysis_time: float = 0.0

    # ── Public API ────────────────────────────────────────────────────

    @property
    def suggestions(self) -> List[CopilotSuggestion]:
        """Current suggestion queue sorted by priority."""
        return sorted(self._suggestions, key=lambda s: s.priority)

    @property
    def topics_covered(self) -> List[str]:
        """Topics already discussed."""
        return list(self._topics_covered)

    @property
    def coverage_stats(self) -> Dict[str, Any]:
        """Topic coverage statistics."""
        total = len(self.required_topics)
        covered = len([t for t in self.required_topics if t in self._topics_covered])
        return {
            "total_required": total,
            "covered": covered,
            "remaining": total - covered,
            "coverage_pct": round(covered / total * 100, 1) if total > 0 else 100.0,
            "topics_covered": list(self._topics_covered),
            "topics_remaining": [
                t for t in self.required_topics if t not in self._topics_covered
            ],
        }

    def analyze_answer(
        self,
        question: str,
        answer: str,
        score: float,
        detected_skills: Optional[List[str]] = None,
        question_topic: str = "",
    ) -> List[CopilotSuggestion]:
        """Analyze a candidate's answer and generate suggestions.

        Args:
            question: The question that was asked.
            answer: The candidate's answer text.
            score: Answer score (0-100).
            detected_skills: Skills detected in the answer.
            question_topic: Topic category of the question.

        Returns:
            List of new CopilotSuggestion objects.
        """
        new_suggestions: List[CopilotSuggestion] = []
        self._question_count += 1
        self._score_tracker.append(score)

        if question_topic:
            self._topics_covered.append(question_topic)

        answer_lower = answer.lower().strip()

        # 1. Check STAR method for behavioral questions
        if self._is_behavioral_question(question):
            star_suggestions = self._check_star_method(answer_lower)
            new_suggestions.extend(star_suggestions)

        # 2. Detect vague/weak answers
        vague_suggestions = self._check_vagueness(answer_lower, question_topic)
        new_suggestions.extend(vague_suggestions)

        # 3. Strong area detection
        if score >= 80 and detected_skills:
            for skill in detected_skills:
                if skill not in self._strong_topics:
                    self._strong_topics.append(skill)
                    new_suggestions.append(CopilotSuggestion(
                        suggestion_type=SuggestionType.STRONG_AREA,
                        message=f"Candidate is strong in {skill}, probe deeper",
                        detail=f"Scored {score:.0f} on this answer. Consider advanced follow-up.",
                        priority=3,
                        topic=skill,
                    ))

        # 4. Weak area / concept avoidance
        if score < 50:
            topic = question_topic or "this topic"
            if topic not in self._weak_topics:
                self._weak_topics.append(topic)
            new_suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.REPHRASE,
                message=f"Candidate struggled with {topic}, consider rephrasing",
                detail=f"Score: {score:.0f}. Try a simpler angle or give a hint.",
                priority=2,
                topic=topic,
            ))

        # 5. Check for concept avoidance (very short or deflective answers)
        if self._is_deflective(answer_lower):
            new_suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.REPHRASE,
                message=f"Candidate may have avoided {question_topic or 'the core concept'}, consider rephrasing",
                detail="Answer was short or deflective. Try asking for a specific example.",
                priority=2,
                topic=question_topic,
            ))

        # 6. Low score consecutive check
        if len(self._score_tracker) >= 3 and all(s < 45 for s in self._score_tracker[-3:]):
            new_suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.REDIRECT,
                message="Candidate struggling — consider changing topic",
                detail="Last 3 scores were below 45. Moving to a different area may help.",
                priority=1,
            ))

        # 7. Depth check for technical answers
        if score >= 60 and not self._has_technical_depth(answer_lower):
            new_suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.PROBE_DEEPER,
                message="Answer is correct but shallow — ask for deeper explanation",
                detail="Candidate gave a surface-level answer. Ask about trade-offs or internals.",
                priority=4,
                topic=question_topic,
            ))

        # 8. Generate LLM-powered suggestion if available
        if self._llm:
            try:
                llm_suggestion = self._generate_llm_suggestion(question, answer, score)
                if llm_suggestion:
                    new_suggestions.append(llm_suggestion)
            except Exception as exc:
                logger.debug(f"LLM suggestion failed: {exc}")

        # Add to queue and trim
        self._suggestions.extend(new_suggestions)
        self._suggestions = sorted(self._suggestions, key=lambda s: s.priority)[:self.max_suggestions]
        self._last_analysis_time = time.time()

        return new_suggestions

    def suggest_next_question(self) -> Optional[CopilotSuggestion]:
        """Suggest the next best question based on uncovered topics.

        Returns:
            A suggestion for the next topic, or None if all covered.
        """
        remaining = [
            t for t in self.required_topics
            if t not in self._topics_covered and t not in self._flagged_topics
        ]

        if not remaining:
            return None

        # Prioritize weak topics first
        for topic in self._weak_topics:
            if topic in remaining:
                return CopilotSuggestion(
                    suggestion_type=SuggestionType.GAP_FILL,
                    message=f"Next topic: {topic} (weak area — address early)",
                    detail="This topic showed weakness in earlier answers.",
                    priority=1,
                    topic=topic,
                )

        # Then normal remaining topics
        next_topic = remaining[0]
        return CopilotSuggestion(
            suggestion_type=SuggestionType.GAP_FILL,
            message=f"Next topic: {next_topic} ({len(remaining)} topics remaining)",
            detail=f"Remaining: {', '.join(remaining[:5])}",
            priority=3,
            topic=next_topic,
        )

    def mark_topic_strong(self, topic: str) -> None:
        """Mark a topic as a strong area for the candidate."""
        if topic not in self._strong_topics:
            self._strong_topics.append(topic)
        logger.info(f"Marked '{topic}' as strong")

    def flag_concern(self, topic: str, reason: str = "") -> None:
        """Flag a topic as a concern."""
        if topic not in self._flagged_topics:
            self._flagged_topics.append(topic)
        self._suggestions.append(CopilotSuggestion(
            suggestion_type=SuggestionType.REDIRECT,
            message=f"⚠️ Flagged concern: {topic}",
            detail=reason or "Human interviewer flagged this topic.",
            priority=1,
            topic=topic,
        ))

    def skip_topic(self, topic: str) -> None:
        """Skip a topic and add it to covered."""
        if topic not in self._topics_covered:
            self._topics_covered.append(topic)
        self._suggestions.append(CopilotSuggestion(
            suggestion_type=SuggestionType.SKIP,
            message=f"Skipped: {topic}",
            detail="Human interviewer chose to skip this topic.",
            priority=7,
            topic=topic,
        ))

    def get_candidate_scorecard(self) -> Dict[str, Any]:
        """Get the current candidate scorecard.

        Returns:
            Dict with scores, trends, and assessment.
        """
        if not self._score_tracker:
            return {
                "average": 0.0,
                "trend": "neutral",
                "questions_answered": 0,
                "assessment": "No data yet",
            }

        avg = sum(self._score_tracker) / len(self._score_tracker)

        # Trend: compare last 3 to first 3
        trend = "neutral"
        if len(self._score_tracker) >= 6:
            first_half = sum(self._score_tracker[:3]) / 3
            second_half = sum(self._score_tracker[-3:]) / 3
            diff = second_half - first_half
            if diff > 10:
                trend = "improving"
            elif diff < -10:
                trend = "declining"

        if avg >= 80:
            assessment = "Strong candidate — consistently high performance"
        elif avg >= 60:
            assessment = "Solid candidate — good overall with some gaps"
        elif avg >= 40:
            assessment = "Mixed performance — significant areas for growth"
        else:
            assessment = "Below expectations — major gaps identified"

        return {
            "average": round(avg, 1),
            "latest": self._score_tracker[-1],
            "min": min(self._score_tracker),
            "max": max(self._score_tracker),
            "trend": trend,
            "questions_answered": self._question_count,
            "assessment": assessment,
            "strong_topics": list(self._strong_topics),
            "weak_topics": list(self._weak_topics),
            "flagged_topics": list(self._flagged_topics),
        }

    def reset(self) -> None:
        """Reset all state for a new interview."""
        self._suggestions = []
        self._topics_covered = []
        self._question_count = 0
        self._strong_topics = []
        self._weak_topics = []
        self._flagged_topics = []
        self._score_tracker = []
        self._last_analysis_time = 0.0

    # ── Internal analysis ─────────────────────────────────────────────

    def _is_behavioral_question(self, question: str) -> bool:
        """Check if a question is behavioral (asks for examples/stories)."""
        behavioral_signals = [
            "tell me about a time", "describe a situation", "give an example",
            "how did you handle", "describe a time", "share an experience",
            "when have you", "what would you do if",
        ]
        q_lower = question.lower()
        return any(sig in q_lower for sig in behavioral_signals)

    def _check_star_method(self, answer: str) -> List[CopilotSuggestion]:
        """Check if answer uses the STAR method."""
        components_found = {}
        for component, keywords in _STAR_KEYWORDS.items():
            if any(kw in answer for kw in keywords):
                components_found[component] = True

        missing = [c for c in ["situation", "task", "action", "result"] if c not in components_found]

        suggestions = []
        if len(missing) >= 2:
            missing_str = ", ".join(missing)
            suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.STAR_METHOD,
                message="STAR method not fully used — suggest asking for specific example",
                detail=f"Missing components: {missing_str}. Guide candidate to structure their answer.",
                priority=2,
            ))
        elif "result" in missing:
            suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.STAR_METHOD,
                message="Ask for the result/outcome of their example",
                detail="Candidate described situation and action but didn't state the result.",
                priority=3,
            ))

        return suggestions

    def _check_vagueness(self, answer: str, topic: str) -> List[CopilotSuggestion]:
        """Detect vague or unclear answers."""
        vague_count = sum(1 for phrase in _VAGUE_PHRASES if phrase in answer)
        word_count = len(answer.split())

        suggestions = []
        if vague_count >= 3 and word_count < 50:
            suggestions.append(CopilotSuggestion(
                suggestion_type=SuggestionType.REPHRASE,
                message=f"Answer seems vague — consider rephrasing the question on {topic or 'this topic'}",
                detail=f"Detected {vague_count} vague phrases in a {word_count}-word answer.",
                priority=3,
                topic=topic,
            ))

        return suggestions

    def _is_deflective(self, answer: str) -> bool:
        """Check if an answer is very short or deflective."""
        word_count = len(answer.split())
        if word_count < 15:
            return True
        deflective_patterns = [
            r"^i (haven't|don't|can't|wouldn't)",
            r"^not (really|applicable)",
            r"^no[,.\s]",
            r"^nothing (comes to mind|specific)",
        ]
        return any(re.match(p, answer) for p in deflective_patterns)

    def _has_technical_depth(self, answer: str) -> bool:
        """Check if a technical answer has sufficient depth."""
        depth_count = sum(1 for ind in _DEPTH_INDICATORS if ind in answer)
        word_count = len(answer.split())
        return depth_count >= 2 or word_count >= 100

    def _generate_llm_suggestion(
        self, question: str, answer: str, score: float
    ) -> Optional[CopilotSuggestion]:
        """Generate a suggestion using the LLM callback."""
        prompt = (
            "You are an AI copilot assisting a human interviewer. "
            "Based on the candidate's answer, suggest ONE follow-up action.\n\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Score: {score}/100\n\n"
            "Respond with a single actionable suggestion in 1-2 sentences. "
            "Be specific and concise."
        )
        response = self._llm(prompt)
        if response and len(response.strip()) > 10:
            return CopilotSuggestion(
                suggestion_type=SuggestionType.FOLLOW_UP,
                message=response.strip(),
                priority=4,
            )
        return None

"""Personalized coaching plan generator based on interview weak areas."""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from modules.coaching.resource_recommender import ResourceRecommender, Resource

logger = logging.getLogger(__name__)


@dataclass
class TopicPlan:
    """Study plan for a single weak topic."""
    topic: str
    current_level: str  # "beginner", "intermediate", "advanced"
    target_level: str
    gap_description: str
    resources: List[Resource] = field(default_factory=list)
    practice_exercises: List[str] = field(default_factory=list)
    estimated_time: str = "1-2 weeks"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "current_level": self.current_level,
            "target_level": self.target_level,
            "gap_description": self.gap_description,
            "resources": [r.to_dict() for r in self.resources],
            "practice_exercises": self.practice_exercises,
            "estimated_time": self.estimated_time,
        }


@dataclass
class StudyPlan:
    """Complete post-interview study plan."""
    candidate_name: str
    overall_score: float
    weak_topics: List[TopicPlan] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    one_week_plan: str = ""
    one_month_plan: str = ""
    three_month_plan: str = ""
    coaching_advice: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "overall_score": self.overall_score,
            "weak_topics": [t.to_dict() for t in self.weak_topics],
            "strong_topics": self.strong_topics,
            "one_week_plan": self.one_week_plan,
            "one_month_plan": self.one_month_plan,
            "three_month_plan": self.three_month_plan,
            "coaching_advice": self.coaching_advice,
        }


class CoachingPlanGenerator:
    """Generates personalized study plans based on interview performance.

    Uses interview scores, identified weak areas, and resource database
    to produce actionable improvement roadmaps.

    Args:
        resource_recommender: Optional ResourceRecommender instance.
        llm_callback: Optional callable for LLM-generated coaching advice.
            Signature: (prompt: str) -> str
    """

    def __init__(
        self,
        resource_recommender: Optional[ResourceRecommender] = None,
        llm_callback: Optional[callable] = None,
    ):
        self._resources = resource_recommender or ResourceRecommender()
        self._llm = llm_callback
        self._openai_key = os.getenv("OPENAI_API_KEY", "")

    @property
    def has_llm(self) -> bool:
        """Whether LLM-based advice generation is available."""
        return bool(self._llm or self._openai_key)

    def generate_plan(
        self,
        candidate_name: str,
        question_results: List[Dict[str, Any]],
        overall_score: float,
        strong_topics: Optional[List[str]] = None,
        weak_topics_override: Optional[List[str]] = None,
    ) -> StudyPlan:
        """Generate a complete study plan based on interview results.

        Args:
            candidate_name: Name of the candidate.
            question_results: List of question result dicts with at least:
                - question_text, question_type, target_skill, answer_score
            overall_score: Overall interview score (0-100).
            strong_topics: Optional list of known strong topics.
            weak_topics_override: Optional manual override of weak topics.

        Returns:
            StudyPlan with topic plans, timelines, and coaching advice.
        """
        # Identify weak topics
        if weak_topics_override:
            weak_areas = [
                {"topic": t, "score": 0, "description": "Manually identified"}
                for t in weak_topics_override
            ]
        else:
            weak_areas = self._extract_weak_areas(question_results)

        # Identify strong topics
        if strong_topics:
            strong = strong_topics
        else:
            strong = self._extract_strong_areas(question_results)

        # Build topic plans
        topic_plans: List[TopicPlan] = []
        for area in weak_areas:
            topic = area["topic"]
            score = area.get("score", 30)

            current_level = self._score_to_level(score)
            target_level = self._target_level(current_level)

            # Get resources for this topic
            resources = self._resources.recommend(
                topic=topic,
                current_level=current_level,
                max_results=4,
            )

            # Generate practice exercises
            exercises = self._generate_exercises(topic, current_level)

            # Estimate time
            estimated = self._estimate_time(current_level, target_level)

            topic_plans.append(TopicPlan(
                topic=topic,
                current_level=current_level,
                target_level=target_level,
                gap_description=area.get("description", f"Scored {score:.0f}/100 on {topic}"),
                resources=resources,
                practice_exercises=exercises,
                estimated_time=estimated,
            ))

        # Generate timeline plans
        one_week = self._generate_weekly_plan(topic_plans, "1 week")
        one_month = self._generate_weekly_plan(topic_plans, "1 month")
        three_month = self._generate_weekly_plan(topic_plans, "3 months")

        # Generate coaching advice
        coaching = self._generate_coaching_advice(
            candidate_name, overall_score, topic_plans, strong
        )

        return StudyPlan(
            candidate_name=candidate_name,
            overall_score=overall_score,
            weak_topics=topic_plans,
            strong_topics=strong,
            one_week_plan=one_week,
            one_month_plan=one_month,
            three_month_plan=three_month,
            coaching_advice=coaching,
        )

    # ── Internal methods ──────────────────────────────────────────────

    def _extract_weak_areas(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract weak areas from question results."""
        skill_scores: Dict[str, List[float]] = {}

        for r in results:
            skill = r.get("target_skill") or r.get("question_type", "general")
            score = r.get("answer_score", 0)
            if skill not in skill_scores:
                skill_scores[skill] = []
            skill_scores[skill].append(score)

        weak = []
        for skill, scores in skill_scores.items():
            avg = sum(scores) / len(scores)
            if avg < 65:  # Below "good" threshold
                weak.append({
                    "topic": skill,
                    "score": avg,
                    "description": f"Average score of {avg:.0f}/100 across {len(scores)} questions on {skill}",
                })

        # Sort by score ascending (worst first)
        weak.sort(key=lambda x: x["score"])
        return weak[:8]  # Cap at 8 weak areas

    def _extract_strong_areas(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract strong areas from question results."""
        skill_scores: Dict[str, List[float]] = {}

        for r in results:
            skill = r.get("target_skill") or r.get("question_type", "general")
            score = r.get("answer_score", 0)
            if skill not in skill_scores:
                skill_scores[skill] = []
            skill_scores[skill].append(score)

        strong = []
        for skill, scores in skill_scores.items():
            avg = sum(scores) / len(scores)
            if avg >= 75:
                strong.append(skill)

        return sorted(strong)

    @staticmethod
    def _score_to_level(score: float) -> str:
        """Convert a score to a skill level."""
        if score >= 70:
            return "intermediate"
        elif score >= 40:
            return "beginner"
        else:
            return "beginner"

    @staticmethod
    def _target_level(current: str) -> str:
        """Determine the target level to aim for."""
        mapping = {
            "beginner": "intermediate",
            "intermediate": "advanced",
            "advanced": "expert",
        }
        return mapping.get(current, "advanced")

    def _generate_exercises(self, topic: str, level: str) -> List[str]:
        """Generate practice exercises for a topic and level."""
        exercises_db = {
            "beginner": [
                f"Complete 5 basic {topic} tutorials on a learning platform",
                f"Build a small project using {topic} fundamentals",
                f"Read the official {topic} documentation introduction",
                f"Practice {topic} concepts with interactive exercises (e.g., Exercism, Codewars)",
                f"Watch a {topic} crash course and code along",
            ],
            "intermediate": [
                f"Solve 10 intermediate {topic} problems on LeetCode or HackerRank",
                f"Build a real-world application using {topic}",
                f"Contribute to an open-source {topic} project",
                f"Implement common {topic} patterns from scratch",
                f"Write unit tests for a {topic} module",
            ],
            "advanced": [
                f"Solve 15 hard {topic} problems focusing on optimization",
                f"Design and architect a system using {topic} at scale",
                f"Write a blog post explaining advanced {topic} concepts",
                f"Conduct a code review of a production {topic} system",
                f"Mentor someone in {topic} to deepen your understanding",
            ],
        }

        level_exercises = exercises_db.get(level, exercises_db["intermediate"])
        return level_exercises[:3]

    @staticmethod
    def _estimate_time(current: str, target: str) -> str:
        """Estimate time to progress from current to target level."""
        levels = ["beginner", "intermediate", "advanced", "expert"]
        current_idx = levels.index(current) if current in levels else 0
        target_idx = levels.index(target) if target in levels else 1
        gap = target_idx - current_idx

        if gap <= 0:
            return "1 week (maintenance)"
        elif gap == 1:
            return "2-4 weeks"
        else:
            return f"{gap * 3}-{gap * 5} weeks"

    def _generate_weekly_plan(self, topic_plans: List[TopicPlan], horizon: str) -> str:
        """Generate a text plan for a given time horizon."""
        if not topic_plans:
            return "No weak areas identified — maintain current skills with regular practice."

        if horizon == "1 week":
            return self._one_week_plan(topic_plans)
        elif horizon == "1 month":
            return self._one_month_plan(topic_plans)
        else:
            return self._three_month_plan(topic_plans)

    def _one_week_plan(self, topics: List[TopicPlan]) -> str:
        """1-week sprint plan."""
        lines = ["**1-Week Improvement Sprint**\n"]
        # Focus on top 2 worst topics
        focus_topics = topics[:2]
        for i, topic in enumerate(focus_topics, 1):
            lines.append(f"**Days {1 + (i-1)*3}-{3 + (i-1)*3}: {topic.topic}**")
            lines.append(f"- Level: {topic.current_level} → {topic.target_level}")
            if topic.resources:
                lines.append(f"- Start with: {topic.resources[0].title}")
            if topic.practice_exercises:
                lines.append(f"- Practice: {topic.practice_exercises[0]}")
            lines.append("")

        lines.append("**Days 6-7: Review & Practice**")
        lines.append("- Review what you learned")
        lines.append("- Take a practice interview or mock technical assessment")
        return "\n".join(lines)

    def _one_month_plan(self, topics: List[TopicPlan]) -> str:
        """1-month improvement plan."""
        lines = ["**1-Month Improvement Plan**\n"]
        for i, topic in enumerate(topics[:4], 1):
            week_start = (i - 1) * 7 + 1
            week_end = min(i * 7, 30)
            lines.append(f"**Week {i} (Days {week_start}-{week_end}): {topic.topic}**")
            lines.append(f"- Current: {topic.current_level} | Target: {topic.target_level}")
            for r in topic.resources[:2]:
                lines.append(f"- 📚 {r.title} ({r.type})")
            for ex in topic.practice_exercises[:2]:
                lines.append(f"- 💻 {ex}")
            lines.append("")

        return "\n".join(lines)

    def _three_month_plan(self, topics: List[TopicPlan]) -> str:
        """3-month comprehensive improvement plan."""
        lines = ["**3-Month Comprehensive Improvement Roadmap**\n"]

        lines.append("**Month 1: Foundation Building**")
        for topic in topics[:3]:
            lines.append(f"- {topic.topic}: Master {topic.target_level} concepts")
            if topic.resources:
                lines.append(f"  Resource: {topic.resources[0].title}")
        lines.append("")

        lines.append("**Month 2: Applied Practice**")
        for topic in topics[2:5]:
            lines.append(f"- {topic.topic}: Build projects and solve problems")
            if topic.practice_exercises:
                lines.append(f"  Exercise: {topic.practice_exercises[0]}")
        lines.append("")

        lines.append("**Month 3: Mastery & Interview Prep**")
        lines.append("- Mock interviews covering all weak areas")
        lines.append("- Review and fill remaining gaps")
        lines.append("- Practice explaining concepts out loud")
        lines.append("- Time-boxed problem solving sessions")

        return "\n".join(lines)

    def _generate_coaching_advice(
        self,
        name: str,
        score: float,
        topic_plans: List[TopicPlan],
        strong_topics: List[str],
    ) -> str:
        """Generate natural language coaching advice."""
        if self.has_llm:
            return self._generate_llm_advice(name, score, topic_plans, strong_topics)
        return self._generate_template_advice(name, score, topic_plans, strong_topics)

    def _generate_llm_advice(
        self,
        name: str,
        score: float,
        topic_plans: List[TopicPlan],
        strong_topics: List[str],
    ) -> str:
        """Generate coaching advice using LLM."""
        weak_summary = "\n".join(
            f"- {tp.topic}: {tp.current_level} level (target: {tp.target_level})"
            for tp in topic_plans
        )
        strong_summary = ", ".join(strong_topics) if strong_topics else "None identified"

        prompt = (
            f"You are an expert career coach and technical mentor. "
            f"Give personalized, encouraging coaching advice to {name}.\n\n"
            f"Interview Score: {score:.0f}/100\n"
            f"Strong Areas: {strong_summary}\n"
            f"Areas for Growth:\n{weak_summary}\n\n"
            f"Write 2-3 paragraphs of natural, warm coaching advice. "
            f"Be specific about what they should focus on and why. "
            f"Acknowledge their strengths. Be motivating but honest."
        )

        # Try OpenAI API
        if self._openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self._openai_key)
                resp = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=[
                        {"role": "system", "content": "You are a warm, encouraging career coach."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.8,
                    max_tokens=500,
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning(f"LLM coaching advice failed: {exc}")

        # Try callback
        if self._llm:
            try:
                return self._llm(prompt)
            except Exception:
                pass

        return self._generate_template_advice(name, score, topic_plans, strong_topics)

    @staticmethod
    def _generate_template_advice(
        name: str,
        score: float,
        topic_plans: List[TopicPlan],
        strong_topics: List[str],
    ) -> str:
        """Generate coaching advice from templates."""
        parts: List[str] = []

        # Opening
        if score >= 70:
            parts.append(
                f"Great job, {name}! You scored {score:.0f}/100, which shows solid knowledge. "
                f"Your strengths in {', '.join(strong_topics[:3]) if strong_topics else 'several areas'} "
                f"are impressive and set a strong foundation."
            )
        elif score >= 50:
            parts.append(
                f"{name}, you scored {score:.0f}/100, which is a decent starting point. "
                f"You showed competence in {', '.join(strong_topics[:2]) if strong_topics else 'some areas'}, "
                f"and there's clear room for targeted improvement."
            )
        else:
            parts.append(
                f"{name}, your score of {score:.0f}/100 indicates significant areas to work on, "
                f"but don't be discouraged — focused effort on the right topics can make a big difference."
            )

        # Focus areas
        if topic_plans:
            worst = topic_plans[0]
            parts.append(
                f"I'd recommend starting with {worst.topic} — it's an area where structured learning "
                f"can move you from {worst.current_level} to {worst.target_level} in about {worst.estimated_time}. "
                f"{'Check out ' + worst.resources[0].title + ' to get started.' if worst.resources else 'Start with hands-on practice.'}"
            )

        # Closing
        parts.append(
            "Consistency is key — even 30 minutes of focused practice daily adds up quickly. "
            "Set specific, measurable goals for each week, and don't hesitate to revisit fundamentals. "
            "You've got this!"
        )

        return "\n\n".join(parts)

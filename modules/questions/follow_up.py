"""Dynamic follow-up question generation based on answer analysis."""

import logging
import random
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def should_generate_followup(
    answer_score: float,
    follow_up_probability: float = 0.3,
    max_followups: int = 2,
    current_followups: int = 0,
) -> bool:
    """Determine whether to generate a follow-up question.
    
    Args:
        answer_score: Score of the current answer (0-100).
        follow_up_probability: Base probability of generating a follow-up.
        max_followups: Maximum follow-ups per question.
        current_followups: Number of follow-ups already asked.
        
    Returns:
        True if a follow-up should be generated.
    """
    if current_followups >= max_followups:
        return False

    # Adjust probability based on score
    # Very low or very high scores get higher follow-up probability
    if answer_score < 40:
        adjusted_prob = follow_up_probability * 1.5
    elif answer_score > 85:
        adjusted_prob = follow_up_probability * 1.2
    else:
        adjusted_prob = follow_up_probability

    return random.random() < min(adjusted_prob, 0.8)


def generate_followup(
    question: str,
    answer: str,
    score: float,
    skills: List[str] = None,
    question_type: str = "technical",
) -> Dict[str, Any]:
    """Generate a follow-up question based on the candidate's answer.
    
    Args:
        question: The original question asked.
        answer: The candidate's answer text.
        score: Score of the answer (0-100).
        skills: Candidate's skills for context.
        question_type: Type of the original question.
        
    Returns:
        Dictionary with follow-up question text and metadata.
    """
    # Try LLM generation first
    try:
        return _generate_followup_llm(question, answer, score, question_type)
    except Exception as e:
        logger.warning(f"LLM follow-up generation failed, using templates: {e}")
        return _generate_followup_template(question, answer, score, skills, question_type)


def _generate_followup_llm(
    question: str,
    answer: str,
    score: float,
    question_type: str,
) -> Dict[str, Any]:
    """Generate follow-up using OpenAI API."""
    from app.config import OPENAI_API_KEY, OPENAI_MODEL
    from app.constants import FOLLOWUP_PROMPT

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = FOLLOWUP_PROMPT.format(
        question=question,
        answer=answer[:500],  # Truncate long answers
        score=score,
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a technical interviewer. Generate a concise follow-up question that probes deeper understanding."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=200,
    )

    followup_text = response.choices[0].message.content or ""
    followup_text = followup_text.strip().strip('"').strip("'")

    return {
        "question_text": followup_text,
        "question_type": question_type,
        "difficulty": _infer_followup_difficulty(score),
        "is_followup": True,
    }


def _generate_followup_template(
    question: str,
    answer: str,
    score: float,
    skills: List[str] = None,
    question_type: str = "technical",
) -> Dict[str, Any]:
    """Generate follow-up using templates."""
    difficulty = _infer_followup_difficulty(score)

    if score < 40:
        # Low score - ask for clarification or simpler version
        templates = [
            "Could you elaborate a bit more on that? Perhaps walk me through a specific example.",
            "I'd like to understand better - can you explain that in simpler terms?",
            "Let me rephrase: can you describe a practical use case for what you just mentioned?",
            "That's a good start. Can you go deeper into how that actually works under the hood?",
        ]
    elif score > 85:
        # High score - challenge with harder follow-up
        templates = [
            "Great answer! Now, what would happen if the requirements changed significantly? How would you adapt?",
            "Excellent. Can you describe the potential pitfalls or edge cases with that approach?",
            "That's well explained. How would you handle scaling that solution to 10x the current load?",
            "Very thorough. What alternative approaches did you consider, and why did you choose this one?",
        ]
    else:
        # Medium score - probe deeper
        templates = [
            "Can you walk me through the specific steps you'd take to implement that?",
            "What trade-offs did you consider when making that decision?",
            "How would you test or validate that approach?",
            "Can you give a concrete example from your experience?",
        ]

    followup_text = random.choice(templates)

    # If the answer mentions specific technologies, try to reference them
    if skills:
        for skill in skills:
            if skill.lower() in answer.lower():
                followup_text += f" Especially in the context of {skill}."
                break

    return {
        "question_text": followup_text,
        "question_type": question_type,
        "difficulty": difficulty,
        "is_followup": True,
    }


def _infer_followup_difficulty(score: float) -> str:
    """Infer follow-up difficulty based on answer score.
    
    High scores get harder follow-ups, low scores get easier ones.
    """
    if score >= 85:
        return "hard"
    elif score >= 60:
        return "medium"
    else:
        return "easy"

"""Answer evaluation orchestrator - composite scoring."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def evaluate_answer(
    question: str,
    answer: str,
    reference_answer: str = "",
    keywords: List[str] = None,
    concepts: List[str] = None,
    question_type: str = "technical",
) -> Dict[str, Any]:
    """Evaluate a candidate's answer using composite scoring.
    
    Score = 0.4 * Semantic + 0.3 * Keywords + 0.3 * Concepts + modifiers
    
    Args:
        question: The interview question.
        answer: The candidate's answer.
        reference_answer: A reference/ideal answer for comparison.
        keywords: Expected keywords to look for.
        concepts: Expected concepts to check coverage.
        question_type: Type of question (resume/technical/behavioral).
        
    Returns:
        Dictionary with overall score and breakdown.
    """
    from app.config import ANSWER_WEIGHTS

    if not answer or not answer.strip():
        return {
            "total_score": 0.0,
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "concept_score": 0.0,
            "modifiers": {},
            "feedback": "No answer provided.",
        }

    # Calculate individual scores
    semantic_score = _calculate_semantic_score(question, answer, reference_answer)
    keyword_score = _calculate_keyword_score(answer, keywords or [])
    concept_score = _calculate_concept_score(answer, concepts or [])

    # Calculate modifiers
    modifiers = _calculate_modifiers(answer)

    # Weighted total
    total = (
        ANSWER_WEIGHTS["semantic"] * semantic_score +
        ANSWER_WEIGHTS["keywords"] * keyword_score +
        ANSWER_WEIGHTS["concepts"] * concept_score
    )

    # Apply modifiers
    total += modifiers.get("total_modifier", 0.0)

    # Clamp to 0-100
    total = max(0.0, min(100.0, total))

    # Generate feedback
    feedback = _generate_feedback(total, semantic_score, keyword_score, concept_score)

    return {
        "total_score": round(total, 1),
        "semantic_score": round(semantic_score, 1),
        "keyword_score": round(keyword_score, 1),
        "concept_score": round(concept_score, 1),
        "modifiers": modifiers,
        "feedback": feedback,
    }


def _calculate_semantic_score(question: str, answer: str, reference: str) -> float:
    """Calculate semantic similarity score (0-100)."""
    from modules.evaluation.semantic_scorer import compute_similarity

    if reference:
        # Compare answer to reference answer
        similarity = compute_similarity(answer, reference)
    else:
        # Compare answer relevance to question
        similarity = compute_similarity(question, answer)

    return similarity * 100


def _calculate_keyword_score(answer: str, keywords: List[str]) -> float:
    """Calculate keyword match score (0-100)."""
    if not keywords:
        # If no keywords provided, give moderate score based on answer length
        word_count = len(answer.split())
        if word_count < 10:
            return 20.0
        elif word_count < 30:
            return 50.0
        return 60.0

    answer_lower = answer.lower()
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return (matched / len(keywords)) * 100


def _calculate_concept_score(answer: str, concepts: List[str]) -> float:
    """Calculate concept coverage score (0-100)."""
    if not concepts:
        # Assess depth based on answer characteristics
        score = 40.0
        word_count = len(answer.split())
        if word_count > 50:
            score += 20
        if word_count > 100:
            score += 10
        # Check for technical depth indicators
        depth_indicators = [
            "because", "therefore", "however", "specifically",
            "for example", "such as", "in other words", "the reason",
            "trade-off", "advantage", "disadvantage", "approach",
            "implementation", "architecture", "design pattern",
        ]
        answer_lower = answer.lower()
        depth_count = sum(1 for ind in depth_indicators if ind in answer_lower)
        score += min(30, depth_count * 5)
        return min(100.0, score)

    answer_lower = answer.lower()
    covered = sum(1 for concept in concepts if concept.lower() in answer_lower)
    return (covered / len(concepts)) * 100


def _calculate_modifiers(answer: str) -> Dict[str, Any]:
    """Calculate score modifiers based on answer quality.
    
    Returns:
        Dictionary with modifier breakdown.
    """
    total_modifier = 0.0
    details = {}

    word_count = len(answer.split())

    # Length modifier: very short answers are penalized
    if word_count < 5:
        length_mod = -15.0
    elif word_count < 15:
        length_mod = -5.0
    elif word_count > 200:
        length_mod = 5.0  # Detailed answers get a small bonus
    else:
        length_mod = 0.0
    total_modifier += length_mod
    details["length_modifier"] = length_mod

    # Structure modifier: answers with structure (lists, steps) get bonus
    structure_indicators = ["1.", "2.", "first", "second", "finally", "step"]
    answer_lower = answer.lower()
    structure_count = sum(1 for ind in structure_indicators if ind in answer_lower)
    if structure_count >= 2:
        structure_mod = 5.0
    else:
        structure_mod = 0.0
    total_modifier += structure_mod
    details["structure_modifier"] = structure_mod

    # Hesitation modifier: filler words indicate uncertainty
    fillers = ["um", "uh", "like", "you know", "basically", "i mean"]
    filler_count = sum(answer_lower.count(f) for f in fillers)
    filler_ratio = filler_count / max(word_count, 1)
    if filler_ratio > 0.1:
        hesitation_mod = -10.0
    elif filler_ratio > 0.05:
        hesitation_mod = -5.0
    else:
        hesitation_mod = 0.0
    total_modifier += hesitation_mod
    details["hesitation_modifier"] = hesitation_mod

    details["total_modifier"] = round(total_modifier, 1)
    return details


def _generate_feedback(
    total: float,
    semantic: float,
    keyword: float,
    concept: float,
) -> str:
    """Generate brief text feedback based on scores."""
    parts = []

    if total >= 85:
        parts.append("Excellent answer!")
    elif total >= 70:
        parts.append("Good answer.")
    elif total >= 55:
        parts.append("Acceptable answer.")
    elif total >= 40:
        parts.append("Below average answer.")
    else:
        parts.append("Needs improvement.")

    if keyword < 40:
        parts.append("Consider using more relevant technical terms.")
    if concept < 40:
        parts.append("Try to cover more key concepts in your answer.")
    if semantic < 40:
        parts.append("Your answer could be more relevant to the question.")

    return " ".join(parts)

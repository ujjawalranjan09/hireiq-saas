"""Question generator using OpenAI API with template fallback."""

import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_questions(
    skills: List[str],
    projects: List[str],
    difficulty: str = "medium",
    count: int = 10,
    question_types: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Generate interview questions based on candidate profile.
    
    Args:
        skills: List of candidate's skills.
        projects: List of candidate's projects.
        difficulty: Difficulty level (easy, medium, hard, expert).
        count: Number of questions to generate.
        question_types: Distribution of question types {type: weight}.
        
    Returns:
        List of question dictionaries with text, type, and difficulty.
    """
    if question_types is None:
        from app.config import QUESTION_WEIGHTS
        question_types = QUESTION_WEIGHTS

    # Try OpenAI API first, fall back to templates
    try:
        return _generate_with_openai(skills, projects, difficulty, count, question_types)
    except Exception as e:
        logger.warning(f"OpenAI generation failed, using templates: {e}")
        return _generate_with_templates(skills, projects, difficulty, count, question_types)


def _generate_with_openai(
    skills: List[str],
    projects: List[str],
    difficulty: str,
    count: int,
    question_types: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Generate questions using OpenAI API."""
    from app.config import OPENAI_API_KEY, OPENAI_MODEL
    from app.constants import QUESTION_GENERATION_PROMPT

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        raise ImportError("openai package not installed")

    prompt = QUESTION_GENERATION_PROMPT.format(
        count=count,
        skills=", ".join(skills[:15]),
        projects=", ".join(projects[:5]),
        difficulty=difficulty,
        types=", ".join(f"{k} ({v*100:.0f}%)" for k, v in question_types.items()),
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert technical interviewer. Generate diverse, specific interview questions."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    content = response.choices[0].message.content or ""
    return _parse_llm_questions(content, difficulty)


def _parse_llm_questions(content: str, default_difficulty: str) -> List[Dict[str, Any]]:
    """Parse LLM-generated questions from text response."""
    questions = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Parse [type] question format
        if line.startswith("[") and "]" in line:
            bracket_end = line.index("]")
            q_type = line[1:bracket_end].strip().lower()
            q_text = line[bracket_end + 1:].strip()
            # Remove leading numbers, dots, dashes
            q_text = q_text.lstrip("0123456789.-) ")
            if q_text and q_type in ("resume", "technical", "behavioral"):
                questions.append({
                    "question_text": q_text,
                    "question_type": q_type,
                    "difficulty": default_difficulty,
                })
        else:
            # No type prefix, assume technical
            cleaned = line.lstrip("0123456789.-) ")
            if cleaned and len(cleaned) > 10:
                questions.append({
                    "question_text": cleaned,
                    "question_type": "technical",
                    "difficulty": default_difficulty,
                })
    return questions


def _generate_with_templates(
    skills: List[str],
    projects: List[str],
    difficulty: str,
    count: int,
    question_types: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Generate questions using template fallback."""
    from app.constants import (
        TECHNICAL_QUESTION_TEMPLATES,
        RESUME_QUESTION_TEMPLATES,
        BEHAVIORAL_QUESTIONS,
    )

    questions: List[Dict[str, Any]] = []

    # Calculate counts per type
    type_counts = {}
    remaining = count
    for q_type, weight in question_types.items():
        type_count = max(1, int(count * weight))
        type_counts[q_type] = min(type_count, remaining)
        remaining -= type_counts[q_type]

    # Adjust for rounding errors
    while sum(type_counts.values()) < count and type_counts:
        for q_type in type_counts:
            if sum(type_counts.values()) >= count:
                break
            type_counts[q_type] += 1

    # Generate resume questions
    resume_templates = RESUME_QUESTION_TEMPLATES
    resume_count = type_counts.get("resume", 0)
    if resume_count > 0 and (skills or projects):
        used_templates = set()
        for _ in range(resume_count):
            template = _pick_unique(resume_templates, used_templates)
            if template:
                skill = random.choice(skills) if skills else "your primary skill"
                other_skill = random.choice(skills) if len(skills) > 1 else "another technology"
                project = random.choice(projects) if projects else "your most recent project"
                text = template.format(skill=skill, other_skill=other_skill, project=project)
                questions.append({
                    "question_text": text,
                    "question_type": "resume",
                    "difficulty": difficulty,
                })

    # Generate technical questions
    tech_templates = TECHNICAL_QUESTION_TEMPLATES.get(difficulty, TECHNICAL_QUESTION_TEMPLATES["medium"])
    tech_count = type_counts.get("technical", 0)
    if tech_count > 0 and skills:
        used_templates = set()
        for _ in range(tech_count):
            template = _pick_unique(tech_templates, used_templates)
            if template:
                skill = random.choice(skills)
                other_skill = random.choice(skills) if len(skills) > 1 else "databases"
                text = template.format(skill=skill, other_skill=other_skill)
                questions.append({
                    "question_text": text,
                    "question_type": "technical",
                    "difficulty": difficulty,
                })

    # Generate behavioral questions
    behavioral_count = type_counts.get("behavioral", 0)
    if behavioral_count > 0:
        used_questions = set()
        for _ in range(behavioral_count):
            question = _pick_unique(BEHAVIORAL_QUESTIONS, used_questions)
            if question:
                questions.append({
                    "question_text": question,
                    "question_type": "behavioral",
                    "difficulty": "easy",  # Behavioral questions are typically easier
                })

    # Shuffle to mix question types
    random.shuffle(questions)
    return questions[:count]


def _pick_unique(items: list, used: set) -> Optional[str]:
    """Pick a unique item not in the used set."""
    available = [item for item in items if item not in used]
    if not available:
        # Reset if all used
        available = items
    if not available:
        return None
    choice = random.choice(available)
    used.add(choice)
    return choice


def generate_introduction(name: str, skills: List[str], question_count: int) -> str:
    """Generate an introduction message for the interview.
    
    Args:
        name: Candidate name.
        skills: List of extracted skills.
        question_count: Number of questions planned.
        
    Returns:
        Introduction text.
    """
    from app.constants import INTRODUCTION_TEMPLATE
    top_skills = ", ".join(skills[:3]) if skills else "your technical expertise"
    return INTRODUCTION_TEMPLATE.format(
        name=name,
        top_skills=top_skills,
        question_count=question_count,
    )


def generate_closing(name: str, answered_count: int, avg_score: float) -> str:
    """Generate a closing message for the interview.
    
    Args:
        name: Candidate name.
        answered_count: Number of questions answered.
        avg_score: Average answer score.
        
    Returns:
        Closing text.
    """
    from app.constants import CLOSING_TEMPLATE
    return CLOSING_TEMPLATE.format(
        name=name,
        answered_count=answered_count,
        avg_score=avg_score,
    )

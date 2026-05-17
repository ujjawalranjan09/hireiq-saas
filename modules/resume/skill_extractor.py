"""Skill extraction using spaCy NER and custom skill taxonomy."""

import logging
import re
from typing import List, Set, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded spaCy model
_nlp = None


def _get_nlp():
    """Lazily load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            from app.config import SPACY_MODEL
            try:
                _nlp = spacy.load(SPACY_MODEL)
            except OSError:
                logger.warning(f"spaCy model {SPACY_MODEL} not found, downloading...")
                from spacy.cli import download
                download(SPACY_MODEL)
                _nlp = spacy.load(SPACY_MODEL)
        except ImportError:
            logger.warning("spaCy not available, using regex-only extraction")
            _nlp = False
    return _nlp if _nlp else None


def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text using spaCy NER and taxonomy matching.
    
    Args:
        text: Resume text (or skills section text).
        
    Returns:
        List of unique extracted skills.
    """
    from app.constants import SKILL_TAXONOMY, ALL_SKILLS

    skills_found: Set[str] = set()
    text_lower = text.lower()

    # Method 1: Taxonomy-based matching
    for skill in ALL_SKILLS:
        # Use word boundary matching to avoid false positives
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            skills_found.add(skill.lower())

    # Method 2: spaCy NER for technology/product entities
    nlp = _get_nlp()
    if nlp:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
                    ent_lower = ent.text.lower().strip()
                    # Check if it matches known skills
                    for skill in ALL_SKILLS:
                        if skill.lower() in ent_lower or ent_lower in skill.lower():
                            skills_found.add(skill.lower())
        except Exception as e:
            logger.warning(f"spaCy NER failed: {e}")

    # Method 3: Look for common skill patterns
    # e.g., "Python 3.x", "React.js", "Node.js", "C++", "C#"
    skill_patterns = [
        r'\b[A-Z][a-z]+(?:\.[a-z]+)+\b',  # React.js, Node.js
        r'\b[A-Z]\+\+\b',  # C++
        r'\b[A-Z]#\b',  # C#
        r'\b(?:AWS|GCP|CI/CD|REST|API|SQL|NoSQL|HTML|CSS|JSON|XML|YAML|SSH|TCP|UDP)\b',
    ]
    for pattern in skill_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            skills_found.add(match.lower())

    # Categorize skills
    categorized = categorize_skills(list(skills_found))
    logger.info(f"Extracted {len(skills_found)} skills across {len(categorized)} categories")
    return sorted(skills_found)


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Categorize extracted skills into technology categories.
    
    Args:
        skills: List of skill strings.
        
    Returns:
        Dictionary mapping category names to lists of skills.
    """
    from app.constants import SKILL_TAXONOMY

    categorized: Dict[str, List[str]] = {cat: [] for cat in SKILL_TAXONOMY}
    categorized["other"] = []

    for skill in skills:
        skill_lower = skill.lower()
        found = False
        for category, category_skills in SKILL_TAXONOMY.items():
            if skill_lower in [s.lower() for s in category_skills]:
                categorized[category].append(skill)
                found = True
                break
        if not found:
            categorized["other"].append(skill)

    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}


def extract_projects(text: str) -> List[str]:
    """Extract project names from resume text.
    
    Args:
        text: Resume text (or projects section text).
        
    Returns:
        List of project names/titles.
    """
    projects: List[str] = []
    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Project entries often start with bullet points, dashes, or bold markers
        # Also look for lines that look like project titles
        cleaned = re.sub(r'^[\-•*▪►▸▹●○◆◇■□★☆→➜❯]+\s*', '', stripped)
        cleaned = cleaned.strip()

        # Skip very short or very long lines (likely not project names)
        if 3 < len(cleaned) < 200:
            # Skip lines that look like dates or durations
            if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2})', cleaned, re.IGNORECASE):
                continue
            # Skip lines that are just technology lists
            if re.match(r'^(?:Technologies|Tech Stack|Tools|Skills used):', cleaned, re.IGNORECASE):
                continue
            projects.append(cleaned)

    return projects[:20]  # Limit to reasonable number


def extract_candidate_info(text: str) -> Dict[str, Any]:
    """Extract candidate information (name, email) from resume text.
    
    Args:
        text: Raw resume text.
        
    Returns:
        Dictionary with candidate info fields.
    """
    info: Dict[str, Any] = {}

    # Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    if emails:
        info["email"] = emails[0]

    # Extract name (first line heuristic - often the name is on line 1)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        # The first non-empty line is often the name
        first_line = lines[0]
        # Skip if it looks like an email, phone, or URL
        if not re.search(email_pattern, first_line) and not re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', first_line):
            if not first_line.startswith("http") and len(first_line) < 60:
                info["name"] = first_line

    # Extract phone number
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}'
    phones = re.findall(phone_pattern, text)
    if phones:
        info["phone"] = phones[0]

    return info

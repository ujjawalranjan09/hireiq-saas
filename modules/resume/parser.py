"""PDF resume parser with section segmentation."""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        Extracted text as a single string.
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        RuntimeError: If extraction fails.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not available, falling back to PyPDF2")
        return _extract_with_pypdf2(pdf_path)

    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        full_text = "\n".join(text_parts)
        if not full_text.strip():
            logger.warning(f"No text extracted from {pdf_path}, trying PyPDF2")
            return _extract_with_pypdf2(pdf_path)
        return full_text
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")
        return _extract_with_pypdf2(pdf_path)


def _extract_with_pypdf2(pdf_path: str) -> str:
    """Fallback PDF extraction using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PyPDF2 extraction also failed: {e}")
        raise RuntimeError(f"Could not extract text from PDF: {e}")


# Common resume section headers
SECTION_PATTERNS = [
    r"(?i)^(?:professional\s+)?(?:summary|profile|objective|about\s+me)\s*$",
    r"(?i)^(?:work\s+)?experience\s*$",
    r"(?i)^(?:employment\s+)?history\s*$",
    r"(?i)^education\s*$",
    r"(?i)^(?:technical\s+)?skills?\s*$",
    r"(?i)^(?:technical\s+)?(?:competencies|expertise)\s*$",
    r"(?i)^projects?\s*$",
    r"(?i)^(?:key\s+)?projects?\s*$",
    r"(?i)^(?:certifications?|licenses?)\s*$",
    r"(?i)^(?:awards?|achievements?|honors?)\s*$",
    r"(?i)^(?:publications?)\s*$",
    r"(?i)^(?:volunteer|community)\s*(?:experience|work)?\s*$",
    r"(?i)^languages?\s*$",
    r"(?i)^(?:references?)\s*$",
    r"(?i)^(?:additional\s+)?(?:information|info)\s*$",
    r"(?i)^(?:internships?)\s*$",
]


def segment_resume(text: str) -> Dict[str, str]:
    """Segment resume text into named sections.
    
    Args:
        text: Raw resume text.
        
    Returns:
        Dictionary mapping section names to their content.
    """
    lines = text.split("\n")
    sections: Dict[str, str] = {}
    current_section = "header"
    current_content: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_content.append("")
            continue

        # Check if this line is a section header
        matched_section = None
        for pattern in SECTION_PATTERNS:
            if re.match(pattern, stripped):
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                # Normalize section name
                matched_section = _normalize_section_name(stripped)
                current_section = matched_section
                current_content = []
                break

        if matched_section is None:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _normalize_section_name(raw_name: str) -> str:
    """Normalize a section header to a canonical name."""
    name = raw_name.strip().lower()
    mapping = {
        "summary": "summary",
        "professional summary": "summary",
        "profile": "summary",
        "objective": "summary",
        "about me": "summary",
        "experience": "experience",
        "work experience": "experience",
        "employment history": "experience",
        "history": "experience",
        "education": "education",
        "skills": "skills",
        "skill": "skills",
        "technical skills": "skills",
        "technical skill": "skills",
        "competencies": "skills",
        "technical competencies": "skills",
        "expertise": "skills",
        "technical expertise": "skills",
        "projects": "projects",
        "project": "projects",
        "key projects": "projects",
        "certifications": "certifications",
        "certification": "certifications",
        "licenses": "certifications",
        "awards": "awards",
        "award": "awards",
        "achievements": "awards",
        "achievement": "awards",
        "honors": "awards",
        "publications": "publications",
        "publication": "publications",
        "volunteer experience": "volunteer",
        "volunteer work": "volunteer",
        "community experience": "volunteer",
        "community work": "volunteer",
        "volunteer": "volunteer",
        "languages": "languages",
        "language": "languages",
        "references": "references",
        "reference": "references",
        "additional information": "additional_info",
        "additional info": "additional_info",
        "information": "additional_info",
        "info": "additional_info",
        "internships": "internships",
        "internship": "internships",
    }
    return mapping.get(name, name.replace(" ", "_"))


def extract_sections(pdf_path: str) -> Dict[str, str]:
    """Extract and segment a resume PDF into named sections.
    
    Args:
        pdf_path: Path to the resume PDF.
        
    Returns:
        Dictionary of section name to section content.
    """
    raw_text = extract_text_from_pdf(pdf_path)
    sections = segment_resume(raw_text)
    logger.info(f"Extracted {len(sections)} sections from resume")
    return sections

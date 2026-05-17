"""Job matcher — compares candidate skills against job requirements."""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of matching candidate skills to job requirements."""
    match_percentage: float
    matched_skills: List[str]
    missing_skills: List[str]
    bonus_skills: List[str]
    total_required: int
    total_matched: int
    skill_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_percentage": self.match_percentage,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "bonus_skills": self.bonus_skills,
            "total_required": self.total_required,
            "total_matched": self.total_matched,
            "skill_details": self.skill_details,
        }

    @property
    def assessment(self) -> str:
        """Human-readable assessment of the match."""
        if self.match_percentage >= 80:
            return "Excellent match — candidate meets most requirements"
        elif self.match_percentage >= 60:
            return "Good match — candidate covers core requirements"
        elif self.match_percentage >= 40:
            return "Partial match — significant gaps exist"
        else:
            return "Weak match — candidate does not meet key requirements"


class JobMatcher:
    """Compares candidate skills against job description requirements.

    Extracts required and preferred skills from a job description and
    calculates match statistics against the candidate's skill set.

    Args:
        skill_taxonomy: Optional custom skill taxonomy. Uses default from
            constants if not provided.
    """

    def __init__(self, skill_taxonomy: Optional[Dict[str, List[str]]] = None):
        if skill_taxonomy:
            self._taxonomy = skill_taxonomy
        else:
            try:
                from app.constants import SKILL_TAXONOMY
                self._taxonomy = SKILL_TAXONOMY
            except ImportError:
                self._taxonomy = {}

        # Flatten for quick lookup
        self._all_known_skills: Set[str] = set()
        for skills in self._taxonomy.values():
            self._all_known_skills.update(s.lower() for s in skills)

    def match(
        self,
        candidate_skills: List[str],
        job_description: str,
        project_skills: Optional[List[str]] = None,
    ) -> MatchResult:
        """Match candidate skills against a job description.

        Args:
            candidate_skills: Skills listed on the candidate's resume.
            job_description: Full text of the job description.
            project_skills: Additional skills inferred from project descriptions.

        Returns:
            MatchResult with detailed match analysis.
        """
        candidate_set = {s.lower().strip() for s in candidate_skills}
        if project_skills:
            candidate_set.update(s.lower().strip() for s in project_skills)

        jd_lower = job_description.lower()

        # Extract required and preferred skills from JD
        required_skills = self._extract_required_skills(jd_lower)
        preferred_skills = self._extract_preferred_skills(jd_lower)

        # Match against required
        matched_required = []
        missing_required = []
        for skill in required_skills:
            if self._skill_matches(skill, candidate_set):
                matched_required.append(skill)
            else:
                missing_required.append(skill)

        # Match against preferred
        matched_preferred = []
        for skill in preferred_skills:
            if self._skill_matches(skill, candidate_set):
                matched_preferred.append(skill)

        # Calculate bonus skills (candidate has but JD doesn't mention)
        jd_all_skills = required_skills | preferred_skills
        bonus_skills = sorted(
            s for s in candidate_set
            if not any(self._fuzzy_match(s, js) for js in jd_all_skills)
        )

        # Match percentage: weight required at 70%, preferred at 30%
        req_total = len(required_skills) or 1
        pref_total = len(preferred_skills) or 1
        req_pct = len(matched_required) / req_total * 100
        pref_pct = len(matched_preferred) / pref_total * 100 if preferred_skills else 100
        match_pct = req_pct * 0.7 + pref_pct * 0.3

        # Build per-skill details
        skill_details: List[Dict[str, Any]] = []
        for skill in sorted(required_skills):
            matched = self._skill_matches(skill, candidate_set)
            skill_details.append({
                "skill": skill,
                "required": True,
                "matched": matched,
                "severity": "critical" if not matched else "met",
            })
        for skill in sorted(preferred_skills):
            matched = self._skill_matches(skill, candidate_set)
            skill_details.append({
                "skill": skill,
                "required": False,
                "matched": matched,
                "severity": "preferred" if not matched else "bonus",
            })

        return MatchResult(
            match_percentage=round(match_pct, 1),
            matched_skills=sorted(set(matched_required + matched_preferred)),
            missing_skills=sorted(missing_required),
            bonus_skills=bonus_skills[:20],  # Cap bonus list
            total_required=len(required_skills) + len(preferred_skills),
            total_matched=len(matched_required) + len(matched_preferred),
            skill_details=skill_details,
        )

    def generate_gap_analysis(self, match_result: MatchResult) -> Dict[str, Any]:
        """Generate a detailed gap analysis report.

        Args:
            match_result: The MatchResult from match().

        Returns:
            Dict with gap analysis structured for report generation.
        """
        critical_gaps = [
            d for d in match_result.skill_details
            if d["required"] and not d["matched"]
        ]
        nice_to_have_gaps = [
            d for d in match_result.skill_details
            if not d["required"] and not d["matched"]
        ]

        # Estimate effort to close gaps
        effort_map = {
            "programming_languages": "2-4 weeks",
            "web_frameworks": "1-3 weeks",
            "databases": "1-2 weeks",
            "cloud_devops": "2-4 weeks",
            "ml_ai": "4-8 weeks",
            "data_tools": "1-3 weeks",
            "mobile": "3-6 weeks",
            "soft_skills": "Ongoing practice",
        }

        gap_details = []
        for gap in critical_gaps:
            category = self._find_skill_category(gap["skill"])
            gap_details.append({
                "skill": gap["skill"],
                "severity": "critical",
                "category": category,
                "estimated_effort": effort_map.get(category, "2-4 weeks"),
                "suggestion": f"Focus on learning {gap['skill']} fundamentals and hands-on practice.",
            })

        for gap in nice_to_have_gaps:
            category = self._find_skill_category(gap["skill"])
            gap_details.append({
                "skill": gap["skill"],
                "severity": "nice-to-have",
                "category": category,
                "estimated_effort": effort_map.get(category, "1-2 weeks"),
                "suggestion": f"Consider learning {gap['skill']} to strengthen your candidacy.",
            })

        return {
            "match_percentage": match_result.match_percentage,
            "assessment": match_result.assessment,
            "critical_gaps": critical_gaps,
            "nice_to_have_gaps": nice_to_have_gaps,
            "gap_details": gap_details,
            "matched_count": len(match_result.matched_skills),
            "missing_count": len(match_result.missing_skills),
            "bonus_skills": match_result.bonus_skills,
        }

    # ── Internal methods ──────────────────────────────────────────────

    def _extract_required_skills(self, jd_text: str) -> Set[str]:
        """Extract required skills from job description text."""
        return self._extract_skills_by_keywords(
            jd_text,
            keywords=["required", "must have", "essential", "minimum", "qualifications", "requirements"],
        )

    def _extract_preferred_skills(self, jd_text: str) -> Set[str]:
        """Extract preferred/nice-to-have skills from job description text."""
        return self._extract_skills_by_keywords(
            jd_text,
            keywords=["preferred", "nice to have", "bonus", "plus", "desirable", "advantage"],
        )

    def _extract_skills_by_keywords(
        self, text: str, keywords: List[str]
    ) -> Set[str]:
        """Extract skills from text segments that contain specific keywords."""
        found_skills: Set[str] = set()
        lines = re.split(r"[.\n,;]", text)

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if any(kw in line_stripped for kw in keywords):
                # Check for known skills in this line
                for skill in self._all_known_skills:
                    if skill in line_stripped:
                        found_skills.add(skill)

        # Also scan the full text for common skills
        for skill in self._all_known_skills:
            if skill in text:
                found_skills.add(skill)

        return found_skills

    def _skill_matches(self, target_skill: str, candidate_skills: Set[str]) -> bool:
        """Check if a target skill matches any candidate skill."""
        for cs in candidate_skills:
            if self._fuzzy_match(target_skill, cs):
                return True
        return False

    @staticmethod
    def _fuzzy_match(a: str, b: str) -> bool:
        """Fuzzy skill matching with common aliases."""
        a = a.lower().strip()
        b = b.lower().strip()

        if a == b:
            return True

        # Check substrings
        if a in b or b in a:
            return True

        # Common aliases
        aliases = {
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "c++": "cpp",
            "node.js": "nodejs",
            "node": "nodejs",
            "react.js": "react",
            "vue.js": "vue",
            "next.js": "nextjs",
            "postgresql": "postgres",
            "mongo": "mongodb",
            "k8s": "kubernetes",
            "tf": "tensorflow",
            "sklearn": "scikit-learn",
            "cv": "computer vision",
        }

        a_normalized = aliases.get(a, a)
        b_normalized = aliases.get(b, b)

        return a_normalized == b_normalized

    def _find_skill_category(self, skill: str) -> str:
        """Find which taxonomy category a skill belongs to."""
        skill_lower = skill.lower()
        for category, skills in self._taxonomy.items():
            if skill_lower in [s.lower() for s in skills]:
                return category
        return "other"

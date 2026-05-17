"""Tests for the resume parsing and skill extraction modules."""

import unittest
import tempfile
import os


class TestResumeParser(unittest.TestCase):
    """Test resume PDF parsing."""

    def test_segment_resume_empty(self):
        """Test segmenting empty text."""
        from modules.resume.parser import segment_resume
        result = segment_resume("")
        self.assertIsInstance(result, dict)

    def test_segment_resume_sections(self):
        """Test section detection."""
        from modules.resume.parser import segment_resume
        text = """John Doe
john@example.com

Summary
Experienced software engineer.

Skills
Python, JavaScript, SQL

Experience
Senior Engineer at Tech Corp.

Education
BS Computer Science, MIT
"""
        result = segment_resume(text)
        self.assertIn("summary", result)
        self.assertIn("skills", result)
        self.assertIn("experience", result)
        self.assertIn("education", result)

    def test_normalize_section_names(self):
        """Test section name normalization."""
        from modules.resume.parser import _normalize_section_name
        self.assertEqual(_normalize_section_name("Work Experience"), "experience")
        self.assertEqual(_normalize_section_name("Technical Skills"), "skills")
        self.assertEqual(_normalize_section_name("Education"), "education")


class TestSkillExtractor(unittest.TestCase):
    """Test skill extraction."""

    def test_extract_skills_from_text(self):
        """Test basic skill extraction."""
        from modules.resume.skill_extractor import extract_skills
        text = "I have experience with Python, JavaScript, React, and AWS."
        skills = extract_skills(text)
        self.assertIsInstance(skills, list)
        # Should find at least some skills
        skills_lower = [s.lower() for s in skills]
        self.assertTrue(any(s in skills_lower for s in ["python", "javascript"]))

    def test_extract_skills_empty(self):
        """Test skill extraction with empty text."""
        from modules.resume.skill_extractor import extract_skills
        skills = extract_skills("")
        self.assertEqual(skills, [])

    def test_categorize_skills(self):
        """Test skill categorization."""
        from modules.resume.skill_extractor import categorize_skills
        skills = ["python", "javascript", "react", "aws", "mongodb"]
        categories = categorize_skills(skills)
        self.assertIsInstance(categories, dict)

    def test_extract_projects(self):
        """Test project extraction."""
        from modules.resume.skill_extractor import extract_projects
        text = """Projects
E-commerce Platform - Built a full-stack web app
Data Pipeline - Designed ETL workflow
"""
        projects = extract_projects(text)
        self.assertIsInstance(projects, list)
        self.assertGreater(len(projects), 0)

    def test_extract_candidate_info(self):
        """Test candidate info extraction."""
        from modules.resume.skill_extractor import extract_candidate_info
        text = "John Doe\njohn.doe@example.com\n+1-555-123-4567"
        info = extract_candidate_info(text)
        self.assertIn("email", info)
        self.assertEqual(info["email"], "john.doe@example.com")


class TestSkillGraph(unittest.TestCase):
    """Test skill graph building."""

    def test_build_skill_graph(self):
        """Test building a skill graph."""
        from modules.resume.skill_graph import build_skill_graph
        skills = ["python", "javascript", "react", "django", "sql"]
        text = "Python Django web applications with JavaScript React frontend and SQL database."
        graph = build_skill_graph(skills, text)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertGreater(len(graph["nodes"]), 0)

    def test_build_skill_graph_empty(self):
        """Test building graph with no skills."""
        from modules.resume.skill_graph import build_skill_graph
        graph = build_skill_graph([])
        self.assertEqual(graph["node_count"], 0)

    def test_get_related_skills(self):
        """Test getting related skills."""
        from modules.resume.skill_graph import build_skill_graph, get_related_skills
        skills = ["python", "django", "sql", "javascript"]
        text = "Python Django and SQL backend with JavaScript frontend."
        graph = build_skill_graph(skills, text)
        related = get_related_skills(graph, "python", top_k=2)
        self.assertIsInstance(related, list)


if __name__ == "__main__":
    unittest.main()

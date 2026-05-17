"""Tests for the evaluation module."""

import unittest


class TestAnswerEvaluator(unittest.TestCase):
    """Test answer evaluation."""

    def test_evaluate_empty_answer(self):
        """Test evaluating an empty answer."""
        from modules.evaluation.answer_evaluator import evaluate_answer
        result = evaluate_answer("What is Python?", "")
        self.assertEqual(result["total_score"], 0.0)

    def test_evaluate_good_answer(self):
        """Test evaluating a good answer."""
        from modules.evaluation.answer_evaluator import evaluate_answer
        answer = (
            "Python is a high-level, interpreted programming language known for its "
            "simplicity and readability. It supports multiple programming paradigms "
            "including procedural, object-oriented, and functional programming. "
            "Python is widely used in web development, data science, machine learning, "
            "and automation. I've used it extensively in my projects."
        )
        result = evaluate_answer("What is Python?", answer, keywords=["python", "programming"])
        self.assertGreater(result["total_score"], 0)
        self.assertIn("semantic_score", result)
        self.assertIn("keyword_score", result)

    def test_evaluate_with_keywords(self):
        """Test keyword matching."""
        from modules.evaluation.answer_evaluator import _calculate_keyword_score
        score = _calculate_keyword_score(
            "I use Python and JavaScript daily",
            ["python", "javascript", "sql"]
        )
        # Should match 2 out of 3
        self.assertAlmostEqual(score, 2 / 3 * 100, delta=1)

    def test_evaluate_without_keywords(self):
        """Test scoring without keywords."""
        from modules.evaluation.answer_evaluator import _calculate_keyword_score
        score = _calculate_keyword_score("Some answer here", [])
        self.assertGreater(score, 0)


class TestSemanticScorer(unittest.TestCase):
    """Test semantic similarity scoring."""

    def test_compute_similarity_identical(self):
        """Test identical texts."""
        from modules.evaluation.semantic_scorer import compute_similarity
        sim = compute_similarity("hello world", "hello world")
        self.assertGreater(sim, 0.5)

    def test_compute_similarity_different(self):
        """Test different texts."""
        from modules.evaluation.semantic_scorer import compute_similarity
        sim = compute_similarity("Python programming", "cooking recipes")
        self.assertLess(sim, 0.8)

    def test_compute_similarity_empty(self):
        """Test empty texts."""
        from modules.evaluation.semantic_scorer import compute_similarity
        sim = compute_similarity("", "hello")
        self.assertEqual(sim, 0.0)

    def test_fallback_similarity(self):
        """Test fallback Jaccard similarity."""
        from modules.evaluation.semantic_scorer import _fallback_similarity
        sim = _fallback_similarity("the cat sat on mat", "the cat sat on a mat")
        self.assertGreater(sim, 0.5)


class TestConfidenceModel(unittest.TestCase):
    """Test confidence calculation."""

    def test_calculate_confidence_default(self):
        """Test default confidence calculation."""
        from modules.evaluation.confidence_model import calculate_confidence
        result = calculate_confidence(50, 50, 50)
        self.assertEqual(result["combined_score"], 50.0)

    def test_calculate_confidence_high(self):
        """Test high confidence."""
        from modules.evaluation.confidence_model import calculate_confidence
        result = calculate_confidence(90, 80, 85)
        self.assertGreater(result["combined_score"], 80)

    def test_calculate_confidence_low(self):
        """Test low confidence."""
        from modules.evaluation.confidence_model import calculate_confidence
        result = calculate_confidence(20, 30, 10)
        self.assertLess(result["combined_score"], 30)

    def test_confidence_weights(self):
        """Test that facial has highest weight."""
        from modules.evaluation.confidence_model import calculate_confidence
        # Same scores, facial should dominate
        result = calculate_confidence(100, 0, 0)
        self.assertGreater(result["combined_score"], 40)

    def test_calculate_fluency(self):
        """Test fluency score calculation."""
        from modules.evaluation.confidence_model import calculate_fluency_score
        # Ideal speaking speed, no pauses, no hesitation
        score = calculate_fluency_score(
            speaking_speed=140,
            pause_ratio=0.1,
            hesitation_detected=False,
            word_count=100,
            duration=60,
        )
        self.assertGreater(score, 60)

    def test_aggregate_confidence_timeline(self):
        """Test timeline aggregation."""
        from modules.evaluation.confidence_model import aggregate_confidence_timeline
        timeline = [
            {"combined_score": 40},
            {"combined_score": 50},
            {"combined_score": 60},
            {"combined_score": 70},
            {"combined_score": 80},
        ]
        result = aggregate_confidence_timeline(timeline)
        self.assertEqual(result["trend"], "improving")


class TestDifficultyManager(unittest.TestCase):
    """Test adaptive difficulty management."""

    def test_initial_difficulty(self):
        """Test initial difficulty is medium."""
        from modules.questions.difficulty_manager import DifficultyManager
        dm = DifficultyManager()
        self.assertEqual(dm.current_level, 2)

    def test_increase_difficulty(self):
        """Test difficulty increases on high scores."""
        from modules.questions.difficulty_manager import DifficultyManager
        dm = DifficultyManager()
        dm.add_score(90)
        dm.add_score(92)
        dm.add_score(88)
        self.assertGreater(dm.current_level, 2)

    def test_decrease_difficulty(self):
        """Test difficulty decreases on low scores."""
        from modules.questions.difficulty_manager import DifficultyManager
        dm = DifficultyManager()
        dm.add_score(30)
        dm.add_score(25)
        dm.add_score(20)
        self.assertLess(dm.current_level, 2)

    def test_maintain_difficulty(self):
        """Test difficulty stays same on medium scores."""
        from modules.questions.difficulty_manager import DifficultyManager
        dm = DifficultyManager()
        dm.add_score(70)
        dm.add_score(72)
        dm.add_score(68)
        self.assertEqual(dm.current_level, 2)

    def test_stats(self):
        """Test getting stats."""
        from modules.questions.difficulty_manager import DifficultyManager
        dm = DifficultyManager()
        dm.add_score(80)
        stats = dm.get_stats()
        self.assertIn("current_level", stats)
        self.assertIn("average_score", stats)


class TestQuestionGenerator(unittest.TestCase):
    """Test question generation."""

    def test_generate_with_templates(self):
        """Test template-based generation."""
        from modules.questions.generator import generate_questions
        questions = generate_questions(
            skills=["python", "javascript", "sql"],
            projects=["E-commerce App", "Data Pipeline"],
            difficulty="medium",
            count=5,
        )
        self.assertEqual(len(questions), 5)
        for q in questions:
            self.assertIn("question_text", q)
            self.assertIn("question_type", q)
            self.assertIn("difficulty", q)

    def test_generate_introduction(self):
        """Test introduction generation."""
        from modules.questions.generator import generate_introduction
        intro = generate_introduction("John Doe", ["python", "react"], 10)
        self.assertIn("John Doe", intro)
        self.assertIn("10", intro)

    def test_generate_closing(self):
        """Test closing generation."""
        from modules.questions.generator import generate_closing
        closing = generate_closing("Jane", 8, 75.5)
        self.assertIn("Jane", closing)
        self.assertIn("8", closing)


class TestFollowUp(unittest.TestCase):
    """Test follow-up question generation."""

    def test_should_generate_followup(self):
        """Test follow-up decision logic."""
        from modules.questions.follow_up import should_generate_followup
        # Low score, might get follow-up
        self.assertIsInstance(should_generate_followup(30), bool)
        # High score, might get follow-up
        self.assertIsInstance(should_generate_followup(90), bool)

    def test_should_not_followup_max(self):
        """Test max follow-ups limit."""
        from modules.questions.follow_up import should_generate_followup
        self.assertFalse(should_generate_followup(50, max_followups=2, current_followups=2))

    def test_generate_followup_template(self):
        """Test template follow-up generation."""
        from modules.questions.follow_up import _generate_followup_template
        result = _generate_followup_template(
            question="What is Python?",
            answer="Python is a programming language.",
            score=60,
            skills=["python"],
        )
        self.assertIn("question_text", result)
        self.assertTrue(result["is_followup"])


class TestStateMachine(unittest.TestCase):
    """Test state machine transitions."""

    def test_initial_state(self):
        """Test initial state is IDLE."""
        from modules.orchestrator.state_machine import StateMachine
        sm = StateMachine()
        self.assertEqual(sm.current_state, "idle")

    def test_valid_transition(self):
        """Test valid state transition."""
        from modules.orchestrator.state_machine import StateMachine
        from app.constants import InterviewState
        sm = StateMachine()
        result = sm.transition(InterviewState.RESUME_PROCESSING)
        self.assertTrue(result)
        self.assertEqual(sm.current_state, InterviewState.RESUME_PROCESSING)

    def test_invalid_transition(self):
        """Test invalid state transition."""
        from modules.orchestrator.state_machine import StateMachine
        from app.constants import InterviewState
        sm = StateMachine()
        # Can't go from IDLE to COMPLETED
        result = sm.transition(InterviewState.COMPLETED)
        self.assertFalse(result)

    def test_force_transition(self):
        """Test forced transition."""
        from modules.orchestrator.state_machine import StateMachine
        from app.constants import InterviewState
        sm = StateMachine()
        sm.force_transition(InterviewState.COMPLETED)
        self.assertEqual(sm.current_state, InterviewState.COMPLETED)

    def test_reset(self):
        """Test state machine reset."""
        from modules.orchestrator.state_machine import StateMachine
        from app.constants import InterviewState
        sm = StateMachine()
        sm.transition(InterviewState.RESUME_PROCESSING)
        sm.reset()
        self.assertEqual(sm.current_state, "idle")

    def test_can_transition(self):
        """Test transition checking."""
        from modules.orchestrator.state_machine import StateMachine
        from app.constants import InterviewState
        sm = StateMachine()
        self.assertTrue(sm.can_transition(InterviewState.RESUME_PROCESSING))
        self.assertFalse(sm.can_transition(InterviewState.COMPLETED))


class TestPerformanceEngine(unittest.TestCase):
    """Test performance metrics calculation."""

    def test_empty_metrics(self):
        """Test with no questions."""
        from modules.analytics.performance_engine import calculate_performance_metrics
        metrics = calculate_performance_metrics([])
        self.assertEqual(metrics["average_score"], 0.0)
        self.assertEqual(metrics["questions_answered"], 0)

    def test_basic_metrics(self):
        """Test basic metric calculation."""
        from modules.analytics.performance_engine import calculate_performance_metrics
        questions = [
            {"answer_score": 80, "question_type": "technical", "difficulty": "medium",
             "semantic_similarity_score": 70, "keyword_match_score": 85, "concept_coverage_score": 75},
            {"answer_score": 60, "question_type": "behavioral", "difficulty": "easy",
             "semantic_similarity_score": 50, "keyword_match_score": 60, "concept_coverage_score": 55},
        ]
        metrics = calculate_performance_metrics(questions)
        self.assertEqual(metrics["questions_answered"], 2)
        self.assertEqual(metrics["average_score"], 70.0)
        self.assertIn("scores_by_type", metrics)


if __name__ == "__main__":
    unittest.main()

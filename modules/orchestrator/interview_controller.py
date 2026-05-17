"""Main interview flow controller - orchestrates the entire interview."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.constants import InterviewState, DifficultyLevel

logger = logging.getLogger(__name__)


class InterviewController:
    """Controls the full interview flow from resume processing to report generation."""

    def __init__(self):
        """Initialize the interview controller."""
        from modules.orchestrator.state_machine import StateMachine
        from modules.orchestrator.session_manager import SessionManager
        from modules.questions.difficulty_manager import DifficultyManager

        self.state_machine = StateMachine()
        self.session_manager = SessionManager()
        self.difficulty_manager = DifficultyManager()
        self._session_id: Optional[str] = None

    def start_interview(
        self,
        candidate_id: str,
        resume_path: str = "",
        question_count: int = 10,
    ) -> Dict[str, Any]:
        """Start a new interview from resume processing.
        
        Args:
            candidate_id: MongoDB candidate ID.
            resume_path: Path to the candidate's resume PDF.
            question_count: Number of questions to prepare.
            
        Returns:
            Result dictionary with session info and generated questions.
        """
        try:
            # 1. Process resume
            self.state_machine.transition(InterviewState.RESUME_PROCESSING)
            skills, projects = self._process_resume(resume_path)

            # 2. Create interview in DB
            from database.models import Interview
            from database.queries import create_interview

            interview = Interview(
                candidate_id=candidate_id,
                status="active",
                difficulty_level=self.difficulty_manager.current_level,
                start_time=datetime.utcnow(),
                questions_count=question_count,
            )
            interview_id = create_interview(interview)

            # 3. Create session
            self._session_id = self.session_manager.create_session(
                candidate_id=candidate_id,
                interview_id=interview_id,
                skills=skills,
                projects=projects,
            )

            # 4. Generate questions
            self.state_machine.transition(InterviewState.READY)
            questions = self._generate_questions(
                skills=skills,
                projects=projects,
                count=question_count,
                difficulty=DifficultyLevel.to_name(self.difficulty_manager.current_level),
            )

            # 5. Save questions to DB and session
            from database.models import Question as QuestionModel
            from database.queries import bulk_create_questions

            db_questions = []
            for i, q in enumerate(questions):
                q_obj = QuestionModel(
                    interview_id=interview_id,
                    question_text=q["question_text"],
                    question_type=q.get("question_type", "technical"),
                    difficulty=q.get("difficulty", "medium"),
                    order=i,
                )
                db_questions.append(q_obj)
                self.session_manager.add_question(self._session_id, q)

            bulk_create_questions(db_questions)

            # 6. Update interview status
            from database.queries import update_interview
            update_interview(interview_id, {"status": "ready"})

            logger.info(f"Interview started: {interview_id} with {len(questions)} questions")

            return {
                "success": True,
                "interview_id": interview_id,
                "session_id": self._session_id,
                "skills": skills,
                "projects": projects,
                "questions": questions,
                "question_count": len(questions),
            }

        except Exception as e:
            logger.error(f"Failed to start interview: {e}")
            self.state_machine.force_transition(InterviewState.ERROR)
            return {"success": False, "error": str(e)}

    def get_introduction(self, candidate_name: str) -> str:
        """Generate the introduction message.
        
        Args:
            candidate_name: Name of the candidate.
            
        Returns:
            Introduction text.
        """
        session = self.session_manager.get_session(self._session_id) if self._session_id else None
        skills = session.get("skills", []) if session else []
        count = len(session.get("questions", [])) if session else 10

        self.state_machine.transition(InterviewState.INTRODUCTION)

        from modules.questions.generator import generate_introduction
        return generate_introduction(candidate_name, skills, count)

    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """Get the next question to ask.
        
        Returns:
            Question dictionary or None if no more questions.
        """
        if not self._session_id:
            return None

        session = self.session_manager.get_session(self._session_id)
        if not session:
            return None

        questions = session.get("questions", [])
        index = session.get("current_question_index", 0)

        if index >= len(questions):
            return None

        question = questions[index]
        self.state_machine.transition(InterviewState.ASKING_QUESTION)
        self.state_machine.transition(InterviewState.LISTENING)

        return {
            "question": question,
            "index": index,
            "total": len(questions),
            "difficulty": self.difficulty_manager.difficulty_name,
        }

    def process_answer(
        self,
        answer_text: str,
        audio_path: str = "",
        facial_emotion: Dict[str, Any] = None,
        voice_features: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process a candidate's answer and evaluate it.
        
        Args:
            answer_text: Transcribed answer text.
            audio_path: Path to the audio recording.
            facial_emotion: Facial emotion detection result.
            voice_features: Voice emotion analysis result.
            
        Returns:
            Evaluation result with scores and next action.
        """
        if not self._session_id:
            return {"error": "No active session"}

        session = self.session_manager.get_session(self._session_id)
        if not session:
            return {"error": "Session not found"}

        self.state_machine.transition(InterviewState.PROCESSING_ANSWER)

        index = session.get("current_question_index", 0)
        questions = session.get("questions", [])
        question = questions[index] if index < len(questions) else {}

        # 1. Evaluate the answer
        from modules.evaluation.answer_evaluator import evaluate_answer
        evaluation = evaluate_answer(
            question=question.get("question_text", ""),
            answer=answer_text,
            keywords=self._extract_keywords(question, session),
            question_type=question.get("question_type", "technical"),
        )

        score = evaluation["total_score"]

        # 2. Calculate confidence
        from modules.evaluation.confidence_model import calculate_confidence, calculate_fluency_score

        facial_conf = 50.0
        if facial_emotion:
            facial_conf = facial_emotion.get("confidence_score", 50.0)

        voice_conf = 50.0
        fluency = 50.0
        if voice_features:
            voice_conf = voice_features.get("confidence_score", 50.0)
            fluency = calculate_fluency_score(
                speaking_speed=voice_features.get("speaking_speed", 120),
                pause_ratio=voice_features.get("pause_ratio", 0),
                hesitation_detected=voice_features.get("hesitation_detected", False),
                word_count=len(answer_text.split()),
                duration=voice_features.get("duration", 0),
            )

        confidence = calculate_confidence(facial_conf, voice_conf, fluency)

        # 3. Update question in DB
        from database.queries import update_question, get_questions_for_interview
        interview_id = session["interview_id"]
        db_questions = get_questions_for_interview(interview_id)
        if index < len(db_questions):
            update_question(str(db_questions[index]._id), {
                "candidate_answer_text": answer_text,
                "answer_audio_path": audio_path,
                "answer_score": score,
                "semantic_similarity_score": evaluation["semantic_score"],
                "keyword_match_score": evaluation["keyword_score"],
                "concept_coverage_score": evaluation["concept_score"],
            })

        # 4. Save emotion snapshot
        from database.models import EmotionSnapshot
        from database.queries import create_emotion_snapshot

        snapshot = EmotionSnapshot(
            interview_id=interview_id,
            facial_emotion=facial_emotion.get("dominant_emotion", "neutral") if facial_emotion else "neutral",
            facial_confidence_score=facial_conf,
            voice_emotion=voice_features.get("emotion_label", "neutral") if voice_features else "neutral",
            voice_pitch=voice_features.get("pitch_mean", 0) if voice_features else 0,
            speaking_speed=voice_features.get("speaking_speed", 0) if voice_features else 0,
            hesitation_detected=voice_features.get("hesitation_detected", False) if voice_features else False,
            combined_confidence_score=confidence["combined_score"],
        )
        create_emotion_snapshot(snapshot)
        self.session_manager.add_emotion_snapshot(self._session_id, snapshot.to_dict())

        # 5. Update scores
        self.session_manager.add_score(self._session_id, score)
        self.difficulty_manager.add_score(score)

        # 6. Advance question index
        self.session_manager.update_session(self._session_id, {
            "current_question_index": index + 1,
        })

        # 7. Check for follow-up
        from modules.questions.follow_up import should_generate_followup, generate_followup

        followup = None
        session = self.session_manager.get_session(self._session_id)
        followup_count = session.get("followup_count", 0)

        if should_generate_followup(score, current_followups=followup_count):
            followup = generate_followup(
                question=question.get("question_text", ""),
                answer=answer_text,
                score=score,
                skills=session.get("skills", []),
                question_type=question.get("question_type", "technical"),
            )
            self.session_manager.increment_followup(self._session_id)
        else:
            self.session_manager.reset_followup(self._session_id)

        # 8. Determine next action
        has_more = (index + 1) < len(questions)
        next_action = "followup" if followup else ("next_question" if has_more else "closing")

        return {
            "evaluation": evaluation,
            "confidence": confidence,
            "next_action": next_action,
            "followup": followup,
            "question_number": index + 1,
            "total_questions": len(questions),
            "difficulty": self.difficulty_manager.difficulty_name,
        }

    def process_followup_answer(
        self,
        answer_text: str,
        audio_path: str = "",
        facial_emotion: Dict[str, Any] = None,
        voice_features: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process a follow-up answer (simplified evaluation).
        
        Args:
            answer_text: Transcribed answer text.
            audio_path: Path to audio recording.
            facial_emotion: Facial emotion result.
            voice_features: Voice features.
            
        Returns:
            Result with next action.
        """
        if not self._session_id:
            return {"error": "No active session"}

        self.state_machine.transition(InterviewState.PROCESSING_ANSWER)

        # Simplified evaluation for follow-ups
        from modules.evaluation.answer_evaluator import evaluate_answer
        session = self.session_manager.get_session(self._session_id)
        questions = session.get("questions", [])
        index = session.get("current_question_index", 0)
        question = questions[index - 1] if index > 0 else {}

        evaluation = evaluate_answer(
            question=question.get("question_text", ""),
            answer=answer_text,
        )

        # Check if more questions remain
        has_more = index < len(questions)
        return {
            "evaluation": evaluation,
            "next_action": "next_question" if has_more else "closing",
        }

    def close_interview(self, candidate_name: str = "Candidate") -> Dict[str, Any]:
        """Close the interview and generate the report.
        
        Args:
            candidate_name: Name of the candidate.
            
        Returns:
            Report generation result.
        """
        if not self._session_id:
            return {"error": "No active session"}

        session = self.session_manager.get_session(self._session_id)
        if not session:
            return {"error": "Session not found"}

        # Transition to closing
        self.state_machine.transition(InterviewState.CLOSING)

        scores = session.get("score_history", [])
        avg_score = sum(scores) / len(scores) if scores else 0

        from modules.questions.generator import generate_closing
        closing_message = generate_closing(
            candidate_name,
            len(scores),
            avg_score,
        )

        # Generate report
        self.state_machine.transition(InterviewState.GENERATING_REPORT)

        try:
            report_result = self._generate_report(session, candidate_name)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            report_result = {"error": str(e)}

        # Update interview in DB
        from database.queries import update_interview
        update_interview(session["interview_id"], {
            "status": "completed",
            "end_time": datetime.utcnow(),
            "total_score": avg_score,
        })

        # Mark session as closed
        self.session_manager.close_session(self._session_id)

        # Transition to completed
        self.state_machine.transition(InterviewState.COMPLETED)

        return {
            "closing_message": closing_message,
            "average_score": avg_score,
            "questions_answered": len(scores),
            "report": report_result,
        }

    def get_state(self) -> str:
        """Get current interview state."""
        return self.state_machine.current_state

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive interview statistics."""
        stats = {
            "state": self.state_machine.get_stats(),
            "difficulty": self.difficulty_manager.get_stats(),
        }
        if self._session_id:
            stats["session"] = self.session_manager.get_session_stats(self._session_id)
        return stats

    # ─── Private helpers ──────────────────────────────────────────────

    def _process_resume(self, resume_path: str) -> tuple:
        """Process resume to extract skills and projects."""
        if not resume_path:
            return ["python", "javascript", "sql"], ["Sample Project"]

        from modules.resume.parser import extract_sections
        from modules.resume.skill_extractor import extract_skills, extract_projects, extract_candidate_info

        sections = extract_sections(resume_path)

        # Extract from all text
        full_text = "\n".join(sections.values())
        skills = extract_skills(full_text)
        projects = extract_projects(sections.get("projects", full_text))

        # Update candidate in DB if session exists
        if self._session_id:
            from database.queries import update_candidate
            session = self.session_manager.get_session(self._session_id)
            if session:
                update_candidate(session["candidate_id"], {
                    "extracted_skills": skills,
                    "extracted_projects": projects,
                    "resume_path": resume_path,
                })

        return skills, projects

    def _generate_questions(
        self,
        skills: List[str],
        projects: List[str],
        count: int,
        difficulty: str,
    ) -> List[Dict[str, Any]]:
        """Generate interview questions."""
        from modules.questions.generator import generate_questions
        return generate_questions(
            skills=skills,
            projects=projects,
            difficulty=difficulty,
            count=count,
        )

    def _extract_keywords(self, question: Dict[str, Any], session: Dict[str, Any]) -> List[str]:
        """Extract expected keywords for a question."""
        skills = session.get("skills", [])
        q_text = question.get("question_text", "").lower()
        # Find skills mentioned in the question
        return [s for s in skills if s.lower() in q_text]

    def _generate_report(self, session: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
        """Generate the full interview report."""
        interview_id = session["interview_id"]

        from database.queries import get_questions_for_interview, get_emotion_timeline
        db_questions = get_questions_for_interview(interview_id)
        emotion_timeline = get_emotion_timeline(interview_id)

        questions = [
            {
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "candidate_answer_text": q.candidate_answer_text,
                "answer_score": q.answer_score,
                "semantic_similarity_score": q.semantic_similarity_score,
                "keyword_match_score": q.keyword_match_score,
                "concept_coverage_score": q.concept_coverage_score,
                "follow_up_questions": q.follow_up_questions,
            }
            for q in db_questions
        ]

        emotion_data = [e.to_dict() for e in emotion_timeline]

        # Calculate metrics
        from modules.analytics.performance_engine import calculate_performance_metrics
        metrics = calculate_performance_metrics(questions, emotion_data)

        # Generate feedback
        from modules.report.feedback_generator import generate_feedback
        feedback = generate_feedback(candidate_name, questions, emotion_data, metrics)

        # Generate charts
        from app.config import GRAPHS_DIR
        from modules.analytics.graph_generator import generate_all_charts
        chart_paths = generate_all_charts(questions, emotion_data, metrics, str(GRAPHS_DIR))

        # Generate PDF
        from modules.report.pdf_report import generate_pdf_report
        interview_data = session
        pdf_path = generate_pdf_report(
            candidate_name=candidate_name,
            interview_data=interview_data,
            questions=questions,
            feedback=feedback,
            metrics=metrics,
            chart_paths=chart_paths,
        )

        # Save report to DB
        from database.models import Report
        from database.queries import create_report
        report = Report(
            interview_id=interview_id,
            pdf_path=pdf_path,
            strengths=feedback.get("strengths", []),
            weaknesses=feedback.get("weaknesses", []),
            suggestions=feedback.get("suggestions", []),
            graphs=chart_paths,
            overall_assessment=feedback.get("overall_assessment", ""),
        )
        create_report(report)

        return {
            "pdf_path": pdf_path,
            "metrics": metrics,
            "feedback": feedback,
            "chart_paths": chart_paths,
        }

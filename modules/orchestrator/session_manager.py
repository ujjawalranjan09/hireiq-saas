"""Session lifecycle management for interview sessions."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages interview session lifecycle."""

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        candidate_id: str,
        interview_id: str,
        skills: List[str] = None,
        projects: List[str] = None,
    ) -> str:
        """Create a new interview session.
        
        Args:
            candidate_id: MongoDB candidate ID.
            interview_id: MongoDB interview ID.
            skills: Candidate's extracted skills.
            projects: Candidate's extracted projects.
            
        Returns:
            Session ID (same as interview_id).
        """
        session_id = interview_id
        self._sessions[session_id] = {
            "candidate_id": candidate_id,
            "interview_id": interview_id,
            "skills": skills or [],
            "projects": projects or [],
            "created_at": datetime.utcnow(),
            "status": "created",
            "current_question_index": 0,
            "questions": [],
            "emotion_snapshots": [],
            "followup_count": 0,
            "total_score": 0.0,
            "score_history": [],
            "audio_files": [],
            "data": {},
        }
        logger.info(f"Session created: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID.
        
        Args:
            session_id: Session ID.
            
        Returns:
            Session data dictionary or None.
        """
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data.
        
        Args:
            session_id: Session ID.
            updates: Dictionary of fields to update.
            
        Returns:
            True if updated successfully.
        """
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False

        self._sessions[session_id].update(updates)
        return True

    def add_question(self, session_id: str, question: Dict[str, Any]) -> bool:
        """Add a question to the session.
        
        Args:
            session_id: Session ID.
            question: Question data.
            
        Returns:
            True if added successfully.
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["questions"].append(question)
        return True

    def add_score(self, session_id: str, score: float) -> bool:
        """Add a score to the session history.
        
        Args:
            session_id: Session ID.
            score: Answer score.
            
        Returns:
            True if added successfully.
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["score_history"].append(score)
        session["total_score"] = sum(session["score_history"]) / len(session["score_history"])
        return True

    def add_emotion_snapshot(self, session_id: str, snapshot: Dict[str, Any]) -> bool:
        """Add an emotion snapshot to the session.
        
        Args:
            session_id: Session ID.
            snapshot: Emotion data.
            
        Returns:
            True if added successfully.
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["emotion_snapshots"].append(snapshot)
        return True

    def add_audio_file(self, session_id: str, audio_path: str) -> bool:
        """Add an audio file reference to the session.
        
        Args:
            session_id: Session ID.
            audio_path: Path to the audio file.
            
        Returns:
            True if added successfully.
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["audio_files"].append(audio_path)
        return True

    def increment_followup(self, session_id: str) -> int:
        """Increment the follow-up counter.
        
        Args:
            session_id: Session ID.
            
        Returns:
            New follow-up count.
        """
        session = self.get_session(session_id)
        if not session:
            return 0

        session["followup_count"] += 1
        return session["followup_count"]

    def reset_followup(self, session_id: str) -> None:
        """Reset the follow-up counter.
        
        Args:
            session_id: Session ID.
        """
        session = self.get_session(session_id)
        if session:
            session["followup_count"] = 0

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics.
        
        Args:
            session_id: Session ID.
            
        Returns:
            Statistics dictionary.
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        scores = session.get("score_history", [])
        return {
            "session_id": session_id,
            "status": session.get("status", "unknown"),
            "questions_asked": len(session.get("questions", [])),
            "current_index": session.get("current_question_index", 0),
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "total_score": session.get("total_score", 0.0),
            "followup_count": session.get("followup_count", 0),
            "emotion_snapshots": len(session.get("emotion_snapshots", [])),
            "audio_files": len(session.get("audio_files", [])),
        }

    def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Close a session and return final data.
        
        Args:
            session_id: Session ID.
            
        Returns:
            Final session data or None.
        """
        session = self.get_session(session_id)
        if session:
            session["status"] = "closed"
            session["closed_at"] = datetime.utcnow()
            logger.info(f"Session closed: {session_id}")
            return session
        return None

    def cleanup(self) -> int:
        """Remove closed sessions from memory.
        
        Returns:
            Number of sessions cleaned up.
        """
        to_remove = [
            sid for sid, data in self._sessions.items()
            if data.get("status") == "closed"
        ]
        for sid in to_remove:
            del self._sessions[sid]
        logger.info(f"Cleaned up {len(to_remove)} sessions")
        return len(to_remove)

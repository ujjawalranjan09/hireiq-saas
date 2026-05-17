"""Data models for the AI Interview Agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId


@dataclass
class Candidate:
    """Candidate data model."""
    name: str
    email: str
    resume_path: str = ""
    extracted_skills: List[str] = field(default_factory=list)
    extracted_projects: List[str] = field(default_factory=list)
    skill_graph: Dict[str, Any] = field(default_factory=dict)
    _id: Optional[ObjectId] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "email": self.email,
            "resume_path": self.resume_path,
            "extracted_skills": self.extracted_skills,
            "extracted_projects": self.extracted_projects,
            "skill_graph": self.skill_graph,
            "created_at": self.created_at,
        }
        if self._id:
            d["_id"] = self._id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candidate":
        return cls(
            name=data.get("name", ""),
            email=data.get("email", ""),
            resume_path=data.get("resume_path", ""),
            extracted_skills=data.get("extracted_skills", []),
            extracted_projects=data.get("extracted_projects", []),
            skill_graph=data.get("skill_graph", {}),
            _id=data.get("_id"),
            created_at=data.get("created_at", datetime.utcnow()),
        )


@dataclass
class Interview:
    """Interview session data model."""
    candidate_id: str
    status: str = "idle"
    difficulty_level: int = 2
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_score: float = 0.0
    final_feedback: Dict[str, Any] = field(default_factory=dict)
    questions_count: int = 10
    _id: Optional[ObjectId] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "candidate_id": self.candidate_id,
            "status": self.status,
            "difficulty_level": self.difficulty_level,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_score": self.total_score,
            "final_feedback": self.final_feedback,
            "questions_count": self.questions_count,
            "created_at": self.created_at,
        }
        if self._id:
            d["_id"] = self._id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Interview":
        return cls(
            candidate_id=str(data.get("candidate_id", "")),
            status=data.get("status", "idle"),
            difficulty_level=data.get("difficulty_level", 2),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            total_score=data.get("total_score", 0.0),
            final_feedback=data.get("final_feedback", {}),
            questions_count=data.get("questions_count", 10),
            _id=data.get("_id"),
            created_at=data.get("created_at", datetime.utcnow()),
        )


@dataclass
class Question:
    """Question data model."""
    interview_id: str
    question_text: str
    question_type: str = "technical"  # resume, technical, behavioral
    difficulty: str = "medium"  # easy, medium, hard, expert
    candidate_answer_text: str = ""
    answer_audio_path: str = ""
    answer_score: float = 0.0
    semantic_similarity_score: float = 0.0
    keyword_match_score: float = 0.0
    concept_coverage_score: float = 0.0
    follow_up_questions: List[str] = field(default_factory=list)
    order: int = 0
    _id: Optional[ObjectId] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "interview_id": self.interview_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "difficulty": self.difficulty,
            "candidate_answer_text": self.candidate_answer_text,
            "answer_audio_path": self.answer_audio_path,
            "answer_score": self.answer_score,
            "semantic_similarity_score": self.semantic_similarity_score,
            "keyword_match_score": self.keyword_match_score,
            "concept_coverage_score": self.concept_coverage_score,
            "follow_up_questions": self.follow_up_questions,
            "order": self.order,
            "timestamp": self.timestamp,
        }
        if self._id:
            d["_id"] = self._id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        return cls(
            interview_id=str(data.get("interview_id", "")),
            question_text=data.get("question_text", ""),
            question_type=data.get("question_type", "technical"),
            difficulty=data.get("difficulty", "medium"),
            candidate_answer_text=data.get("candidate_answer_text", ""),
            answer_audio_path=data.get("answer_audio_path", ""),
            answer_score=data.get("answer_score", 0.0),
            semantic_similarity_score=data.get("semantic_similarity_score", 0.0),
            keyword_match_score=data.get("keyword_match_score", 0.0),
            concept_coverage_score=data.get("concept_coverage_score", 0.0),
            follow_up_questions=data.get("follow_up_questions", []),
            order=data.get("order", 0),
            _id=data.get("_id"),
            timestamp=data.get("timestamp", datetime.utcnow()),
        )


@dataclass
class EmotionSnapshot:
    """Emotion snapshot data model."""
    interview_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    facial_emotion: str = "neutral"
    facial_confidence_score: float = 0.0
    voice_emotion: str = "neutral"
    voice_pitch: float = 0.0
    speaking_speed: float = 0.0  # words per minute
    hesitation_detected: bool = False
    combined_confidence_score: float = 0.0
    _id: Optional[ObjectId] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "interview_id": self.interview_id,
            "timestamp": self.timestamp,
            "facial_emotion": self.facial_emotion,
            "facial_confidence_score": self.facial_confidence_score,
            "voice_emotion": self.voice_emotion,
            "voice_pitch": self.voice_pitch,
            "speaking_speed": self.speaking_speed,
            "hesitation_detected": self.hesitation_detected,
            "combined_confidence_score": self.combined_confidence_score,
        }
        if self._id:
            d["_id"] = self._id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionSnapshot":
        return cls(
            interview_id=str(data.get("interview_id", "")),
            timestamp=data.get("timestamp", datetime.utcnow()),
            facial_emotion=data.get("facial_emotion", "neutral"),
            facial_confidence_score=data.get("facial_confidence_score", 0.0),
            voice_emotion=data.get("voice_emotion", "neutral"),
            voice_pitch=data.get("voice_pitch", 0.0),
            speaking_speed=data.get("speaking_speed", 0.0),
            hesitation_detected=data.get("hesitation_detected", False),
            combined_confidence_score=data.get("combined_confidence_score", 0.0),
            _id=data.get("_id"),
        )


@dataclass
class Report:
    """Report data model."""
    interview_id: str
    pdf_path: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    graphs: Dict[str, str] = field(default_factory=dict)
    overall_assessment: str = ""
    _id: Optional[ObjectId] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "interview_id": self.interview_id,
            "pdf_path": self.pdf_path,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "graphs": self.graphs,
            "overall_assessment": self.overall_assessment,
            "generated_at": self.generated_at,
        }
        if self._id:
            d["_id"] = self._id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Report":
        return cls(
            interview_id=str(data.get("interview_id", "")),
            pdf_path=data.get("pdf_path", ""),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            graphs=data.get("graphs", {}),
            overall_assessment=data.get("overall_assessment", ""),
            _id=data.get("_id"),
            generated_at=data.get("generated_at", datetime.utcnow()),
        )

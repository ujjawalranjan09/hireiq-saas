"""CRUD operations for all MongoDB collections."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from database.connection import get_db
from database.models import Candidate, Interview, Question, EmotionSnapshot, Report

logger = logging.getLogger(__name__)


# ─── Candidate CRUD ───────────────────────────────────────────────────────────

def create_candidate(candidate: Candidate) -> str:
    """Insert a new candidate and return the ID."""
    db = get_db()
    result = db.candidates.insert_one(candidate.to_dict())
    logger.info(f"Created candidate: {result.inserted_id}")
    return str(result.inserted_id)


def get_candidate(candidate_id: str) -> Optional[Candidate]:
    """Get a candidate by ID."""
    db = get_db()
    data = db.candidates.find_one({"_id": ObjectId(candidate_id)})
    if data:
        return Candidate.from_dict(data)
    return None


def get_candidate_by_email(email: str) -> Optional[Candidate]:
    """Get a candidate by email."""
    db = get_db()
    data = db.candidates.find_one({"email": email})
    if data:
        return Candidate.from_dict(data)
    return None


def update_candidate(candidate_id: str, update_data: Dict[str, Any]) -> bool:
    """Update candidate fields."""
    db = get_db()
    result = db.candidates.update_one(
        {"_id": ObjectId(candidate_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0


def list_candidates(limit: int = 50) -> List[Candidate]:
    """List all candidates."""
    db = get_db()
    cursor = db.candidates.find().sort("created_at", -1).limit(limit)
    return [Candidate.from_dict(doc) for doc in cursor]


# ─── Interview CRUD ───────────────────────────────────────────────────────────

def create_interview(interview: Interview) -> str:
    """Create a new interview session."""
    db = get_db()
    result = db.interviews.insert_one(interview.to_dict())
    logger.info(f"Created interview: {result.inserted_id}")
    return str(result.inserted_id)


def get_interview(interview_id: str) -> Optional[Interview]:
    """Get an interview by ID."""
    db = get_db()
    data = db.interviews.find_one({"_id": ObjectId(interview_id)})
    if data:
        return Interview.from_dict(data)
    return None


def update_interview(interview_id: str, update_data: Dict[str, Any]) -> bool:
    """Update interview fields."""
    db = get_db()
    result = db.interviews.update_one(
        {"_id": ObjectId(interview_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0


def get_interviews_for_candidate(candidate_id: str) -> List[Interview]:
    """Get all interviews for a candidate."""
    db = get_db()
    cursor = db.interviews.find({"candidate_id": candidate_id}).sort("created_at", -1)
    return [Interview.from_dict(doc) for doc in cursor]


def get_latest_interview(candidate_id: str) -> Optional[Interview]:
    """Get the most recent interview for a candidate."""
    db = get_db()
    data = db.interviews.find_one(
        {"candidate_id": candidate_id},
        sort=[("created_at", -1)]
    )
    if data:
        return Interview.from_dict(data)
    return None


# ─── Question CRUD ────────────────────────────────────────────────────────────

def create_question(question: Question) -> str:
    """Insert a new question."""
    db = get_db()
    result = db.questions.insert_one(question.to_dict())
    return str(result.inserted_id)


def get_question(question_id: str) -> Optional[Question]:
    """Get a question by ID."""
    db = get_db()
    data = db.questions.find_one({"_id": ObjectId(question_id)})
    if data:
        return Question.from_dict(data)
    return None


def update_question(question_id: str, update_data: Dict[str, Any]) -> bool:
    """Update question fields."""
    db = get_db()
    result = db.questions.update_one(
        {"_id": ObjectId(question_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0


def get_questions_for_interview(interview_id: str) -> List[Question]:
    """Get all questions for an interview, ordered."""
    db = get_db()
    cursor = db.questions.find({"interview_id": interview_id}).sort("order", 1)
    return [Question.from_dict(doc) for doc in cursor]


def bulk_create_questions(questions: List[Question]) -> List[str]:
    """Insert multiple questions at once."""
    if not questions:
        return []
    db = get_db()
    docs = [q.to_dict() for q in questions]
    result = db.questions.insert_many(docs)
    return [str(_id) for _id in result.inserted_ids]


# ─── EmotionSnapshot CRUD ─────────────────────────────────────────────────────

def create_emotion_snapshot(snapshot: EmotionSnapshot) -> str:
    """Insert an emotion snapshot."""
    db = get_db()
    result = db.emotion_timeline.insert_one(snapshot.to_dict())
    return str(result.inserted_id)


def get_emotion_timeline(interview_id: str) -> List[EmotionSnapshot]:
    """Get all emotion snapshots for an interview, ordered by time."""
    db = get_db()
    cursor = db.emotion_timeline.find({"interview_id": interview_id}).sort("timestamp", 1)
    return [EmotionSnapshot.from_dict(doc) for doc in cursor]


def bulk_create_emotion_snapshots(snapshots: List[EmotionSnapshot]) -> List[str]:
    """Insert multiple emotion snapshots at once."""
    if not snapshots:
        return []
    db = get_db()
    docs = [s.to_dict() for s in snapshots]
    result = db.emotion_timeline.insert_many(docs)
    return [str(_id) for _id in result.inserted_ids]


# ─── Report CRUD ──────────────────────────────────────────────────────────────

def create_report(report: Report) -> str:
    """Insert a new report."""
    db = get_db()
    result = db.reports.insert_one(report.to_dict())
    return str(result.inserted_id)


def get_report_for_interview(interview_id: str) -> Optional[Report]:
    """Get a report by interview ID."""
    db = get_db()
    data = db.reports.find_one({"interview_id": interview_id})
    if data:
        return Report.from_dict(data)
    return None


def update_report(report_id: str, update_data: Dict[str, Any]) -> bool:
    """Update report fields."""
    db = get_db()
    result = db.reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0

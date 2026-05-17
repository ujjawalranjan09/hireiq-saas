"""Replay system for reviewing past interviews."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_replay_data(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]],
    interview_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Build replay data structure for reviewing an interview.
    
    Args:
        questions: List of question data with timestamps.
        emotion_timeline: List of emotion snapshots.
        interview_data: Interview session metadata.
        
    Returns:
        Replay data dictionary with timeline, events, and metadata.
    """
    events = []

    # Add question events
    for q in questions:
        timestamp = q.get("timestamp")
        if timestamp:
            if hasattr(timestamp, "isoformat"):
                ts_str = timestamp.isoformat()
            else:
                ts_str = str(timestamp)
        else:
            ts_str = ""

        events.append({
            "type": "question",
            "timestamp": ts_str,
            "data": {
                "question_text": q.get("question_text", ""),
                "question_type": q.get("question_type", ""),
                "difficulty": q.get("difficulty", ""),
                "answer_text": q.get("candidate_answer_text", ""),
                "answer_score": q.get("answer_score", 0),
                "audio_path": q.get("answer_audio_path", ""),
                "order": q.get("order", 0),
            }
        })

    # Add emotion events
    for e in emotion_timeline:
        timestamp = e.get("timestamp")
        if timestamp:
            if hasattr(timestamp, "isoformat"):
                ts_str = timestamp.isoformat()
            else:
                ts_str = str(timestamp)
        else:
            ts_str = ""

        events.append({
            "type": "emotion",
            "timestamp": ts_str,
            "data": {
                "facial_emotion": e.get("facial_emotion", "neutral"),
                "confidence_score": e.get("combined_confidence_score", 50),
                "voice_pitch": e.get("voice_pitch", 0),
                "speaking_speed": e.get("speaking_speed", 0),
                "hesitation_detected": e.get("hesitation_detected", False),
            }
        })

    # Sort events by timestamp
    events.sort(key=lambda x: x.get("timestamp", ""))

    # Build timeline markers for emotions
    emotion_markers = []
    for e in emotion_timeline:
        ts = e.get("timestamp")
        if ts:
            if hasattr(ts, "isoformat"):
                ts_str = ts.isoformat()
            else:
                ts_str = str(ts)
            emotion_markers.append({
                "time": ts_str,
                "emotion": e.get("facial_emotion", "neutral"),
                "confidence": e.get("combined_confidence_score", 50),
            })

    # Build score progression
    score_progression = [
        {
            "order": q.get("order", i),
            "score": q.get("answer_score", 0),
            "type": q.get("question_type", ""),
            "difficulty": q.get("difficulty", ""),
        }
        for i, q in enumerate(questions)
    ]

    return {
        "interview_id": str(interview_data.get("_id", "")),
        "candidate_id": str(interview_data.get("candidate_id", "")),
        "start_time": str(interview_data.get("start_time", "")),
        "end_time": str(interview_data.get("end_time", "")),
        "total_questions": len(questions),
        "events": events,
        "emotion_markers": emotion_markers,
        "score_progression": score_progression,
        "questions": [
            {
                "text": q.get("question_text", ""),
                "type": q.get("question_type", ""),
                "difficulty": q.get("difficulty", ""),
                "score": q.get("answer_score", 0),
                "answer": q.get("candidate_answer_text", ""),
                "audio_path": q.get("answer_audio_path", ""),
            }
            for q in questions
        ],
    }


def get_replay_at_timestamp(
    replay_data: Dict[str, Any],
    target_timestamp: str,
) -> Dict[str, Any]:
    """Get the state of the interview at a specific timestamp.
    
    Args:
        replay_data: Full replay data structure.
        target_timestamp: ISO format timestamp to look up.
        
    Returns:
        State at that point in time.
    """
    events = replay_data.get("events", [])
    events_before = [e for e in events if e.get("timestamp", "") <= target_timestamp]

    current_question = None
    emotion_state = {"emotion": "neutral", "confidence": 50}

    for event in reversed(events_before):
        if event["type"] == "question" and current_question is None:
            current_question = event["data"]
        if event["type"] == "emotion" and emotion_state["emotion"] == "neutral":
            emotion_state = {
                "emotion": event["data"].get("facial_emotion", "neutral"),
                "confidence": event["data"].get("confidence_score", 50),
            }

    return {
        "timestamp": target_timestamp,
        "current_question": current_question,
        "emotion_state": emotion_state,
        "events_so_far": len(events_before),
    }

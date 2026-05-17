# Candidates Schema - Pydantic models for candidate-related API requests/responses
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class InviteRequest(BaseModel):
    """Request schema for inviting candidates to a job."""
    emails: List[EmailStr] = Field(..., description="List of candidate email addresses")


class CandidateListItem(BaseModel):
    """Response schema for a candidate in a list view."""
    id: int
    name: Optional[str] = None
    email: str
    status: str
    overall_score: Optional[float] = None
    rank: Optional[int] = None

    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    """Response schema for a list of candidates."""
    candidates: List[CandidateListItem]
    total: int


class SessionStartResponse(BaseModel):
    """Response schema for starting an interview session."""
    session_id: str
    job_title: str
    questions_count: int
    status: str


class CandidateValidateResponse(BaseModel):
    """Response schema for validating an invite token."""
    valid: bool
    job_title: str
    company_name: str
    candidate_name: Optional[str] = None


class CandidateStatusResponse(BaseModel):
    """Response schema for candidate status."""
    status: str
    overall_score: Optional[float] = None
    completed_at: Optional[datetime] = None


class CandidateDetailResponse(BaseModel):
    """Detailed response schema for a candidate."""
    id: int
    name: Optional[str] = None
    email: str
    status: str
    overall_score: Optional[float] = None
    rank: Optional[int] = None
    invited_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

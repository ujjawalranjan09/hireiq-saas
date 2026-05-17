# Job Schemas - Pydantic models for job-related requests and responses
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class JobStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    min_experience: int = Field(default=0, ge=0)
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    questions_count: int = Field(default=10, ge=1, le=50)

    class Config:
        use_enum_values = True


class JobUpdate(BaseModel):
    """Schema for updating an existing job."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    min_experience: Optional[int] = Field(None, ge=0)
    difficulty_level: Optional[DifficultyLevel] = None
    questions_count: Optional[int] = Field(None, ge=1, le=50)
    status: Optional[JobStatus] = None

    class Config:
        use_enum_values = True


class JobListItem(BaseModel):
    """Schema for a job item in a list."""
    id: int
    title: str
    status: str
    candidate_count: int
    average_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDetailResponse(BaseModel):
    """Schema for detailed job response."""
    id: int
    title: str
    description: Optional[str]
    required_skills: List[str]
    min_experience: int
    difficulty_level: str
    questions_count: int
    status: str
    candidate_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InviteRequest(BaseModel):
    """Schema for inviting candidates to a job (already in candidates/schemas but duplicated here for convenience)."""
    emails: List[str] = Field(..., min_length=1)

    class Config:
        # Validate email format
        pass

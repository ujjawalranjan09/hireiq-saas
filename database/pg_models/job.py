# Job Model - represents a job listing created by an HR user
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from database.postgres import Base


class JobStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    required_skills: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)
    min_years_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(
        SQLEnum(DifficultyLevel), 
        default=DifficultyLevel.MEDIUM, 
        nullable=False
    )
    questions_count: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(JobStatus), 
        default=JobStatus.ACTIVE, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    creator = relationship("User", back_populates="jobs")
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', status='{self.status}')>"

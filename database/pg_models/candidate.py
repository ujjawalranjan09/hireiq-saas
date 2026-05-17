# Candidate Model - represents one candidate invited for one specific job
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
import secrets

from database.postgres import Base


class CandidateStatus(str, enum.Enum):
    INVITED = "invited"
    STARTED = "started"
    COMPLETED = "completed"
    EXPIRED = "expired"


def generate_invite_token() -> str:
    """Generate a secure random invite token."""
    return secrets.token_urlsafe(32)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    invite_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, default=generate_invite_token)
    token_expiry: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(CandidateStatus), 
        default=CandidateStatus.INVITED, 
        nullable=False
    )
    mongo_session_id: Mapped[str] = mapped_column(String(255), nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=True)
    invited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="candidates")
    company = relationship("Company")

    def __repr__(self):
        return f"<Candidate(id={self.id}, email='{self.email}', status='{self.status}')>"

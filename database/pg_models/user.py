# User Model - represents an HR user inside a company
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from database.postgres import Base


class UserRole(str, enum.Enum):
    HR = "hr"
    ADMIN = "admin"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(SQLEnum(UserRole), default=UserRole.HR, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to company
    company = relationship("Company", back_populates="users")
    jobs = relationship("Job", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

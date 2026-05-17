# Company Model - represents a hiring company
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from database.postgres import Base


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=True)
    subscription_plan: Mapped[str] = mapped_column(
        SQLEnum(SubscriptionPlan), 
        default=SubscriptionPlan.FREE, 
        nullable=False
    )
    interviews_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interviews_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', plan='{self.subscription_plan}')>"

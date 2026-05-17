# Pydantic schemas for authentication
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    company_name: str = Field(..., min_length=1, description="Company name is required")


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    user_id: int
    company_id: int
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User info response schema."""
    id: int
    email: str
    role: str
    company_id: int
    company_name: str
    is_active: bool

    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    """Company info response schema."""
    id: int
    name: str
    domain: Optional[str] = None
    subscription_plan: str
    interviews_used: int
    interviews_limit: int
    created_at: datetime

    class Config:
        from_attributes = True

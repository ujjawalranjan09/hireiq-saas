# Pydantic schemas for authentication
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    company_name: str = Field(..., min_length=1, description="Company name is required")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


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


class RefreshRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


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

# Auth Router - Authentication endpoints (register, login, refresh)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from database.postgres import get_db
from database.pg_models.company import Company, SubscriptionPlan
from database.pg_models.user import User, UserRole
from saas.auth.service import hash_password, verify_password, create_access_token, create_refresh_token
from saas.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, RefreshRequest
from saas.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new company and admin user.
    
    Creates a new company with the free plan and an admin user.
    Returns access and refresh tokens.
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create company
    company = Company(
        name=request.company_name,
        subscription_plan=SubscriptionPlan.FREE,
        interviews_used=0,
        interviews_limit=10  # Free tier limit
    )
    db.add(company)
    await db.flush()  # Get company ID
    
    # Create admin user
    user = User(
        company_id=company.id,
        email=request.email,
        hashed_password=hash_password(request.password),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    await db.flush()
    
    # Create tokens
    token_data = {
        "user_id": user.id,
        "company_id": company.id,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        company_id=company.id
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.
    
    Verifies credentials and returns access and refresh tokens.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    token_data = {
        "user_id": user.id,
        "company_id": user.company_id,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        company_id=user.company_id
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Accepts a refresh token and returns a new access token.
    """
    refresh_token_str = request.refresh_token
    
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    # Import here to avoid circular imports
    from saas.auth.service import verify_token
    
    # Verify the refresh token
    payload = verify_token(refresh_token_str, token_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("user_id")
    company_id = payload.get("company_id")
    
    if user_id is None or company_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    token_data = {
        "user_id": user.id,
        "company_id": user.company_id,
        "email": user.email,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,  # Return same refresh token
        user_id=user.id,
        company_id=user.company_id
    )

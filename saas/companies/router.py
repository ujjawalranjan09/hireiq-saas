# Companies Router - Company management endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database.postgres import get_db
from database.pg_models.company import Company
from database.pg_models.user import User
from saas.auth.dependencies import get_current_user, require_role
from saas.auth.schemas import CompanyResponse, UserResponse

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/me", response_model=CompanyResponse)
async def get_current_company(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current company's info and usage stats.
    
    Returns information about the company associated with the authenticated user.
    """
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company


@router.put("/me", response_model=CompanyResponse)
async def update_current_company(
    name: Optional[str] = None,
    domain: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current company's name or domain.
    
    Only admin users can update company information.
    """
    # Check if user has admin role
    from database.pg_models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update company information"
        )
    
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Update fields if provided
    if name is not None:
        company.name = name
    
    if domain is not None:
        company.domain = domain
    
    # Mark for update (SQLAlchemy will handle it on commit)
    db.add(company)
    
    return company

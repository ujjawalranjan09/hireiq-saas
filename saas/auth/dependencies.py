# FastAPI dependencies for authentication and authorization
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database.postgres import get_db
from database.pg_models.user import User, UserRole
from saas.auth.service import verify_token


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Reads the Bearer token from Authorization header, decodes it,
    looks up the user in PostgreSQL, and returns the user object.
    
    Raises 401 if token is invalid or user does not exist.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Verify the access token
    payload = verify_token(token, token_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Look up the user in the database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(*allowed_roles: str):
    """
    Factory function that returns a dependency to check user role.
    
    Args:
        allowed_roles: One or more role names that are allowed (e.g., "admin", "hr")
    
    Returns:
        A FastAPI dependency function that raises 403 if user's role is not allowed
    """
    allowed_role_enums = [UserRole(role) for role in allowed_roles]
    
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_role_enums:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker

# Tenant Middleware - Enriches request state with company_id from JWT token
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from jose import jwt, JWTError
import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key_here_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that runs on every single request.
    
    Reads the Bearer token from the Authorization header, decodes it,
    and stores the company_id from the payload in request.state.company_id.
    
    If there is no token, it sets request.state.company_id to None.
    This middleware never rejects requests — it only enriches the request state.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Initialize company_id as None
        request.state.company_id = None
        
        # Get Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            try:
                # Decode the JWT token
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                
                # Extract company_id from payload
                company_id = payload.get("company_id")
                if company_id is not None:
                    request.state.company_id = int(company_id)
            except JWTError:
                # Token is invalid, but we don't reject the request
                # Just leave company_id as None
                pass
            except (ValueError, TypeError):
                # company_id couldn't be converted to int
                pass
        
        # Continue with the request
        response = await call_next(request)
        return response

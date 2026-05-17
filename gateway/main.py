# Gateway Main - FastAPI Application Entry Point
# This file creates the FastAPI application, adds middleware, and includes all routers

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import middleware
from saas.middleware.tenant import TenantMiddleware
from saas.middleware.rate_limit import RateLimitMiddleware

# Import routers
from saas.auth.router import router as auth_router
from saas.companies.router import router as companies_router
from saas.jobs.router import router as jobs_router
from saas.candidates.router import router as candidates_router
from saas.dashboard.router import router as dashboard_router

# Environment variables
HR_DASHBOARD_BASE_URL = os.getenv("HR_DASHBOARD_BASE_URL", "http://localhost:5173")
CANDIDATE_PORTAL_BASE_URL = os.getenv("CANDIDATE_PORTAL_BASE_URL", "http://localhost:5174")

# API Version
API_VERSION = "1.0.0"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="HireIQ SaaS API",
        description="API for HireIQ SaaS platform - AI-powered interview system",
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            HR_DASHBOARD_BASE_URL,
            CANDIDATE_PORTAL_BASE_URL,
            "http://localhost:5173",
            "http://localhost:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Tenant middleware (enriches request state with company_id)
    app.add_middleware(TenantMiddleware)
    
    # Add Rate Limit middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(companies_router)
    app.include_router(jobs_router)
    app.include_router(candidates_router)
    app.include_router(dashboard_router)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.
        
        Returns API version and status.
        """
        return {
            "status": "ok",
            "version": API_VERSION
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

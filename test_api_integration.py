"""
API Integration Tests for HireIQ SaaS
Tests the FastAPI application endpoints using TestClient
"""
import pytest
import sys
import os

sys.path.insert(0, '/workspace')

os.environ['POSTGRES_URL'] = 'postgresql+asyncpg://test:test@localhost/test'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-rigorous-testing-1234567890'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['MAIL_USERNAME'] = 'test@test.com'
os.environ['MAIL_PASSWORD'] = 'password'
os.environ['CANDIDATE_PORTAL_BASE_URL'] = 'http://localhost:5174'
os.environ['HR_DASHBOARD_BASE_URL'] = 'http://localhost:5173'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017'


class TestFastAPIApplication:
    """Test the FastAPI application structure and configuration."""
    
    def test_app_creation(self):
        """Test that the FastAPI app can be created."""
        from gateway.main import app
        assert app is not None
        assert app.title == "HireIQ SaaS API"
        
    def test_health_endpoint_exists(self):
        """Test that the health endpoint is registered."""
        from gateway.main import app
        routes = [route.path for route in app.routes]
        assert '/health' in routes
        
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        from gateway.main import app
        # Check if CORS middleware is in the stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert 'CORSMiddleware' in middleware_classes
        
    def test_tenant_middleware_configured(self):
        """Test that Tenant middleware is configured."""
        from gateway.main import app
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert 'TenantMiddleware' in middleware_classes


class TestAuthRouter:
    """Test authentication router configuration."""
    
    def test_auth_router_exists(self):
        """Test that auth router is properly configured."""
        from saas.auth.router import router
        assert router is not None
        routes = [route.path for route in router.routes]
        assert '/auth/register' in routes
        assert '/auth/login' in routes
        assert '/auth/refresh' in routes


class TestJobsRouter:
    """Test jobs router configuration."""
    
    def test_jobs_router_exists(self):
        """Test that jobs router is properly configured."""
        from saas.jobs.router import router
        assert router is not None
        routes = [route.path for route in router.routes]
        assert '/jobs/' in routes
        assert '/jobs/{job_id}' in routes


class TestCandidatesRouter:
    """Test candidates router configuration."""
    
    def test_candidates_router_exists(self):
        """Test that candidates router is properly configured."""
        from saas.candidates.router import router
        assert router is not None
        routes = [route.path for route in router.routes]
        assert '/candidates/{token}/validate' in routes
        assert '/candidates/{token}/start' in routes
        assert '/candidates/{token}/status' in routes
        assert '/candidates/{token}/report' in routes


class TestDashboardRouter:
    """Test dashboard router configuration."""
    
    def test_dashboard_router_exists(self):
        """Test that dashboard router is properly configured."""
        from saas.dashboard.router import router
        assert router is not None
        routes = [route.path for route in router.routes]
        assert '/analytics/dashboard' in routes
        assert '/analytics/jobs/{job_id}' in routes


class TestCompaniesRouter:
    """Test companies router configuration."""
    
    def test_companies_router_exists(self):
        """Test that companies router is properly configured."""
        from saas.companies.router import router
        assert router is not None
        routes = [route.path for route in router.routes]
        assert '/companies/me' in routes


class TestDatabaseModelsIntegration:
    """Test database models integration."""
    
    def test_all_models_importable(self):
        """Test that all database models can be imported."""
        from database.pg_models.company import Company
        from database.pg_models.user import User
        from database.pg_models.job import Job
        from database.pg_models.candidate import Candidate
        
        assert Company.__tablename__ == 'companies'
        assert User.__tablename__ == 'users'
        assert Job.__tablename__ == 'jobs'
        assert Candidate.__tablename__ == 'candidates'
        
    def test_model_relationships(self):
        """Test that model relationships are properly defined."""
        from database.pg_models.company import Company
        from database.pg_models.user import User
        
        # Company should have users relationship
        assert hasattr(Company, 'users')
        assert hasattr(Company, 'jobs')
        
        # User should have company relationship
        assert hasattr(User, 'company')


class TestInterviewBridgeIntegration:
    """Test interview bridge integration."""
    
    def test_all_functions_exist(self):
        """Test that all required bridge functions exist."""
        from saas.candidates.interview_bridge import (
            validate_invite_token,
            check_company_quota,
            start_session,
            complete_session
        )
        
        assert callable(validate_invite_token)
        assert callable(check_company_quota)
        assert callable(start_session)
        assert callable(complete_session)
        
    def test_bridge_no_forbidden_imports(self):
        """Test that bridge doesn't import forbidden modules."""
        import ast
        
        with open('/workspace/saas/candidates/interview_bridge.py', 'r') as f:
            tree = ast.parse(f.read())
        
        forbidden = ['saas.auth', 'saas.jobs', 'saas.companies', 'saas.dashboard']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for f in forbidden:
                        assert not node.module.startswith(f), f"Forbidden import: {node.module}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for f in forbidden:
                        assert not alias.name.startswith(f), f"Forbidden import: {alias.name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

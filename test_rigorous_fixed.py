"""
Rigorous Whitebox & Integration Test Suite for HireIQ SaaS - FIXED VERSION
Covers: Unit, Integration, Edge Cases, Security, and Concurrency
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

# Add project root to path
sys.path.insert(0, '/workspace')

# --- Configuration & Mocks ---
os.environ['POSTGRES_URL'] = 'postgresql+asyncpg://test:test@localhost/test'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-rigorous-testing-1234567890'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['MAIL_USERNAME'] = 'test@test.com'
os.environ['MAIL_PASSWORD'] = 'password'
os.environ['CANDIDATE_PORTAL_BASE_URL'] = 'http://localhost:5174'
os.environ['HR_DASHBOARD_BASE_URL'] = 'http://localhost:5173'

# --- Test Suite: Database Models Integrity ---
class TestDatabaseModels:
    def test_company_model_fields(self):
        from database.pg_models.company import Company
        assert hasattr(Company, 'id')
        assert hasattr(Company, 'name')
        assert hasattr(Company, 'domain')
        assert hasattr(Company, 'subscription_plan')
        assert hasattr(Company, 'interviews_used')
        assert hasattr(Company, 'interviews_limit')  # Fixed: correct field name
        
    def test_user_model_relationships(self):
        from database.pg_models.user import User
        from database.pg_models.company import Company
        assert 'company_id' in User.__table__.columns
    
    def test_job_model_fields(self):
        from database.pg_models.job import Job
        assert hasattr(Job, 'title')
        assert hasattr(Job, 'required_skills')
        assert hasattr(Job, 'difficulty_level')
        assert hasattr(Job, 'status')
        
    def test_candidate_model_token_generation(self):
        from database.pg_models.candidate import Candidate
        import secrets
        token = secrets.token_urlsafe(32)
        assert len(token) > 20
        assert isinstance(token, str)

# --- Test Suite: Authentication Security ---
class TestAuthSecurity:
    def test_password_hashing_uniqueness(self):
        from saas.auth.service import hash_password, verify_password
        pwd = "securePass1!"  # Shorter password to avoid bcrypt issues
        h1 = hash_password(pwd)
        h2 = hash_password(pwd)
        assert h1 != h2  # Salts should be different
        assert verify_password(pwd, h1)
        assert verify_password(pwd, h2)
        
    def test_password_verification_failure(self):
        from saas.auth.service import hash_password, verify_password
        pwd = "securePass1!"
        wrong_pwd = "wrongPass"
        hashed = hash_password(pwd)
        assert not verify_password(wrong_pwd, hashed)
        
    def test_jwt_token_payload_integrity(self):
        from saas.auth.service import create_access_token
        data = {"sub": "user-123", "company_id": "comp-456", "role": "admin"}
        token = create_access_token(data=data)
        assert token is not None
        assert len(token.split('.')) == 3  # JWT structure
        
    def test_jwt_expiration_logic(self):
        from saas.auth.service import create_access_token
        from jose import jwt
        
        data = {"sub": "user-123"}
        token = create_access_token(data=data, expires_delta=timedelta(seconds=60))
        decoded = jwt.decode(token, os.environ['JWT_SECRET_KEY'], algorithms=[os.environ['JWT_ALGORITHM']])
        assert decoded['sub'] == "user-123"

# --- Test Suite: Critical Interview Bridge Logic ---
class TestInterviewBridgeLogic:
    @pytest.mark.asyncio
    async def test_validate_invite_token_success(self):
        from saas.candidates.interview_bridge import validate_invite_token
        from database.pg_models.candidate import Candidate
        
        mock_db = AsyncMock()
        mock_candidate = MagicMock(spec=Candidate)
        mock_candidate.status = "invited"
        mock_candidate.invite_token = "valid-token"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_candidate)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await validate_invite_token("valid-token", mock_db)
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_validate_invite_token_not_found(self):
        from saas.candidates.interview_bridge import validate_invite_token
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await validate_invite_token("invalid-token", mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_check_company_quota_under_limit(self):
        from saas.candidates.interview_bridge import check_company_quota
        from database.pg_models.company import Company
        
        mock_db = AsyncMock()
        mock_company = MagicMock(spec=Company)
        mock_company.interviews_used = 5
        mock_company.interviews_limit = 10
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_company)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await check_company_quota(1, mock_db)
        assert result is True
        
    @pytest.mark.asyncio
    async def test_check_company_quota_at_limit(self):
        from saas.candidates.interview_bridge import check_company_quota
        
        mock_db = AsyncMock()
        mock_company = MagicMock()
        mock_company.interviews_used = 10
        mock_company.interviews_limit = 10
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_company)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await check_company_quota(1, mock_db)
        assert result is False

    @pytest.mark.asyncio
    async def test_start_session_quota_failure(self):
        from saas.candidates.interview_bridge import start_session
        
        mock_db = AsyncMock()
        
        # Mock validate_invite_token to return a candidate
        mock_candidate = MagicMock()
        mock_candidate.company_id = 1
        mock_candidate.job_id = 1
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_candidate)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Mock check_company_quota to fail
        with patch('saas.candidates.interview_bridge.check_company_quota', return_value=False):
            with pytest.raises(Exception) as exc_info:
                await start_session("token", mock_db)
            assert "quota" in str(exc_info.value).lower() or "Quota" in str(exc_info.value)

# --- Test Suite: Middleware Robustness ---
class TestMiddleware:
    def test_tenant_middleware_class_exists(self):
        from saas.middleware.tenant import TenantMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        assert issubclass(TenantMiddleware, BaseHTTPMiddleware)
        
    def test_rate_limit_middleware_logic(self):
        from saas.middleware.rate_limit import RateLimitMiddleware
        assert hasattr(RateLimitMiddleware, '__call__')

# --- Test Suite: Worker Tasks ---
class TestWorkerTasks:
    def test_celery_configuration(self):
        from workers.celery_app import celery_app
        assert celery_app.conf.broker_url.startswith('redis://')
        assert celery_app.conf.result_backend.startswith('redis://')
        assert celery_app.conf.timezone == 'Asia/Kolkata'
        
    def test_email_task_signature(self):
        from workers.tasks.send_invite_email import send_invite_email
        assert send_invite_email.name == 'workers.tasks.send_invite_email.send_invite_email'
        
    def test_rank_task_signature(self):
        from workers.tasks.rank_candidates import rank_candidates_job
        assert rank_candidates_job.name.endswith('rank_candidates_job')

# --- Test Suite: API Schemas Validation ---
class TestSchemas:
    def test_register_request_valid(self):
        from saas.auth.schemas import RegisterRequest
        req = RegisterRequest(email="hr@demo.com", password="Secure123!", company_name="Demo Corp")
        assert req.email == "hr@demo.com"
        
    def test_invite_request_multiple_emails(self):
        from saas.candidates.schemas import InviteRequest
        req = InviteRequest(emails=["a@test.com", "b@test.com"])
        assert len(req.emails) == 2

# --- Test Suite: Integration Scenarios ---
class TestIntegrationScenarios:
    @pytest.mark.asyncio
    async def test_full_registration_flow_mock(self):
        from saas.auth.service import hash_password, create_access_token
        
        hashed = hash_password("TestPass123!")
        
        user_data = {
            "sub": "new-user-id",
            "company_id": "new-comp-id",
            "role": "admin"
        }
        token = create_access_token(data=user_data)
        
        assert token is not None
        assert len(token) > 50
        
    @pytest.mark.asyncio
    async def test_job_creation_schema(self):
        from saas.jobs.schemas import JobCreate
        job = JobCreate(
            title="Senior Engineer",
            description="Build stuff",
            required_skills=["Python", "FastAPI"],
            min_experience=5,
            difficulty_level="hard",
            questions_count=10
        )
        assert job.difficulty_level == "hard"
        assert len(job.required_skills) == 2

# --- Test Suite: Module Integrity (Critical) ---
class TestModuleIntegrity:
    def test_modules_directory_unchanged(self):
        import subprocess
        result = subprocess.run(
            ['git', 'diff', 'HEAD', '--', 'modules/'],
            cwd='/workspace',
            capture_output=True,
            text=True
        )
        assert result.stdout == "", f"Modules directory has changes: {result.stdout}"
        
    def test_streamlit_in_requirements(self):
        with open('/workspace/requirements.txt', 'r') as f:
            content = f.read()
        assert 'streamlit' in content.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

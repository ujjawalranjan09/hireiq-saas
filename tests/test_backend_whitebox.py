"""Whitebox Tests for HireIQ SaaS Backend - No pytest dependency"""
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["POSTGRES_URL"] = "postgresql+asyncpg://test:test@localhost/test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-12345678"
os.environ["JWT_ALGORITHM"] = "HS256"

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"✓ {name}")
        passed += 1
    else:
        print(f"✗ {name}")
        failed += 1

print("=" * 60)
print("HireIQ SaaS Backend - Whitebox Tests")
print("=" * 60)

# Database Models
print("\n[Database Models]")
try:
    from database.pg_models.company import Company
    test("Company model has id", hasattr(Company, 'id'))
    test("Company model has name", hasattr(Company, 'name'))
    test("Company model has domain", hasattr(Company, 'domain'))
except Exception as e:
    test(f"Company model import: {e}", False)

try:
    from database.pg_models.user import User
    test("User model has id", hasattr(User, 'id'))
    test("User model has email", hasattr(User, 'email'))
    test("User model has hashed_password", hasattr(User, 'hashed_password'))
except Exception as e:
    test(f"User model import: {e}", False)

try:
    from database.pg_models.job import Job
    test("Job model has id", hasattr(Job, 'id'))
    test("Job model has title", hasattr(Job, 'title'))
    test("Job model has required_skills", hasattr(Job, 'required_skills'))
except Exception as e:
    test(f"Job model import: {e}", False)

try:
    from database.pg_models.candidate import Candidate
    test("Candidate model has id", hasattr(Candidate, 'id'))
    test("Candidate model has invite_token", hasattr(Candidate, 'invite_token'))
    test("Candidate model has status", hasattr(Candidate, 'status'))
except Exception as e:
    test(f"Candidate model import: {e}", False)

# Auth Service
print("\n[Auth Service]")
try:
    from saas.auth.service import hash_password, verify_password
    hashed = hash_password("testpass")
    test("hash_password returns non-empty string", hashed is not None and len(hashed) > 0)
    test("verify_password correct", verify_password("testpass", hashed) is True)
    test("verify_password incorrect", verify_password("wrongpass", hashed) is False)
except Exception as e:
    test(f"Auth service: {e}", False)

try:
    from saas.auth.service import create_access_token, create_refresh_token
    token = create_access_token(data={"sub": "1", "company_id": 1, "role": "admin"})
    test("create_access_token returns JWT", token is not None and "." in token)
    refresh = create_refresh_token(data={"sub": "1", "company_id": 1})
    test("create_refresh_token returns JWT", refresh is not None and "." in token)
except Exception as e:
    test(f"Token creation: {e}", False)

try:
    from saas.auth.service import create_access_token
    from jose import jwt
    token = create_access_token(data={"sub": "42", "company_id": 99, "role": "hr"})
    payload = jwt.decode(token, os.environ["JWT_SECRET_KEY"], algorithms=[os.environ["JWT_ALGORITHM"]])
    test("Token contains user_id", payload["sub"] == "42")
    test("Token contains company_id", payload["company_id"] == 99)
    test("Token contains role", payload["role"] == "hr")
except Exception as e:
    test(f"Token payload: {e}", False)

# Schemas
print("\n[Schemas]")
try:
    from saas.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
    req = RegisterRequest(email="test@example.com", password="pass123", company_name="Test Corp")
    test("RegisterRequest schema works", req.email == "test@example.com")
    login = LoginRequest(email="test@example.com", password="pass123")
    test("LoginRequest schema works", login.email == "test@example.com")
    resp = TokenResponse(access_token="abc", refresh_token="def", user_id=1, company_id=1)
    test("TokenResponse schema works", resp.user_id == 1)
except Exception as e:
    test(f"Auth schemas: {e}", False)

try:
    from saas.candidates.schemas import InviteRequest, CandidateListItem, SessionStartResponse
    invite = InviteRequest(emails=["a@test.com", "b@test.com"])
    test("InviteRequest schema works", len(invite.emails) == 2)
    item = CandidateListItem(id=1, name="John", email="j@test.com", status="completed", overall_score=85.0, rank=1)
    test("CandidateListItem schema works", item.overall_score == 85.0)
    sess = SessionStartResponse(session_id="sess_123", job_title="Dev", questions_count=10, status="started")
    test("SessionStartResponse schema works", sess.questions_count == 10)
except Exception as e:
    test(f"Candidate schemas: {e}", False)

# Interview Bridge
print("\n[Interview Bridge]")
try:
    from saas.candidates.interview_bridge import validate_invite_token, check_company_quota
    test("validate_invite_token function exists", callable(validate_invite_token))
    test("check_company_quota function exists", callable(check_company_quota))
except Exception as e:
    test(f"Interview bridge import: {e}", False)

try:
    from saas.candidates.interview_bridge import start_session, complete_session
    test("start_session function exists", callable(start_session))
    test("complete_session function exists", callable(complete_session))
except Exception as e:
    test(f"Bridge session functions: {e}", False)

# Middleware
print("\n[Middleware]")
try:
    from saas.middleware.tenant import TenantMiddleware
    test("TenantMiddleware class exists", TenantMiddleware is not None)
except Exception as e:
    test(f"Tenant middleware: {e}", False)

try:
    from saas.middleware.rate_limit import RateLimitMiddleware
    test("RateLimitMiddleware class exists", RateLimitMiddleware is not None)
except Exception as e:
    test(f"Rate limit middleware: {e}", False)

# Workers
print("\n[Workers]")
try:
    from workers.celery_app import celery_app
    test("Celery app exists", celery_app is not None)
    test("Celery broker is Redis", celery_app.conf.broker_url.startswith("redis://"))
except Exception as e:
    test(f"Celery app: {e}", False)

try:
    from workers.tasks.send_invite_email import send_invite_email
    test("send_invite_email task exists", send_invite_email is not None)
except Exception as e:
    test(f"Email task: {e}", False)

try:
    from workers.tasks.rank_candidates import rank_candidates_job
    test("rank_candidates_job task exists", rank_candidates_job is not None)
except Exception as e:
    test(f"Rank task: {e}", False)

try:
    from workers.tasks.generate_report import generate_report
    test("generate_report task exists", generate_report is not None)
except Exception as e:
    test(f"Report task: {e}", False)

# Routers
print("\n[API Routers]")
try:
    from saas.auth.router import router as auth_router
    routes = [r.path for r in auth_router.routes]
    test("/auth/register endpoint exists", "/auth/register" in routes)
    test("/auth/login endpoint exists", "/auth/login" in routes)
    test("/auth/refresh endpoint exists", "/auth/refresh" in routes)
except Exception as e:
    test(f"Auth router: {e}", False)

try:
    from saas.jobs.router import router as jobs_router
    routes = [r.path for r in jobs_router.routes]
    test("Jobs router has /jobs/ endpoints", any("/jobs/" in r for r in routes))
except Exception as e:
    test(f"Jobs router: {e}", False)

try:
    from saas.candidates.router import router as candidates_router
    routes = [r.path for r in candidates_router.routes]
    test("Candidates router has /candidates/ endpoints", any("/candidates/" in r for r in routes))
except Exception as e:
    test(f"Candidates router: {e}", False)

try:
    from saas.dashboard.router import router as dashboard_router
    routes = [r.path for r in dashboard_router.routes]
    test("Dashboard router has /analytics endpoints", any("/analytics" in r for r in routes))
except Exception as e:
    test(f"Dashboard router: {e}", False)

# FastAPI App
print("\n[FastAPI Application]")
try:
    from gateway.main import app
    test("FastAPI app created", app is not None)
    test("App title is correct", app.title == "HireIQ SaaS API")
    routes = [r.path for r in app.routes]
    test("/health endpoint exists", "/health" in routes)
    test("Auth routes included", any("/auth" in r for r in routes))
    test("Jobs routes included", any("/jobs" in r for r in routes))
    test("Candidates routes included", any("/candidates" in r for r in routes))
except Exception as e:
    test(f"FastAPI app: {e}", False)

# Integrity Checks
print("\n[Integrity Checks]")
modules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'modules')
test("modules directory exists", os.path.exists(modules_path))

req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'requirements.txt')
with open(req_path, 'r') as f:
    content = f.read()
test("streamlit preserved in requirements.txt", "streamlit" in content)

# Summary
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    sys.exit(1)
else:
    print("\n✓ All whitebox tests passed!")
    sys.exit(0)

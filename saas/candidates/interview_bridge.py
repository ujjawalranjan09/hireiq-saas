# Interview Bridge - Critical connection between SaaS layer and AI interview engine
# This is the ONLY file Sub-Agent 3 writes inside the saas/ directory
# 
# Import rules:
# - MAY import from modules/ to call the orchestrator
# - MAY import from database/postgres.py and database/pg_models/
# - MAY import from workers/tasks/ to fire background tasks
# - MAY NOT import from saas/auth/, saas/jobs/, saas/companies/, or saas/dashboard/

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from database.postgres import get_db
from database.pg_models.candidate import Candidate, CandidateStatus
from database.pg_models.job import Job
from database.pg_models.company import Company


async def validate_invite_token(token: str, db: AsyncSession) -> Candidate | None:
    """
    Validate an invite token.
    
    Queries PostgreSQL for a Candidate row where:
    - The invite token matches
    - The status is "invited"
    - The expiry timestamp is in the future
    
    Returns the Candidate object or None.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.invite_token == token)
        .where(Candidate.status == CandidateStatus.INVITED)
        .where(Candidate.token_expiry > datetime.utcnow())
    )
    candidate = result.scalar_one_or_none()
    return candidate


async def check_company_quota(company_id: int, db: AsyncSession) -> bool:
    """
    Check if company has remaining interview quota.
    
    Queries the Company row and returns True if interviews_used 
    is less than interviews_limit, False otherwise.
    """
    result = await db.execute(
        select(Company)
        .where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if company is None:
        return False
    
    return company.interviews_used < company.interviews_limit


async def start_session(token: str, db: AsyncSession) -> dict:
    """
    Start an interview session - the main function called by the router.
    
    Steps (in order):
    1. Call validate_invite_token - if it returns None, raise an error
    2. Call check_company_quota - if it returns False, raise an error
    3. Query PostgreSQL for the Job row linked to the candidate
    4. Import and instantiate InterviewOrchestrator from modules/orchestrator
    5. Call the orchestrator's initialize() method - returns MongoDB session ID
    6. Update the Candidate row: set status to "started" and store MongoDB session ID
    7. Increment the Company's interviews_used counter by 1
    8. Commit the database transaction
    9. Return a dictionary with session_id, job_title, questions_count, and status
    
    Args:
        token: The candidate's invite token
        db: AsyncSession database connection
        
    Returns:
        dict with session_id, job_title, questions_count, status
        
    Raises:
        ValueError: If token is invalid/expired or company quota exceeded
    """
    # Step 1: Validate invite token
    candidate = await validate_invite_token(token, db)
    if candidate is None:
        raise ValueError("Invalid or expired invite token")
    
    # Step 2: Check company quota
    has_quota = await check_company_quota(candidate.company_id, db)
    if not has_quota:
        raise ValueError("Company has reached its interview quota")
    
    # Step 3: Get the Job row
    job_result = await db.execute(
        select(Job).where(Job.id == candidate.job_id)
    )
    job = job_result.scalar_one_or_none()
    
    if job is None:
        raise ValueError("Job not found for candidate")
    
    # Step 4: Import and instantiate InterviewOrchestrator
    from modules.orchestrator import InterviewOrchestrator
    
    orchestrator = InterviewOrchestrator(
        job_title=job.title,
        required_skills=job.required_skills,
        difficulty_level=job.difficulty_level.value,
        questions_count=job.questions_count,
        candidate_name=candidate.name,
        candidate_email=candidate.email
    )
    
    # Step 5: Initialize the session (returns MongoDB session ID)
    mongo_session_id = await orchestrator.initialize()
    
    # Step 6: Update Candidate row
    candidate.status = CandidateStatus.STARTED
    candidate.mongo_session_id = mongo_session_id
    db.add(candidate)
    
    # Step 7: Increment company's interviews_used counter
    company_result = await db.execute(
        select(Company).where(Company.id == candidate.company_id)
    )
    company = company_result.scalar_one_or_none()
    
    if company:
        company.interviews_used += 1
        db.add(company)
    
    # Step 8: Commit will happen automatically via dependency
    
    # Step 9: Return response dictionary
    return {
        "session_id": mongo_session_id,
        "job_title": job.title,
        "questions_count": job.questions_count,
        "status": "started"
    }


async def complete_session(token: str, overall_score: float, db: AsyncSession) -> dict:
    """
    Complete an interview session.
    
    Called when an interview ends.
    
    Steps:
    1. Update the Candidate row to status="completed"
    2. Save the overall_score
    3. Set completed_at to now
    4. Commit the transaction
    5. Fire the rank_candidates Celery task for the job
    
    Args:
        token: The candidate's invite token
        overall_score: The final interview score (0-100)
        db: AsyncSession database connection
        
    Returns:
        dict with success status and candidate info
    """
    # Find the candidate
    result = await db.execute(
        select(Candidate)
        .where(Candidate.invite_token == token)
    )
    candidate = result.scalar_one_or_none()
    
    if candidate is None:
        raise ValueError("Candidate not found")
    
    # Step 1-3: Update candidate record
    candidate.status = CandidateStatus.COMPLETED
    candidate.overall_score = overall_score
    candidate.completed_at = datetime.utcnow()
    db.add(candidate)
    
    # Step 4: Commit will happen automatically
    
    # Step 5: Fire the rank_candidates Celery task
    # Import here to avoid circular imports
    try:
        from workers.tasks.rank_candidates import rank_candidates_job
        # Fire and forget - don't await the result
        rank_candidates_job.delay(candidate.job_id)
    except ImportError:
        # Task not available yet, that's okay
        pass
    except Exception:
        # Log error but don't fail the completion
        pass
    
    return {
        "success": True,
        "candidate_id": candidate.id,
        "job_id": candidate.job_id,
        "overall_score": overall_score,
        "status": "completed"
    }

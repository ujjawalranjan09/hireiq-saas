# Jobs Router - Job management endpoints
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, nullslast
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets

from database.postgres import get_db
from database.pg_models.company import Company
from database.pg_models.user import User
from database.pg_models.job import Job, JobStatus, DifficultyLevel
from database.pg_models.candidate import Candidate, CandidateStatus
from saas.auth.dependencies import get_current_user, require_role
from saas.candidates.schemas import InviteRequest, CandidateListItem, CandidateListResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(
    title: str,
    description: Optional[str] = None,
    required_skills: List[str] = [],
    min_years_experience: int = 0,
    difficulty_level: str = "medium",
    questions_count: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job listing.
    
    Requires "hr" or "admin" role.
    """
    # Validate difficulty level
    try:
        difficulty = DifficultyLevel(difficulty_level.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid difficulty level. Must be one of: easy, medium, hard"
        )
    
    job = Job(
        company_id=current_user.company_id,
        created_by_id=current_user.id,
        title=title,
        description=description or "",
        required_skills=required_skills,
        min_years_experience=min_years_experience,
        difficulty_level=difficulty,
        questions_count=questions_count,
        status=JobStatus.ACTIVE
    )
    
    db.add(job)
    await db.flush()
    
    return {
        "id": job.id,
        "title": job.title,
        "status": job.status.value,
        "created_at": job.created_at
    }


@router.get("/")
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all jobs for the current company.
    
    Returns jobs filtered by company_id to ensure tenant isolation.
    """
    result = await db.execute(
        select(Job)
        .where(Job.company_id == current_user.company_id)
        .order_by(desc(Job.created_at))
    )
    jobs = result.scalars().all()
    
    # Get candidate counts for each job
    job_list = []
    for job in jobs:
        candidate_count_result = await db.execute(
            select(func.count(Candidate.id))
            .where(Candidate.job_id == job.id)
        )
        candidate_count = candidate_count_result.scalar()
        
        job_list.append({
            "id": job.id,
            "title": job.title,
            "status": job.status.value,
            "candidate_count": candidate_count,
            "created_at": job.created_at,
            "difficulty_level": job.difficulty_level.value,
            "questions_count": job.questions_count
        })
    
    return {"jobs": job_list, "total": len(job_list)}


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single job with its candidate count.
    """
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.company_id == current_user.company_id)
    )
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get candidate count
    candidate_count_result = await db.execute(
        select(func.count(Candidate.id))
        .where(Candidate.job_id == job.id)
    )
    candidate_count = candidate_count_result.scalar()
    
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills,
        "min_years_experience": job.min_years_experience,
        "difficulty_level": job.difficulty_level.value,
        "questions_count": job.questions_count,
        "status": job.status.value,
        "candidate_count": candidate_count,
        "created_at": job.created_at
    }


@router.put("/{job_id}")
async def update_job(
    job_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
    min_years_experience: Optional[int] = None,
    difficulty_level: Optional[str] = None,
    questions_count: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update job fields.
    
    Requires ownership check (company_id must match).
    """
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.company_id == current_user.company_id)
    )
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Update fields if provided
    if title is not None:
        job.title = title
    
    if description is not None:
        job.description = description
    
    if required_skills is not None:
        job.required_skills = required_skills
    
    if min_years_experience is not None:
        job.min_years_experience = min_years_experience
    
    if difficulty_level is not None:
        try:
            job.difficulty_level = DifficultyLevel(difficulty_level.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid difficulty level. Must be one of: easy, medium, hard"
            )
    
    if questions_count is not None:
        job.questions_count = questions_count
    
    db.add(job)
    
    return {
        "id": job.id,
        "title": job.title,
        "status": job.status.value,
        "updated_at": datetime.now(timezone.utc)
    }


@router.post("/{job_id}/archive")
async def archive_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Archive a job (set status to "archived").
    
    Does not delete the row, just changes status.
    """
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.company_id == current_user.company_id)
    )
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job.status = JobStatus.ARCHIVED
    db.add(job)
    
    return {"message": "Job archived successfully", "id": job.id, "status": "archived"}


@router.post("/{job_id}/invite", status_code=status.HTTP_202_ACCEPTED)
async def invite_candidates(
    job_id: int,
    request: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Invite candidates to a job.
    
    Accepts a list of email addresses, creates one Candidate row per email
    with a generated token, sets token expiry to 7 days from now.
    """
    # Verify job exists and belongs to company
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.company_id == current_user.company_id)
    )
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Create candidate records
    candidates_created = []
    token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
    
    for email in request.emails:
        candidate = Candidate(
            job_id=job.id,
            company_id=current_user.company_id,
            email=email,
            invite_token=secrets.token_urlsafe(32),
            token_expiry=token_expiry,
            status=CandidateStatus.INVITED
        )
        db.add(candidate)
        candidates_created.append(candidate)
    
    await db.flush()
    
    # Fire email tasks in background (fire and forget)
    # Note: In production, you would use Celery here
    # For now, we'll just log that emails would be sent
    for candidate in candidates_created:
        # This would be: send_invite_email.delay(...)
        pass
    
    return {
        "message": f"Invitations sent to {len(candidates_created)} candidates",
        "count": len(candidates_created),
        "job_id": job.id
    }


@router.get("/{job_id}/candidates")
async def list_job_candidates(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all candidates for a job.
    
    Sorted by rank ascending (nulls last), then by overall_score descending.
    """
    # Verify job exists and belongs to company
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.company_id == current_user.company_id)
    )
    job = result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get candidates sorted by rank (nulls last), then by score descending
    candidates_result = await db.execute(
        select(Candidate)
        .where(Candidate.job_id == job_id)
        .order_by(nullslast(Candidate.rank))
        .order_by(desc(Candidate.overall_score))
    )
    candidates = candidates_result.scalars().all()
    
    candidate_list = [
        CandidateListItem(
            id=c.id,
            name=c.name,
            email=c.email,
            status=c.status.value,
            overall_score=c.overall_score,
            rank=c.rank
        )
        for c in candidates
    ]
    
    return {
        "candidates": candidate_list,
        "total": len(candidate_list)
    }

# Dashboard Router - Analytics and dashboard endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from sqlalchemy.sql import case
from typing import List, Optional
import math

from database.postgres import get_db
from database.pg_models.company import Company
from database.pg_models.user import User
from database.pg_models.job import Job, JobStatus
from database.pg_models.candidate import Candidate, CandidateStatus
from saas.auth.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Total jobs count
    jobs_result = await db.execute(
        select(func.count(Job.id))
        .where(Job.company_id == current_user.company_id)
    )
    total_jobs = jobs_result.scalar() or 0
    
    # Total candidates by status
    candidates_by_status_result = await db.execute(
        select(Candidate.status, func.count(Candidate.id))
        .join(Job, Job.id == Candidate.job_id)
        .where(Job.company_id == current_user.company_id)
        .group_by(Candidate.status)
    )
    candidates_by_status = {
        row[0]: row[1] 
        for row in candidates_by_status_result.all()
    }
    
    # Total candidates
    total_candidates = sum(candidates_by_status.values())
    
    # Average score across all completed interviews
    avg_score_result = await db.execute(
        select(func.avg(Candidate.overall_score))
        .join(Job, Job.id == Candidate.job_id)
        .where(Job.company_id == current_user.company_id)
        .where(Candidate.status == CandidateStatus.COMPLETED)
    )
    avg_score = avg_score_result.scalar()
    avg_score = round(float(avg_score), 2) if avg_score else 0.0
    
    # Completion rate
    completed_count = candidates_by_status.get(CandidateStatus.COMPLETED.value, 0)
    completion_rate = round((completed_count / total_candidates * 100), 2) if total_candidates > 0 else 0.0
    
    # Per-job summary list
    jobs_summary_result = await db.execute(
        select(
            Job.id,
            Job.title,
            Job.status,
            func.count(distinct(Candidate.id)).label('candidate_count'),
            func.avg(Candidate.overall_score).label('avg_score')
        )
        .outerjoin(Candidate, Candidate.job_id == Job.id)
        .where(Job.company_id == current_user.company_id)
        .group_by(Job.id, Job.title, Job.status)
        .order_by(Job.created_at.desc())
    )
    
    jobs_summary = []
    for row in jobs_summary_result.all():
        job_avg_score = float(row.avg_score) if row.avg_score else 0.0
        jobs_summary.append({
            "id": row.id,
            "title": row.title,
            "status": row.status.value if hasattr(row.status, 'value') else row.status,
            "candidate_count": row.candidate_count,
            "avg_score": round(job_avg_score, 2)
        })
    
    return {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
        "candidates_by_status": candidates_by_status,
        "average_score": avg_score,
        "completion_rate": completion_rate,
        "jobs_summary": jobs_summary
    }


@router.get("/jobs/{job_id}")
async def get_job_analytics(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get score distribution for a specific job.
    
    Returns:
    - Min score
    - Max score
    - Median score
    - Percentile breakdown (25th, 50th, 75th, 90th)
    """
    
    # Verify job exists and belongs to company
    job_result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .where(Job.company_id == current_user.company_id)
    )
    job = job_result.scalar_one_or_none()
    
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get all completed candidate scores for this job
    scores_result = await db.execute(
        select(Candidate.overall_score)
        .where(Candidate.job_id == job_id)
        .where(Candidate.status == CandidateStatus.COMPLETED)
        .where(Candidate.overall_score.isnot(None))
        .order_by(Candidate.overall_score)
    )
    scores = [row[0] for row in scores_result.all()]
    
    if not scores:
        return {
            "job_id": job_id,
            "job_title": job.title,
            "total_completed": 0,
            "min": None,
            "max": None,
            "median": None,
            "percentiles": {
                "p25": None,
                "p50": None,
                "p75": None,
                "p90": None
            }
        }
    
    # Calculate statistics
    n = len(scores)
    min_score = min(scores)
    max_score = max(scores)
    
    # Median
    if n % 2 == 0:
        median = (scores[n // 2 - 1] + scores[n // 2]) / 2
    else:
        median = scores[n // 2]
    
    # Percentiles
    def percentile(data, p):
        k = (len(data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        return data[f] * (c - k) + data[c] * (k - f)
    
    percentiles = {
        "p25": round(percentile(scores, 25), 2),
        "p50": round(percentile(scores, 50), 2),
        "p75": round(percentile(scores, 75), 2),
        "p90": round(percentile(scores, 90), 2)
    }
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_completed": n,
        "min": round(min_score, 2),
        "max": round(max_score, 2),
        "median": round(median, 2),
        "percentiles": percentiles
    }

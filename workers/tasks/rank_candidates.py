# Rank Candidates Task - Celery task for ranking candidates by score
from celery import shared_task
from sqlalchemy import select, desc
from datetime import datetime
import os

# Read PostgreSQL URL from environment variable
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+asyncpg://hireiq:hireiq_password@localhost:5432/hireiq_saas")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def rank_candidates_job(self, job_id: int):
    """
    Rank all completed candidates for a specific job.
    
    This task:
    1. Queries PostgreSQL for all candidates with status "completed" for the job
    2. Sorts them by overall_score descending
    3. Updates each candidate's rank column with their position (1 = best score)
    
    This task is triggered automatically at the end of each completed interview.
    
    Args:
        job_id: The ID of the job to rank candidates for
    """
    try:
        # Import here to avoid circular imports
        from database.postgres import engine
        from database.pg_models.candidate import Candidate, CandidateStatus
        
        import asyncio
        
        async def _rank_candidates():
            async with engine.begin() as conn:
                # Get all completed candidates for this job, sorted by score descending
                result = await conn.execute(
                    select(Candidate)
                    .where(Candidate.job_id == job_id)
                    .where(Candidate.status == CandidateStatus.COMPLETED)
                    .where(Candidate.overall_score.isnot(None))
                    .order_by(desc(Candidate.overall_score))
                )
                candidates = result.scalars().all()
                
                if not candidates:
                    return {
                        "success": True,
                        "message": f"No completed candidates found for job {job_id}",
                        "ranked_count": 0
                    }
                
                # Update ranks (1 = best score)
                for rank, candidate in enumerate(candidates, start=1):
                    candidate.rank = rank
                
                # Return summary
                return {
                    "success": True,
                    "message": f"Ranked {len(candidates)} candidates for job {job_id}",
                    "ranked_count": len(candidates),
                    "job_id": job_id
                }
        
        # Run the async function
        result = asyncio.run(_rank_candidates())
        return result
        
    except Exception as e:
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except AttributeError:
            # Not running in Celery context
            return {
                "success": False,
                "error": str(e),
                "job_id": job_id
            }


# For testing without Celery broker
def rank_candidates_job_eager(job_id: int):
    """
    Synchronous version for testing without a Celery broker.
    
    This function directly executes the ranking logic.
    """
    return rank_candidates_job(job_id=job_id)

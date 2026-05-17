# Candidates Router - Candidate interview endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import io

from database.postgres import get_db
from database.pg_models.candidate import Candidate, CandidateStatus
from database.pg_models.job import Job
from database.pg_models.company import Company
from saas.candidates.schemas import (
    CandidateValidateResponse, 
    SessionStartResponse, 
    CandidateStatusResponse,
    CandidateDetailResponse
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("/{token}/validate")
async def validate_invite_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate an invite token.
    
    Checks if token exists, is not expired, and has status "invited".
    Returns job title and company name. No side effects.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.invite_token == token)
    )
    candidate = result.scalar_one_or_none()
    
    if candidate is None:
        return CandidateValidateResponse(
            valid=False,
            job_title="",
            company_name="",
            candidate_name=None
        )
    
    # Check if expired
    if candidate.token_expiry < datetime.utcnow():
        return CandidateValidateResponse(
            valid=False,
            job_title="",
            company_name="",
            candidate_name=candidate.name
        )
    
    # Check status
    if candidate.status != CandidateStatus.INVITED:
        return CandidateValidateResponse(
            valid=False,
            job_title="",
            company_name="",
            candidate_name=candidate.name
        )
    
    # Get job and company info
    job_result = await db.execute(
        select(Job).where(Job.id == candidate.job_id)
    )
    job = job_result.scalar_one_or_none()
    
    if job is None:
        return CandidateValidateResponse(
            valid=False,
            job_title="",
            company_name="",
            candidate_name=candidate.name
        )
    
    company_result = await db.execute(
        select(Company).where(Company.id == candidate.company_id)
    )
    company = company_result.scalar_one_or_none()
    
    return CandidateValidateResponse(
        valid=True,
        job_title=job.title,
        company_name=company.name if company else "",
        candidate_name=candidate.name
    )


@router.post("/{token}/start", response_model=SessionStartResponse)
async def start_interview_session(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Start an interview session.
    
    Calls interview_bridge.start_session(token, db) and returns the result.
    This is the critical route that connects to the AI interview engine.
    """
    # Import the bridge function (written by Sub-Agent 3)
    from saas.candidates.interview_bridge import start_session
    
    try:
        result = await start_session(token, db)
        return SessionStartResponse(
            session_id=result["session_id"],
            job_title=result["job_title"],
            questions_count=result["questions_count"],
            status=result["status"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview session: {str(e)}"
        )


@router.get("/{token}/status", response_model=CandidateStatusResponse)
async def get_candidate_status(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current candidate status.
    
    Returns current candidate status and, if completed, the overall score.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.invite_token == token)
    )
    candidate = result.scalar_one_or_none()
    
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return CandidateStatusResponse(
        status=candidate.status.value,
        overall_score=candidate.overall_score,
        completed_at=candidate.completed_at
    )


@router.get("/{token}/report")
async def get_candidate_report(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the candidate's PDF report.
    
    Fetches the PDF from the MongoDB session via existing modules/report functions
    and returns it as a file download.
    
    This is the only place where we call into modules/ - and only the report module, read-only.
    """
    result = await db.execute(
        select(Candidate)
        .where(Candidate.invite_token == token)
    )
    candidate = result.scalar_one_or_none()
    
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    if candidate.mongo_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session not started yet"
        )
    
    # Import the report module (read-only access to existing functionality)
    try:
        from modules.report import generate_pdf_report
        
        # Generate the PDF report
        pdf_data = generate_pdf_report(candidate.mongo_session_id)
        
        # Return as file download
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="interview_report_{candidate.email}.pdf"'
            }
        )
    except ImportError:
        # If report module doesn't exist yet, return a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Report generation not yet available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

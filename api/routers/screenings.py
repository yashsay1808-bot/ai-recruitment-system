"""
FastAPI router for Screening sessions, hybrid evaluations, and recruiter decision tracking.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from api.deps import get_screening_service
from services.screening_service import ScreeningService
from api.schemas.screenings import (
    ScreeningRunRequest,
    ScreeningDecisionUpdate,
    ScreeningResultResponse,
    ScreeningSessionSummary,
    ScreeningSessionDetail,
)

router = APIRouter(prefix="/screenings", tags=["Screenings"])


@router.post("/run", response_model=ScreeningSessionDetail, status_code=status.HTTP_201_CREATED)
def run_screening(
    request: ScreeningRunRequest,
    db: Session = Depends(get_db),
    screening_service: ScreeningService = Depends(get_screening_service)
):
    """
    Executes a multi-dimensional screening evaluation of candidate resumes against a Job.
    Supports optional Blind Screening mode and custom dimension weighting.
    """
    try:
        session = screening_service.run_screening(db=db, request=request)
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[ScreeningSessionSummary])
def list_screenings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    screening_service: ScreeningService = Depends(get_screening_service)
):
    """Lists screening sessions."""
    sessions = screening_service.list_sessions(db=db, skip=skip, limit=limit)
    summaries = []
    for s in sessions:
        summaries.append(ScreeningSessionSummary(
            id=s.id,
            job_id=s.job_id,
            session_name=s.session_name,
            recruiter_email=s.recruiter_email,
            weights=s.weights,
            created_at=s.created_at,
            total_candidates=len(s.results)
        ))
    return summaries


@router.get("/{session_id}", response_model=ScreeningSessionDetail)
def get_screening_session(
    session_id: int,
    db: Session = Depends(get_db),
    screening_service: ScreeningService = Depends(get_screening_service)
):
    """Retrieves full screening session details including all ranked candidate evaluations."""
    session = screening_service.get_session(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Screening session {session_id} not found")
    return session


@router.patch("/results/{result_id}/decision", response_model=ScreeningResultResponse)
def update_screening_decision(
    result_id: int,
    decision_in: ScreeningDecisionUpdate,
    actor: str = "recruiter",
    db: Session = Depends(get_db),
    screening_service: ScreeningService = Depends(get_screening_service)
):
    """
    Logs human recruiter decision (shortlist / reject) with timestamp and audit record.
    """
    result = screening_service.update_candidate_decision(
        db=db,
        result_id=result_id,
        decision=decision_in.decision,
        actor=actor,
        notes=decision_in.notes
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Screening result {result_id} not found")
    return result

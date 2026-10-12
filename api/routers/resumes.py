"""
FastAPI router for Resume ingestion, parsing, and query endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from db.session import get_db
from api.deps import get_resume_service
from services.resume_service import ResumeService
from api.schemas.resumes import ResumeResponse, ResumeSummary, ResumeUploadResponse

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resumes(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    resume_service: ResumeService = Depends(get_resume_service)
):
    """
    Ingests and parses uploaded candidate resume files (PDF, DOCX, TXT).
    Automatically deduplicates files using SHA-256 byte hashing.
    """
    results = []
    cached_count = 0

    for upload in files:
        contents = await upload.read()
        if not contents:
            continue
        resume, is_cached = resume_service.process_and_save_resume(
            db=db,
            file_bytes=contents,
            file_name=upload.filename or "unknown_resume.pdf"
        )
        if is_cached:
            cached_count += 1
        results.append(resume)

    return ResumeUploadResponse(
        total_uploaded=len(results),
        resumes=[ResumeResponse.model_validate(r) for r in results],
        cached_count=cached_count
    )


@router.get("", response_model=List[ResumeSummary])
def list_resumes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    resume_service: ResumeService = Depends(get_resume_service)
):
    """Lists resumes in the system with parsed summary data."""
    resumes = resume_service.list_resumes(db=db, skip=skip, limit=limit)
    summaries = []
    for r in resumes:
        skills = r.parsed_data.get("skills", []) if isinstance(r.parsed_data, dict) else []
        summaries.append(ResumeSummary(
            id=r.id,
            file_name=r.file_name,
            file_hash=r.file_hash,
            candidate_name=r.candidate_name,
            email=r.email,
            skills=skills,
            created_at=r.created_at
        ))
    return summaries


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    resume_service: ResumeService = Depends(get_resume_service)
):
    """Retrieves full resume details and structured parsed profile."""
    resume = resume_service.get_resume(db=db, resume_id=resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resume with ID {resume_id} not found")
    return resume

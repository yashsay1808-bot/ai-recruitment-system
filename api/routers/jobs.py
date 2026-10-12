"""
FastAPI router for Job vacancy management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from api.deps import get_job_service
from services.job_service import JobService
from api.schemas.jobs import JobCreate, JobUpdate, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """Creates a new Job vacancy specification."""
    return job_service.create_job(db=db, job_in=job_in)


@router.get("", response_model=List[JobResponse])
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """Lists all available job openings."""
    return job_service.list_jobs(db=db, skip=skip, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """Retrieves a single job vacancy by ID."""
    job = job_service.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {job_id} not found")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """Updates an existing job vacancy."""
    job = job_service.update_job(db=db, job_id=job_id, job_in=job_in)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {job_id} not found")
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    job_service: JobService = Depends(get_job_service)
):
    """Deletes a job vacancy."""
    success = job_service.delete_job(db=db, job_id=job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {job_id} not found")
    return None

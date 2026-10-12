"""
Service layer for managing Job vacancies.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Job, AuditLog
from api.schemas.jobs import JobCreate, JobUpdate


class JobService:
    """Manages job descriptions and vacancies."""

    @staticmethod
    def create_job(db: Session, job_in: JobCreate, actor: str = "recruiter") -> Job:
        """Creates and stores a new job description."""
        job = Job(
            title=job_in.title,
            department=job_in.department,
            min_experience=job_in.min_experience,
            required_skills=job_in.required_skills,
            preferred_skills=job_in.preferred_skills,
            preferred_degrees=job_in.preferred_degrees,
            description_text=job_in.description_text
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Audit log
        audit = AuditLog(
            action="JOB_CREATED",
            actor=actor,
            details={"job_id": job.id, "title": job.title, "department": job.department}
        )
        db.add(audit)
        db.commit()

        return job

    @staticmethod
    def get_job(db: Session, job_id: int) -> Optional[Job]:
        """Retrieves a job by its unique identifier."""
        return db.get(Job, job_id)

    @staticmethod
    def list_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
        """Lists jobs with pagination ordered by newest first."""
        stmt = select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_job(db: Session, job_id: int, job_in: JobUpdate, actor: str = "recruiter") -> Optional[Job]:
        """Updates an existing job vacancy."""
        job = db.get(Job, job_id)
        if not job:
            return None

        update_data = job_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job, key, value)

        db.commit()
        db.refresh(job)

        audit = AuditLog(
            action="JOB_UPDATED",
            actor=actor,
            details={"job_id": job.id, "updated_fields": list(update_data.keys())}
        )
        db.add(audit)
        db.commit()

        return job

    @staticmethod
    def delete_job(db: Session, job_id: int, actor: str = "recruiter") -> bool:
        """Deletes a job vacancy and cascades deletions."""
        job = db.get(Job, job_id)
        if not job:
            return False

        job_title = job.title
        db.delete(job)
        db.commit()

        audit = AuditLog(
            action="JOB_DELETED",
            actor=actor,
            details={"job_id": job_id, "title": job_title}
        )
        db.add(audit)
        db.commit()

        return True

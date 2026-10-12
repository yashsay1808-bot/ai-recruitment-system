"""
FastAPI application dependencies and dependency injection helpers.
"""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from db.session import get_db
from src.config import Settings, get_settings
from services.job_service import JobService
from services.resume_service import ResumeService
from services.screening_service import ScreeningService
from services.audit_service import AuditService


def get_job_service() -> JobService:
    """Provides JobService instance."""
    return JobService()


def get_resume_service() -> ResumeService:
    """Provides ResumeService instance."""
    return ResumeService()


def get_screening_service() -> ScreeningService:
    """Provides ScreeningService instance."""
    return ScreeningService()


def get_audit_service() -> AuditService:
    """Provides AuditService instance."""
    return AuditService()

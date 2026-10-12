"""
Service layer for Resume ingestion, SHA-256 deduplication caching, and retrieval.
"""

import hashlib
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Resume, AuditLog
from src.core.resume_parser import ResumeParser


class ResumeService:
    """Manages parsing, deduplication, and persistence of candidate resumes."""

    def __init__(self, parser: Optional[ResumeParser] = None):
        self.parser = parser or ResumeParser()

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        """Computes the hex SHA-256 digest of binary content."""
        return hashlib.sha256(content).hexdigest()

    def process_and_save_resume(
        self,
        db: Session,
        file_bytes: bytes,
        file_name: str,
        actor: str = "recruiter"
    ) -> Tuple[Resume, bool]:
        """
        Processes a resume file:
        - Computes SHA-256 hash
        - Checks for existing record (cache hit)
        - If new, parses using ResumeParser and persists to database
        Returns (Resume, is_cached).
        """
        file_hash = self.compute_sha256(file_bytes)

        # Check deduplication cache
        existing = db.scalars(
            select(Resume).where(Resume.file_hash == file_hash)
        ).first()

        if existing:
            return existing, True

        # Parse new resume
        parsed = self.parser.parse(file_bytes, file_name)
        raw_text = parsed.get("raw_text", "")

        resume = Resume(
            file_name=file_name,
            file_hash=file_hash,
            raw_text=raw_text,
            parsed_data=parsed,
            candidate_name=parsed.get("candidate_name"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location")
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Audit log entry
        audit = AuditLog(
            action="RESUME_UPLOADED",
            actor=actor,
            details={
                "resume_id": resume.id,
                "file_name": file_name,
                "file_hash": file_hash,
                "candidate_name": resume.candidate_name
            }
        )
        db.add(audit)
        db.commit()

        return resume, False

    @staticmethod
    def get_resume(db: Session, resume_id: int) -> Optional[Resume]:
        """Retrieves a resume by id."""
        return db.get(Resume, resume_id)

    @staticmethod
    def get_resume_by_hash(db: Session, file_hash: str) -> Optional[Resume]:
        """Retrieves a resume by its SHA-256 hash."""
        return db.scalars(select(Resume).where(Resume.file_hash == file_hash)).first()

    @staticmethod
    def list_resumes(db: Session, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Lists stored resumes ordered by creation date."""
        stmt = select(Resume).order_by(Resume.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

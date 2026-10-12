"""
SQLAlchemy ORM models for the AI Recruitment Platform.
Defines schemas for Jobs, Resumes, ScreeningSessions, ScreeningResults, and AuditLogs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


def utc_now() -> datetime:
    """Helper to return UTC datetime with timezone stripped for DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Job(Base):
    """Job vacancy definition model."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(255), default="Engineering", nullable=False)
    min_experience: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    required_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_skills: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_degrees: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    description_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    sessions: Mapped[List["ScreeningSession"]] = relationship(
        "ScreeningSession",
        back_populates="job",
        cascade="all, delete-orphan"
    )


class Resume(Base):
    """Candidate resume entity with raw text and SHA-256 deduplication hash."""
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    parsed_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    candidate_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    screening_results: Mapped[List["ScreeningResult"]] = relationship(
        "ScreeningResult",
        back_populates="resume"
    )


class ScreeningSession(Base):
    """A batch screening run evaluating candidates for a specific job."""
    __tablename__ = "screening_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    session_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recruiter_email: Mapped[str] = mapped_column(String(255), default="recruiter@enterprise.com", nullable=False)
    weights: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="sessions")
    results: Mapped[List["ScreeningResult"]] = relationship(
        "ScreeningResult",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ScreeningResult.rank"
    )


class ScreeningResult(Base):
    """Detailed score, evidence, and decision for an individual candidate in a screening session."""
    __tablename__ = "screening_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    breakdown: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    gap_results: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    candidate_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    rubric_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    evidence: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., 'shortlist', 'reject'
    decision_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    session: Mapped["ScreeningSession"] = relationship("ScreeningSession", back_populates="results")
    resume: Mapped[Optional["Resume"]] = relationship("Resume", back_populates="screening_results")


class AuditLog(Base):
    """System-wide immutable audit trail for security and recruiter actions."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(255), default="system", nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

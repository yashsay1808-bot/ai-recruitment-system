"""
Service layer for managing and querying the system audit trail.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import AuditLog


class AuditService:
    """Manages audit logging and compliance retrieval."""

    @staticmethod
    def log_event(
        db: Session,
        action: str,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Records an event in the immutable audit log."""
        log = AuditLog(
            action=action,
            actor=actor,
            details=details or {}
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(db: Session, skip: int = 0, limit: int = 100, action: Optional[str] = None) -> List[AuditLog]:
        """Lists audit logs with optional filtering by action type, newest first."""
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

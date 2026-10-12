"""
FastAPI router for System Audit Trail and Compliance Logs.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from db.session import get_db
from api.deps import get_audit_service
from services.audit_service import AuditService
from api.schemas.audits import AuditLogCreate, AuditLogResponse

router = APIRouter(prefix="/audits", tags=["Audits"])


@router.get("", response_model=List[AuditLogResponse])
def list_audits(
    action: Optional[str] = Query(None, description="Filter logs by action name"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Retrieves immutable audit trail entries."""
    return audit_service.list_logs(db=db, skip=skip, limit=limit, action=action)


@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
def create_audit(
    audit_in: AuditLogCreate,
    db: Session = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Manually creates an audit trail event."""
    return audit_service.log_event(
        db=db,
        action=audit_in.action,
        actor=audit_in.actor,
        details=audit_in.details
    )

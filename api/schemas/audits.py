"""
Pydantic schemas for System Audit Logs and security tracking.
"""

from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class AuditLogBase(BaseModel):
    action: str = Field(..., description="Action name, e.g. JOB_CREATED, SCREENING_RUN, DECISION_UPDATED")
    actor: str = Field(default="system", description="Identifier of the user or subsystem initiating action")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured contextual event metadata")


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

"""
Pydantic schemas for Screening Sessions, evaluations, and recruiter decisions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScreeningRunRequest(BaseModel):
    job_id: int = Field(..., description="Target Job vacancy ID")
    resume_ids: Optional[List[int]] = Field(default=None, description="Optional subset of resume IDs; if None, screens all available resumes")
    session_name: Optional[str] = Field(default=None, description="Descriptive name for this screening run")
    recruiter_email: str = Field(default="recruiter@enterprise.com", description="Email of evaluating recruiter")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Optional custom dimension weights")
    blind_screening: bool = Field(default=False, description="Whether to apply PII blind screening redaction")


class ScreeningDecisionUpdate(BaseModel):
    decision: str = Field(..., pattern="^(shortlist|reject|pending)$", description="Recruiter decision: shortlist, reject, or pending")
    notes: Optional[str] = Field(default=None, description="Optional justification or recruiter feedback notes")


class ScreeningResultResponse(BaseModel):
    id: int
    session_id: int
    resume_id: Optional[int] = None
    candidate_name: str
    overall_score: float
    rank: int
    breakdown: Dict[str, Any]
    gap_results: Dict[str, Any]
    candidate_data: Dict[str, Any]
    rubric_scores: Optional[Dict[str, Any]] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    is_verified: bool = False
    decision: Optional[str] = None
    decision_timestamp: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningSessionSummary(BaseModel):
    id: int
    job_id: int
    session_name: str
    recruiter_email: str
    weights: Dict[str, float]
    created_at: datetime
    total_candidates: int = 0

    model_config = ConfigDict(from_attributes=True)


class ScreeningSessionDetail(BaseModel):
    id: int
    job_id: int
    session_name: str
    recruiter_email: str
    weights: Dict[str, float]
    created_at: datetime
    results: List[ScreeningResultResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

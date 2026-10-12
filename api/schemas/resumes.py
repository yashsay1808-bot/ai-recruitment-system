"""
Pydantic schemas for Resume entity, parsed profiles, and uploads.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    file_name: str
    file_hash: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class ResumeCreate(ResumeBase):
    raw_text: str
    parsed_data: Dict[str, Any] = Field(default_factory=dict)


class ResumeResponse(ResumeBase):
    id: int
    raw_text: str
    parsed_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeSummary(BaseModel):
    id: int
    file_name: str
    file_hash: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    total_uploaded: int
    resumes: List[ResumeResponse]
    cached_count: int = 0

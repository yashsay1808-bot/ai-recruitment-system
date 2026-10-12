"""
Pydantic schemas for Job vacancy creation and responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    title: str = Field(..., description="Job role title", min_length=2)
    department: str = Field(default="Engineering", description="Department or business unit")
    min_experience: float = Field(default=0.0, ge=0.0, description="Minimum required years of experience")
    required_skills: List[str] = Field(default_factory=list, description="Must-have technical skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred nice-to-have skills")
    preferred_degrees: List[str] = Field(default_factory=list, description="Preferred educational degrees")
    description_text: str = Field(default="", description="Full text description of the job posting")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    min_experience: Optional[float] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    preferred_degrees: Optional[List[str]] = None
    description_text: Optional[str] = None


class JobResponse(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

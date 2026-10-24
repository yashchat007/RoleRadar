from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProfileOut(BaseModel):
    skills: list[Any] = Field(default_factory=list)
    education: list[Any] = Field(default_factory=list)
    experience: list[Any] = Field(default_factory=list)
    projects: list[Any] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    updated_at: datetime | None = None


class ProfilePatch(BaseModel):
    skills: list[Any] | None = None
    education: list[Any] | None = None
    experience: list[Any] | None = None
    projects: list[Any] | None = None
    preferences: dict | None = None


class ResumeUploadOut(BaseModel):
    resume_id: str
    filename: str
    parsed: bool
    skills_found: int
    matches_recomputed: int


class ResumeStatusOut(BaseModel):
    has_resume: bool
    resume_id: str | None = None
    filename: str | None = None
    uploaded_at: datetime | None = None


class SourceOut(BaseModel):
    field_path: str
    source: dict | None

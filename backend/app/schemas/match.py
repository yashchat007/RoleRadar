import uuid
from datetime import datetime

from pydantic import BaseModel


class MatchOut(BaseModel):
    job_id: uuid.UUID
    score: int | None = None
    preference_score: int | None = None
    resume_match_available: bool = False
    eligible: bool
    role_family: str | None = None
    eligibility_reasons: list[str]
    factors: list[dict]
    requirements: list[dict]
    gaps: list[dict]
    top_reasons: list[str]
    computed_at: datetime


class JobWithMatchOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str | None = None
    title: str
    location: str | None
    listing_url: str
    apply_url: str
    deadline_at: datetime | None = None
    posted_at: datetime | None = None
    score: int | None = None
    preference_score: int | None = None
    resume_match_available: bool = False
    eligible: bool | None = None
    top_reason: str | None = None
    role_family: str | None = None
    company_logo_url: str | None = None
    eligibility_label: str | None = None
    eligibility_detail: str | None = None
    location_display: str | None = None
    career_level_label: str | None = None

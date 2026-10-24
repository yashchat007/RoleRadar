import uuid
from datetime import datetime

from pydantic import BaseModel


class AttentionJobOut(BaseModel):
    job_id: uuid.UUID
    title: str
    company_name: str
    score: int
    top_reason: str | None
    deadline_at: datetime | None


class ChangelogEntryOut(BaseModel):
    message: str
    created_at: datetime


class TodayOut(BaseModel):
    headline: str
    attention: list[AttentionJobOut]
    tracker_counts: dict[str, int]
    upcoming_deadlines: list[AttentionJobOut]
    changelog: list[ChangelogEntryOut]
    sources_degraded: list[str]

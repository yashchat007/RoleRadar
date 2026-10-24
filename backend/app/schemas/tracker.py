import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TrackerStage


class TrackerItemOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    title: str
    company_name: str
    stage: TrackerStage
    score: int | None
    stage_entered_at: datetime
    applied_at: datetime | None
    deadline_at: datetime | None
    notes: str | None


class TrackerPatch(BaseModel):
    stage: TrackerStage
    applied_at: datetime | None = None
    notes: str | None = None


class TrackerBoardOut(BaseModel):
    items: list[TrackerItemOut]
    counts_by_stage: dict[str, int]

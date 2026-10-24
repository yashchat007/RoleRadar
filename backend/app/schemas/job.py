import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ListingStatus
from app.schemas.match import JobWithMatchOut


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str | None = None
    title: str
    location: str | None
    remote_flag: bool | None
    listing_url: str
    apply_url: str
    listing_status: ListingStatus
    description_sections: dict | None = None
    posted_at: datetime | None
    deadline_at: datetime | None
    last_seen_at: datetime
    last_verified_at: datetime | None = None
    lifecycle_status: str | None = None
    requisition_id: str | None = None


class JobListMeta(BaseModel):
    total: int
    matching_total: int | None = None
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None
    visible_count: int | None = None
    sources_degraded: list[str] = []
    hidden_ineligible_count: int = 0
    sort_label: str | None = None
    has_resume: bool = False


class JobListResponse(BaseModel):
    items: list[JobWithMatchOut]
    meta: JobListMeta

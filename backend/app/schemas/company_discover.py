import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LastScanStatus, ParserStatus


class CompanyDiscoverCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    career_page_url: str
    parser_status: ParserStatus
    is_enabled: bool
    last_scan_status: LastScanStatus | None
    active_job_count: int
    india_internship_count: int = 0
    source_state: str
    last_scan_at: datetime | None = None
    coverage_note: str | None = None
    company_logo_url: str | None = None
    priority_rank: int | None = None
    status_label: str = Field(default="", description="Human scan status for UI")
    last_scan_jobs_seen: int | None = None

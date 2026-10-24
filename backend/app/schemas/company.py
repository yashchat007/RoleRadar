import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ExtractionMode, LastScanStatus, ParserStatus


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    career_page_url: str
    parser_status: ParserStatus
    adapter_key: str | None
    extraction_mode: ExtractionMode | None
    scan_cadence_hours: int
    last_scan_status: LastScanStatus | None
    last_success_at: datetime | None
    last_error: str | None
    is_enabled: bool

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import LastScanStatus, ParserStatus


class DiscoveryStatusOut(BaseModel):
    enabled_companies: int
    pending_validation: int
    scanning: bool
    last_aggregate_scan_at: datetime | None


class CompanyHealthOut(BaseModel):
    company_id: uuid.UUID
    name: str
    parser_status: ParserStatus
    last_scan_status: LastScanStatus | None
    last_success_at: datetime | None
    last_error: str | None
    is_enabled: bool

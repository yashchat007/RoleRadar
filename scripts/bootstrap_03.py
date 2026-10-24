import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("backend/app/models/scan_run.py", """import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ExtractionMode, LastScanStatus


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[LastScanStatus] = mapped_column(Enum(LastScanStatus, name="scan_run_status"))
    jobs_seen: Mapped[int] = mapped_column(Integer, default=0)
    jobs_created: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0)
    jobs_closed: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_mode_used: Mapped[ExtractionMode | None] = mapped_column(
        Enum(ExtractionMode, name="scan_extraction_mode"), nullable=True
    )

    company = relationship("Company", back_populates="scan_runs")
""")

w("backend/app/models/listing_event.py", """import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ListingEvent(Base):
    __tablename__ = "listing_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
""")

w("backend/app/models/__init__.py", """from app.models.company import Company
from app.models.job import Job
from app.models.listing_event import ListingEvent
from app.models.scan_run import ScanRun

__all__ = ["Company", "Job", "ListingEvent", "ScanRun"]
""")

w("backend/app/schemas/company.py", """import uuid
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
""")

w("backend/app/schemas/discovery.py", """import uuid
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
""")

print("scan models ok")

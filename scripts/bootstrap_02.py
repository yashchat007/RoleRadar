import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("backend/app/database.py", """from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
""")

w("backend/app/models/enums.py", """import enum


class ParserStatus(str, enum.Enum):
    pending_validation = "pending_validation"
    validating = "validating"
    enabled = "enabled"
    failed = "failed"
    disabled = "disabled"


class ExtractionMode(str, enum.Enum):
    static_html = "static_html"
    browser_render = "browser_render"


class LastScanStatus(str, enum.Enum):
    success = "success"
    partial = "partial"
    error = "error"
    skipped = "skipped"


class ListingStatus(str, enum.Enum):
    active = "active"
    closed_confirmed = "closed_confirmed"
    temporarily_unavailable = "temporarily_unavailable"
""")

w("backend/app/models/company.py", """import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ExtractionMode, LastScanStatus, ParserStatus


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    career_page_url: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_hosts: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    parser_status: Mapped[ParserStatus] = mapped_column(
        Enum(ParserStatus, name="parser_status"), default=ParserStatus.pending_validation
    )
    adapter_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extraction_mode: Mapped[ExtractionMode | None] = mapped_column(
        Enum(ExtractionMode, name="extraction_mode"), nullable=True
    )
    scan_cadence_hours: Mapped[int] = mapped_column(default=24)
    last_scan_status: Mapped[LastScanStatus | None] = mapped_column(
        Enum(LastScanStatus, name="last_scan_status"), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    jobs = relationship("Job", back_populates="company")
    scan_runs = relationship("ScanRun", back_populates="company")
""")

w("backend/app/models/job.py", """import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ListingStatus


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("company_id", "source_job_key", name="uq_job_company_source"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    source_job_key: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    remote_flag: Mapped[bool | None] = mapped_column(nullable=True)
    description_sections: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    listing_url: Mapped[str] = mapped_column(Text, nullable=False)
    apply_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    listing_status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status"), default=ListingStatus.active
    )
    missed_scan_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    company = relationship("Company", back_populates="jobs")
""")

print("models ok")

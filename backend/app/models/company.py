import uuid
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

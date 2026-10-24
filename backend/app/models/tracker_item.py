import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import TrackerStage


class TrackerItem(Base):
    __tablename__ = "tracker_items"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_tracker_user_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    stage: Mapped[TrackerStage] = mapped_column(Enum(TrackerStage, name="tracker_stage"), default=TrackerStage.new)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    timeline: Mapped[list] = mapped_column(JSONB, default=list)

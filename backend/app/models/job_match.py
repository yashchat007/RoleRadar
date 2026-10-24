import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_match_user_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    score: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    preference_score: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    resume_match_available: Mapped[bool] = mapped_column(Boolean, default=False)
    eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    eligibility_reasons: Mapped[list] = mapped_column(JSONB, default=list)
    factors: Mapped[list] = mapped_column(JSONB, default=list)
    requirements: Mapped[list] = mapped_column(JSONB, default=list)
    gaps: Mapped[list] = mapped_column(JSONB, default=list)
    top_reasons: Mapped[list] = mapped_column(JSONB, default=list)
    role_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    scoring_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_content_fingerprint: Mapped[str | None] = mapped_column(String(32), nullable=True)
    profile_resume_fingerprint: Mapped[str | None] = mapped_column(String(32), nullable=True)

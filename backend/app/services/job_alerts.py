"""Email alerts for newly discovered qualifying internships."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.discovery.lifecycle_status import OPEN
from app.models.job import Job
from app.models.job_notification import JobNotification
from app.models.user import User
from app.services.email import send_email

logger = logging.getLogger(__name__)

INDIA_SCOPES = ("india_based", "remote_india", "remote_global_india_ok")


async def select_jobs_pending_notification(session: AsyncSession, user: User) -> list[Job]:
    notified_subq = select(JobNotification.job_id).where(
        JobNotification.user_id == user.id,
        JobNotification.channel == "email",
        JobNotification.status == "sent",
    )
    stmt = (
        select(Job)
        .where(
            Job.employment_type == "internship",
            Job.india_scope.in_(INDIA_SCOPES),
            Job.lifecycle_status == OPEN,
            Job.id.not_in(notified_subq),
        )
        .order_by(Job.first_seen_at.desc())
        .limit(50)
    )
    result = await session.scalars(stmt)
    return list(result.all())


def _format_job_line(job: Job, company_name: str) -> str:
    loc = job.location or "Location unknown"
    deadline = job.deadline_at.strftime("%Y-%m-%d") if job.deadline_at else "—"
    return (
        f"• {job.title} — {company_name}\n"
        f"  Location: {loc}\n"
        f"  Apply: {job.apply_url}\n"
        f"  Deadline: {deadline}\n"
    )


async def send_job_alerts(
    session: AsyncSession,
    user: User,
    *,
    dry_run: bool = False,
    max_retries: int = 2,
) -> tuple[int, int, list[str]]:
    """
    Returns (sent_count, failed_count, errors).
    Does not record success unless SMTP delivery succeeds.
    """
    if not user.email_digest_enabled and not dry_run:
        return 0, 0, ["Daily email notifications are disabled in Settings."]

    recipient = settings.alert_recipient_email or user.email
    jobs = await select_jobs_pending_notification(session, user)
    if not jobs:
        return 0, 0, []

    from app.models.company import Company

    lines: list[str] = []
    for job in jobs:
        company = await session.get(Company, job.company_id)
        lines.append(_format_job_line(job, company.name if company else "Company"))

    subject = f"RoleRadar — {len(jobs)} new internship(s)"
    body = "New qualifying internships:\n\n" + "\n".join(lines) + "\n— RoleRadar"

    if dry_run:
        logger.info("Dry run: would email %s with %s jobs", recipient, len(jobs))
        return 0, 0, [f"Dry run: {len(jobs)} job(s) would be emailed to {recipient}"]

    last_error: str | None = None
    for attempt in range(max_retries + 1):
        try:
            send_email(recipient, subject, body)
            last_error = None
            break
        except OSError as e:
            last_error = str(e)
            logger.warning("SMTP attempt %s failed: %s", attempt + 1, e)

    if last_error:
        for job in jobs:
            session.add(
                JobNotification(
                    user_id=user.id,
                    job_id=job.id,
                    channel="email",
                    status="failed",
                    error_message=last_error,
                )
            )
        await session.commit()
        return 0, len(jobs), [last_error]

    now = datetime.now(UTC)
    for job in jobs:
        session.add(
            JobNotification(
                user_id=user.id,
                job_id=job.id,
                channel="email",
                status="sent",
                sent_at=now,
            )
        )
    await session.commit()
    return len(jobs), 0, []

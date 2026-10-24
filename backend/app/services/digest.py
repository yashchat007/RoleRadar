from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.matching.engine import compute_match
from app.matching.resume_gate import profile_has_resume_evidence
from app.models.enums import ListingStatus
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.profile import Profile
from app.models.user import User
from app.models.watch import Watch
from app.services.digest_result import DigestSendResult
from app.services.email import send_email


async def build_digest_for_user(session: AsyncSession, user: User) -> tuple[str, str] | None:
    profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
    if not profile:
        return None

    since = datetime.now(UTC) - timedelta(days=1)
    new_jobs = await session.scalars(
        select(Job)
        .where(Job.first_seen_at >= since, Job.listing_status == ListingStatus.active)
        .order_by(Job.first_seen_at.desc())
        .limit(30)
    )
    jobs = list(new_jobs.all())
    if not jobs:
        return None

    lines: list[str] = []
    html_parts: list[str] = []
    resume_ok = profile_has_resume_evidence(profile)
    for job in jobs:
        match = compute_match(job, profile, resume_available=resume_ok)
        if not match.eligible:
            continue
        reason = match.top_reasons[0] if match.top_reasons else ""
        score_label = str(match.score) if match.score is not None else "preference"
        lines.append(f"• {job.title} — match {score_label}. {reason}")
        html_parts.append(
            f"<li><strong>{job.title}</strong> — match {match.score}. "
            f'<span style="color:#555">{reason}</span></li>'
        )

    if not lines:
        return None

    headline = f"{len(lines)} new listings worth a look since yesterday"
    text = headline + "\n\n" + "\n".join(lines) + "\n\n— RoleRadar Research Desk"
    html = (
        f"<p style='font-family:Georgia,serif;font-size:18px'>{headline}</p>"
        f"<ul style='font-family:system-ui,sans-serif;line-height:1.5'>{''.join(html_parts)}</ul>"
        f"<p style='color:#6e6b63;font-size:12px'>RoleRadar — official career pages only</p>"
    )
    return text, html


async def send_daily_digest(session: AsyncSession, user: User, *, force: bool = False) -> DigestSendResult:
    if not user.email_digest_enabled and not force:
        return DigestSendResult(
            sent=False,
            status="disabled",
            detail="Daily digest is turned off in Settings.",
        )
    built = await build_digest_for_user(session, user)
    if not built:
        return DigestSendResult(
            sent=False,
            status="no_content",
            detail="No eligible new jobs in the last 24 hours to include.",
        )
    text, html = built
    try:
        send_email(user.email, f"RoleRadar — {text.splitlines()[0]}", text, html)
    except OSError as e:
        return DigestSendResult(sent=False, status="smtp_error", smtp_error=str(e))
    return DigestSendResult(sent=True, status="sent", detail=f"Delivered to {user.email}")


async def run_watch_notifications(session: AsyncSession, user: User) -> int:
    """Email when a watch has new matching jobs since last_notified_at."""
    profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
    if not profile:
        return 0
    resume_ok = profile_has_resume_evidence(profile)

    watches = await session.scalars(select(Watch).where(Watch.user_id == user.id))
    sent = 0
    now = datetime.now(UTC)
    for watch in watches.all():
        since = watch.last_notified_at or (now - timedelta(days=1))
        jobs = await session.scalars(
            select(Job).where(Job.first_seen_at >= since, Job.listing_status == ListingStatus.active).limit(50)
        )
        hits: list[str] = []
        filters = watch.filters or {}
        q = (filters.get("q") or "").lower()
        min_score = filters.get("min_score")
        india_only = filters.get("india_only", True)
        company_id = filters.get("company_id")

        for job in jobs.all():
            if company_id and str(job.company_id) != str(company_id):
                continue
            if india_only is not False:
                scope = job.india_scope or "unknown"
                if scope not in ("india_based", "remote_india", "remote_global_india_ok"):
                    continue
            match_row = await session.scalar(
                select(JobMatch).where(JobMatch.user_id == user.id, JobMatch.job_id == job.id)
            )
            if match_row:
                score = match_row.score if match_row.resume_match_available else match_row.preference_score
                eligible = match_row.eligible
            else:
                computed = compute_match(job, profile, resume_available=resume_ok)
                score = computed.score if computed.score is not None else computed.preference_score
                eligible = computed.eligible
            if not eligible:
                continue
            if min_score is not None and score < min_score:
                continue
            if q and q not in f"{job.title} {job.location or ''}".lower():
                continue
            hits.append(f"{job.title} ({score})")

        if hits:
            body = f"Watch “{watch.name}” found {len(hits)} new matches:\n\n" + "\n".join(f"• {h}" for h in hits[:15])
            send_email(user.email, f"RoleRadar watch: {watch.name}", body)
            watch.last_notified_at = now
            sent += 1
    await session.commit()
    return sent

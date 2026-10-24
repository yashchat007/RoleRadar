from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.enums import ListingStatus, TRACKER_STAGE_ORDER, TrackerStage
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.listing_event import ListingEvent
from app.models.tracker_item import TrackerItem
from app.models.user import User
from app.schemas.today import AttentionJobOut, ChangelogEntryOut, TodayOut
from app.services.source_health import collect_source_status_messages

router = APIRouter(prefix="/today", tags=["today"])


@router.get("", response_model=TodayOut)
async def get_today(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TodayOut:
    since = datetime.now(UTC) - timedelta(days=1)

    match_rows = await db.execute(
        select(Job, Company, JobMatch)
        .join(JobMatch, JobMatch.job_id == Job.id)
        .join(Company, Company.id == Job.company_id)
        .where(
            JobMatch.user_id == user.id,
            Job.listing_status == ListingStatus.active,
            JobMatch.eligible.is_(True),
        )
        .order_by(JobMatch.score.desc())
        .limit(8)
    )
    attention: list[AttentionJobOut] = []
    for job, company, match in match_rows.all():
        attention.append(
            AttentionJobOut(
                job_id=job.id,
                title=job.title,
                company_name=company.name,
                score=match.score,
                top_reason=(match.top_reasons or [None])[0],
                deadline_at=job.deadline_at,
            )
        )

    new_since = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.first_seen_at >= since, Job.listing_status == ListingStatus.active)
    )
    closing = await db.scalar(
        select(func.count())
        .select_from(Job)
        .where(
            Job.deadline_at.is_not(None),
            Job.deadline_at <= datetime.now(UTC) + timedelta(days=7),
            Job.listing_status == ListingStatus.active,
        )
    )
    headline = f"{new_since or 0} new listings since yesterday"
    if closing:
        headline += f", {closing} closing this week"
    headline += "."

    counts = {s.value: 0 for s in TRACKER_STAGE_ORDER}
    tracker_rows = await db.scalars(select(TrackerItem).where(TrackerItem.user_id == user.id))
    for item in tracker_rows.all():
        counts[item.stage.value] = counts.get(item.stage.value, 0) + 1

    deadline_rows = await db.execute(
        select(Job, Company, JobMatch)
        .join(JobMatch, JobMatch.job_id == Job.id)
        .join(Company, Company.id == Job.company_id)
        .where(
            JobMatch.user_id == user.id,
            Job.deadline_at.is_not(None),
            Job.deadline_at >= datetime.now(UTC),
            Job.listing_status == ListingStatus.active,
        )
        .order_by(Job.deadline_at.asc())
        .limit(5)
    )
    upcoming: list[AttentionJobOut] = []
    for job, company, match in deadline_rows.all():
        upcoming.append(
            AttentionJobOut(
                job_id=job.id,
                title=job.title,
                company_name=company.name,
                score=match.score,
                top_reason=None,
                deadline_at=job.deadline_at,
            )
        )

    events = await db.scalars(
        select(ListingEvent).order_by(ListingEvent.created_at.desc()).limit(10)
    )
    changelog: list[ChangelogEntryOut] = []
    for ev in events.all():
        payload = ev.payload or {}
        title = payload.get("title", "Listing update")
        changelog.append(
            ChangelogEntryOut(
                message=f"{ev.event_type}: {title}",
                created_at=ev.created_at,
            )
        )

    all_companies = await db.scalars(select(Company))
    degraded = collect_source_status_messages(all_companies.all())

    if not attention:
        headline = "No ranked matches yet. Upload a resume or run discovery validation."

    return TodayOut(
        headline=headline,
        attention=attention,
        tracker_counts=counts,
        upcoming_deadlines=upcoming,
        changelog=changelog,
        sources_degraded=degraded,
    )

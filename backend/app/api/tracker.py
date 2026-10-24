import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.enums import TRACKER_STAGE_ORDER, TrackerStage
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.tracker_item import TrackerItem
from app.models.user import User
from app.schemas.tracker import TrackerBoardOut, TrackerItemOut, TrackerPatch

router = APIRouter(prefix="/tracker", tags=["tracker"])


@router.get("", response_model=TrackerBoardOut)
async def get_tracker(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrackerBoardOut:
    rows = await db.execute(
        select(TrackerItem, Job, Company, JobMatch)
        .join(Job, Job.id == TrackerItem.job_id)
        .join(Company, Company.id == Job.company_id)
        .outerjoin(JobMatch, (JobMatch.job_id == Job.id) & (JobMatch.user_id == user.id))
        .where(TrackerItem.user_id == user.id)
        .order_by(TrackerItem.stage_entered_at.desc())
    )
    items: list[TrackerItemOut] = []
    counts = {s.value: 0 for s in TRACKER_STAGE_ORDER}
    for tracker, job, company, match in rows.all():
        counts[tracker.stage.value] = counts.get(tracker.stage.value, 0) + 1
        items.append(
            TrackerItemOut(
                id=tracker.id,
                job_id=job.id,
                title=job.title,
                company_name=company.name,
                stage=tracker.stage,
                score=match.score if match else None,
                stage_entered_at=tracker.stage_entered_at,
                applied_at=tracker.applied_at,
                deadline_at=job.deadline_at,
                notes=tracker.notes,
            )
        )
    return TrackerBoardOut(items=items, counts_by_stage=counts)


@router.patch("/{job_id}", response_model=TrackerItemOut)
async def update_tracker_item(
    job_id: uuid.UUID,
    body: TrackerPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrackerItemOut:
    tracker = await db.scalar(
        select(TrackerItem).where(TrackerItem.user_id == user.id, TrackerItem.job_id == job_id)
    )
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    company = await db.get(Company, job.company_id)
    now = datetime.now(UTC)
    if not tracker:
        tracker = TrackerItem(user_id=user.id, job_id=job_id, stage=body.stage, timeline=[])
        db.add(tracker)
    else:
        if tracker.stage != body.stage:
            timeline = list(tracker.timeline or [])
            timeline.append(
                {"from": tracker.stage.value, "to": body.stage.value, "at": now.isoformat()}
            )
            tracker.timeline = timeline
            tracker.stage = body.stage
            tracker.stage_entered_at = now
    if body.applied_at is not None:
        tracker.applied_at = body.applied_at
    if body.notes is not None:
        tracker.notes = body.notes
    await db.commit()
    await db.refresh(tracker)
    match = await db.scalar(
        select(JobMatch).where(JobMatch.user_id == user.id, JobMatch.job_id == job_id)
    )
    return TrackerItemOut(
        id=tracker.id,
        job_id=job.id,
        title=job.title,
        company_name=company.name if company else "",
        stage=tracker.stage,
        score=match.score if match else None,
        stage_entered_at=tracker.stage_entered_at,
        applied_at=tracker.applied_at,
        deadline_at=job.deadline_at,
        notes=tracker.notes,
    )

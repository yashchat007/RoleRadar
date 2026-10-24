import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.bookmark import Bookmark
from app.models.company import Company
from app.models.enums import TrackerStage
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.tracker_item import TrackerItem
from app.models.user import User
from app.schemas.match import JobWithMatchOut

router = APIRouter(prefix="/saved", tags=["saved"])


@router.get("", response_model=list[JobWithMatchOut])
async def list_saved(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobWithMatchOut]:
    rows = await db.execute(
        select(Job, Company, JobMatch, Bookmark)
        .join(Bookmark, Bookmark.job_id == Job.id)
        .join(Company, Company.id == Job.company_id)
        .outerjoin(JobMatch, (JobMatch.job_id == Job.id) & (JobMatch.user_id == user.id))
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
    )
    items: list[JobWithMatchOut] = []
    for job, company, match, _bm in rows.all():
        items.append(
            JobWithMatchOut(
                id=job.id,
                company_id=job.company_id,
                company_name=company.name,
                title=job.title,
                location=job.location,
                listing_url=job.listing_url,
                apply_url=job.apply_url,
                deadline_at=job.deadline_at,
                posted_at=job.posted_at,
                score=match.score if match else None,
                eligible=match.eligible if match else None,
                top_reason=(match.top_reasons or [None])[0] if match else None,
            )
        )
    return items


@router.post("/jobs/{job_id}")
async def create_bookmark(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    exists = await db.scalar(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.job_id == job_id)
    )
    if not exists:
        db.add(Bookmark(user_id=user.id, job_id=job_id))
    tracker = await db.scalar(
        select(TrackerItem).where(TrackerItem.user_id == user.id, TrackerItem.job_id == job_id)
    )
    if not tracker:
        db.add(TrackerItem(user_id=user.id, job_id=job_id, stage=TrackerStage.shortlisted))
    elif tracker.stage == TrackerStage.new:
        tracker.stage = TrackerStage.shortlisted
    await db.commit()
    return {"bookmarked": True, "job_id": str(job_id)}


@router.delete("/jobs/{job_id}")
async def delete_bookmark(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    bm = await db.scalar(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.job_id == job_id)
    )
    if bm:
        await db.delete(bm)
        await db.commit()
    return {"bookmarked": False, "job_id": str(job_id)}

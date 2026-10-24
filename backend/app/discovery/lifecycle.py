import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.discovery.discovery_scope import scope_keys_match
from app.discovery.employment_type import classify_employment_type
from app.discovery.india_location import classify_india_scope
from app.discovery.lifecycle_status import (
    CLOSED,
    MISSED_FOR_CLOSED,
    MISSED_FOR_POSSIBLY_CLOSED,
    OPEN,
    POSSIBLY_CLOSED,
)
from app.discovery.job_title import normalize_job_title
from app.discovery.normalize import canonicalize_url, validate_job_urls
from app.discovery.types import NormalizedJob
from app.models.enums import ListingStatus
from app.models.job import Job
from app.models.listing_event import ListingEvent


def _canonical_listing_url(url: str) -> str:
    return canonicalize_url(url.split("#")[0].split("?")[0])


async def apply_scan_results(
    session: AsyncSession,
    company_id: uuid.UUID,
    incoming: list[NormalizedJob],
    allowed_hosts: frozenset[str],
    *,
    scan_succeeded: bool = True,
    scan_complete: bool = True,
    discovery_scope_key: str | None = None,
) -> tuple[int, int, int]:
    """Upsert jobs from a scan. Returns created, updated, closed counts."""
    now = datetime.now(UTC)
    seen_keys: set[str] = set()
    created = updated = closed = 0

    for raw in incoming:
        validate_job_urls(raw, allowed_hosts)
        display_title, req_id = normalize_job_title(raw.title, raw.listing_url)
        raw.title = display_title
        scope, loc_hint = classify_india_scope(raw)
        if loc_hint and not raw.location:
            raw.location = loc_hint
        loc_meta = dict(raw.location_meta or {})
        if discovery_scope_key:
            loc_meta["discovery_scope_key"] = discovery_scope_key
        raw.location_meta = loc_meta if loc_meta else None
        employment_type = classify_employment_type(raw)
        seen_keys.add(raw.source_job_key)

        existing = await session.scalar(
            select(Job).where(
                Job.company_id == company_id,
                Job.source_job_key == raw.source_job_key,
            )
        )
        if existing is None:
            canon = _canonical_listing_url(raw.listing_url)
            dup = await session.scalar(
                select(Job).where(
                    Job.company_id == company_id,
                    Job.listing_url.like(f"{canon}%"),
                )
            )
            if dup:
                existing = dup

        if existing is None:
            job = Job(
                company_id=company_id,
                source_job_key=raw.source_job_key,
                title=raw.title,
                requisition_id=req_id,
                location=raw.location,
                india_scope=scope.value,
                location_meta=loc_meta,
                employment_type=employment_type,
                lifecycle_status=OPEN,
                last_verified_at=now,
                remote_flag=raw.remote_flag,
                description_sections=raw.description_sections,
                posted_at=raw.posted_at,
                deadline_at=raw.deadline_at,
                listing_url=raw.listing_url,
                apply_url=raw.apply_url,
                content_hash=raw.content_hash,
                listing_status=ListingStatus.active,
                missed_scan_count=0,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(job)
            await session.flush()
            session.add(
                ListingEvent(
                    company_id=company_id,
                    job_id=job.id,
                    event_type="discovered",
                    payload={"title": raw.title, "listing_url": raw.listing_url},
                )
            )
            created += 1
            continue

        changed = existing.content_hash != raw.content_hash
        existing.source_job_key = raw.source_job_key
        existing.title = raw.title
        if req_id:
            existing.requisition_id = req_id
        existing.location = raw.location
        existing.india_scope = scope.value
        existing.location_meta = loc_meta
        existing.employment_type = employment_type
        existing.remote_flag = raw.remote_flag
        existing.description_sections = raw.description_sections
        existing.posted_at = raw.posted_at
        existing.deadline_at = raw.deadline_at
        existing.listing_url = raw.listing_url
        existing.apply_url = raw.apply_url
        existing.content_hash = raw.content_hash
        existing.last_seen_at = now
        existing.last_verified_at = now
        existing.missed_scan_count = 0
        existing.lifecycle_status = OPEN
        if existing.listing_status != ListingStatus.active:
            existing.listing_status = ListingStatus.active
            session.add(
                ListingEvent(
                    company_id=company_id,
                    job_id=existing.id,
                    event_type="reactivated",
                    payload={"title": raw.title},
                )
            )
        elif changed:
            updated += 1
            session.add(
                ListingEvent(
                    company_id=company_id,
                    job_id=existing.id,
                    event_type="updated",
                    payload={"title": raw.title},
                )
            )

    if not scan_succeeded or not scan_complete:
        return created, updated, closed

    active_jobs = await session.scalars(
        select(Job).where(
            Job.company_id == company_id,
            Job.listing_status == ListingStatus.active,
        )
    )
    for job in active_jobs.all():
        if job.source_job_key in seen_keys:
            continue
        job_scope = (job.location_meta or {}).get("discovery_scope_key")
        if not scope_keys_match(job_scope, discovery_scope_key):
            continue
        job.missed_scan_count += 1
        if job.missed_scan_count >= MISSED_FOR_POSSIBLY_CLOSED:
            job.lifecycle_status = POSSIBLY_CLOSED
        if job.missed_scan_count >= MISSED_FOR_CLOSED:
            job.listing_status = ListingStatus.closed_confirmed
            job.lifecycle_status = CLOSED
            closed += 1
            session.add(
                ListingEvent(
                    company_id=company_id,
                    job_id=job.id,
                    event_type="closed",
                    payload={"title": job.title, "reason": "missing_from_scan"},
                )
            )

    return created, updated, closed

"""Apply lifecycle updates from direct official detail-page verification."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.discovery.lifecycle_status import OPEN
from app.models.job import Job
from app.models.listing_event import ListingEvent


def official_page_indicates_open(evidence: dict) -> bool:
    """True when Playwright probe shows a live listing with apply CTA and no closure copy."""
    if evidence.get("error"):
        return False
    if evidence.get("login_wall"):
        return False
    if evidence.get("closed_hint"):
        return False
    if evidence.get("http_status") not in (200, None):
        if evidence.get("http_status") == 404:
            return False
    title = (evidence.get("h1") or evidence.get("og_title") or "").strip()
    if len(title) < 4:
        return False
    return bool(evidence.get("has_apply_cta"))


async def reopen_after_official_verification(
    session: AsyncSession,
    job: Job,
    evidence: dict,
    *,
    verified_by: str = "official_detail_page",
) -> bool:
    """
    Set job back to open when official detail page confirms the listing is live.
    Returns True if the job was updated.
    """
    if not official_page_indicates_open(evidence):
        return False
    now = datetime.now(UTC)
    meta = dict(job.location_meta or {})
    meta["official_verification"] = {
        "verified_at": now.isoformat(),
        "verified_by": verified_by,
        "http_status": evidence.get("http_status"),
        "final_url": evidence.get("final_url"),
        "page_title": evidence.get("h1") or evidence.get("og_title"),
    }
    job.location_meta = meta
    job.lifecycle_status = OPEN
    job.missed_scan_count = 0
    job.last_verified_at = now
    session.add(
        ListingEvent(
            company_id=job.company_id,
            job_id=job.id,
            event_type="verified_open",
            payload={
                "title": job.title,
                "listing_url": job.listing_url,
                "verified_by": verified_by,
            },
        )
    )
    return True

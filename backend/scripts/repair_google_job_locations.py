"""Re-enrich Google listings whose location was mis-parsed as the job title."""

import asyncio
import logging

from sqlalchemy import or_, select

from app.database import SessionLocal
from app.discovery.browser import browser_page
from app.discovery.employment_type import classify_employment_type
from app.discovery.india_location import classify_india_scope
from app.discovery.location_extract import (
    _looks_like_job_title_not_location,
    extract_location_from_detail_page,
)
from app.models.company import Company
from app.models.job import Job

logger = logging.getLogger(__name__)


async def repair_google_locations(dry_run: bool = True) -> int:
    updated = 0
    async with SessionLocal() as session:
        company = await session.scalar(select(Company).where(Company.name == "Google"))
        if not company:
            logger.error("Google company not found")
            return 0
        jobs = list(
            await session.scalars(select(Job).where(Job.company_id == company.id))
        )
        targets = [
            j
            for j in jobs
            if j.location and _looks_like_job_title_not_location(j.location)
            or (j.employment_type == "internship" and j.india_scope == "unknown")
            or (
                j.employment_type == "internship"
                and not (j.location_meta or {}).get("india_site_locations")
            )
        ]
        logger.info("Google location repair candidates: %s", len(targets))

        async with browser_page() as page:
            for job in targets:
                facts = await extract_location_from_detail_page(
                    page, job.listing_url, "google_official"
                )
                if not facts.normalized_location or _looks_like_job_title_not_location(
                    facts.normalized_location
                ):
                    logger.warning("Still no geographic location for %s", job.requisition_id)
                    continue
                job.location = facts.normalized_location
                meta = dict(job.location_meta or {})
                meta.update(facts.to_meta())
                job.location_meta = meta
                scope, _loc_hint = classify_india_scope(job)
                job.india_scope = scope.value
                job.employment_type = classify_employment_type(job)
                logger.info(
                    "Repair %s -> scope=%s loc=%s",
                    job.requisition_id,
                    job.india_scope,
                    job.location,
                )
                updated += 1
        if not dry_run:
            await session.commit()
        else:
            await session.rollback()
    return updated


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    dry = "--apply" not in sys.argv
    n = asyncio.run(repair_google_locations(dry_run=dry))
    print(f"{'Would update' if dry else 'Updated'} {n} Google job(s)")

"""Re-fetch location_meta for active jobs by revisiting official listing URLs."""

import asyncio
import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.discovery.browser import browser_page
from app.discovery.india_location import classify_india_scope
from app.discovery.location_extract import extract_location_from_detail_page
from app.models.company import Company
from app.models.enums import ListingStatus
from app.models.job import Job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 200


async def main() -> None:
    async with SessionLocal() as session:
        companies = {
            c.id: c
            for c in (await session.scalars(select(Company).where(Company.is_enabled.is_(True)))).all()
        }
        jobs = (
            await session.scalars(
                select(Job)
                .where(
                    Job.listing_status == ListingStatus.active,
                    Job.company_id.in_(companies.keys()),
                )
                .limit(BATCH_SIZE)
            )
        ).all()

        if not jobs:
            logger.info("No active jobs to backfill")
            return

        adapter_keys: dict[str, str] = {}
        for cid, company in companies.items():
            if company.adapter_key:
                adapter_keys[str(cid)] = company.adapter_key

        updated = 0
        async with browser_page() as page:
            for job in jobs:
                company = companies[job.company_id]
                key = company.adapter_key
                if not key:
                    continue
                try:
                    facts = await extract_location_from_detail_page(page, job.listing_url, key)
                    job.location_meta = facts.to_meta()
                    if facts.normalized_location:
                        job.location = facts.normalized_location
                    if facts.work_mode == "remote":
                        job.remote_flag = True
                    elif facts.work_mode in ("onsite", "hybrid"):
                        job.remote_flag = False
                    scope, loc_hint = classify_india_scope(job)
                    job.india_scope = scope.value
                    if loc_hint and not job.location:
                        job.location = loc_hint
                    updated += 1
                    logger.info(
                        "%s | %s | scope=%s loc=%s",
                        company.name,
                        job.title[:60],
                        job.india_scope,
                        job.location,
                    )
                except Exception as e:
                    logger.warning("Failed %s: %s", job.listing_url, e)

        await session.commit()
        logger.info("Updated location for %s jobs", updated)


if __name__ == "__main__":
    asyncio.run(main())

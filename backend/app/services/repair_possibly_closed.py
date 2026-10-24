"""Repair possibly_closed rows caused by facet/scope mismatch or non-inventory scans."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.discovery.discovery_scope import discovery_scope_key, scope_keys_match
from app.discovery.lifecycle_status import OPEN
from app.discovery.registry import get_adapter
from app.models.company import Company
from app.models.job import Job


async def repair_incorrect_possibly_closed(session: AsyncSession) -> list[dict]:
    """
    Reopen jobs marked possibly_closed after a single miss when the miss was not
    a verified absence from the same official search facet.
    """
    repairs: list[dict] = []
    companies = (await session.scalars(select(Company))).all()
    by_id = {c.id: c for c in companies}

    jobs = (
        await session.scalars(
            select(Job).where(Job.lifecycle_status == "possibly_closed", Job.missed_scan_count <= 1)
        )
    ).all()

    for job in jobs:
        company = by_id.get(job.company_id)
        if not company or not company.adapter_key:
            continue
        try:
            adapter = get_adapter(company.adapter_key)
        except KeyError:
            continue
        current_scope = discovery_scope_key(adapter.adapter_key, adapter.discovery_search_urls)
        job_scope = (job.location_meta or {}).get("discovery_scope_key")
        reason: str | None = None

        if not scope_keys_match(job_scope, current_scope):
            if job_scope is None and company.name == "Meta":
                reason = None  # browse facet; completeness unknown — keep possibly_closed
            else:
                reason = "discovery_scope_mismatch" if job_scope else "legacy_out_of_facet"
        elif job_scope == current_scope:
            reason = None  # same facet, single miss — retain per lifecycle policy
        else:
            reason = "faceted_scan_not_inventory_complete"

        if reason:
            job.lifecycle_status = OPEN
            job.missed_scan_count = 0
            repairs.append(
                {
                    "company": company.name,
                    "job_id": str(job.id),
                    "title": job.title,
                    "listing_url": job.listing_url,
                    "reason": reason,
                }
            )

    return repairs

"""Re-open Meta possibly_closed rows after per-URL official detail verification."""

import asyncio
import json
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.discovery.official_verify import official_page_indicates_open, reopen_after_official_verification
from app.models.company import Company
from app.models.job import Job

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "verify_meta_listings", Path(__file__).resolve().parent / "verify_meta_listings.py"
)
_vml = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(_vml)
probe = _vml.probe


async def main(dry_run: bool) -> int:
    async with SessionLocal() as session:
        company = await session.scalar(select(Company).where(Company.name == "Meta"))
        jobs = (
            await session.scalars(
                select(Job).where(
                    Job.company_id == company.id,
                    Job.lifecycle_status == "possibly_closed",
                )
            )
        ).all()
        if not jobs:
            print("No Meta possibly_closed jobs")
            return 0

        report = []
        for job in jobs:
            evidence = await probe(job.listing_url)
            classification = (
                "confirmed_open"
                if official_page_indicates_open(evidence)
                else "uncertain"
                if not evidence.get("closed_hint")
                else "confirmed_closed"
            )
            updated = False
            if classification == "confirmed_open" and not dry_run:
                updated = await reopen_after_official_verification(session, job, evidence)
            report.append(
                {
                    "job_id": str(job.id),
                    "title": job.title,
                    "listing_url": job.listing_url,
                    "classification": classification,
                    "updated": updated,
                    "evidence": {
                        "http_status": evidence.get("http_status"),
                        "h1": evidence.get("h1"),
                        "has_apply_cta": evidence.get("has_apply_cta"),
                        "closed_hint": evidence.get("closed_hint"),
                    },
                }
            )
            await asyncio.sleep(2)

        if not dry_run:
            await session.commit()
        print(json.dumps(report, indent=2))
        return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    raise SystemExit(asyncio.run(main(dry)))

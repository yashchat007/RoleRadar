"""Print per-company adapter health and inventory for the 8-company registry."""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.company import Company
from app.models.job import Job
from app.models.scan_run import ScanRun
from app.services.company_registry import ACTIVE_REGISTRY_COMPANIES


async def main() -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        feed = await session.scalar(
            select(func.count()).select_from(Job).where(
                Job.employment_type == "internship",
                Job.india_scope.in_(("india_based", "remote_india", "remote_global_india_ok")),
                Job.lifecycle_status == "open",
            )
        )
        print(f"Default feed (internship + India + open): {feed}\n")
        for name in ACTIVE_REGISTRY_COMPANIES:
            company = await session.scalar(select(Company).where(Company.name == name))
            if not company:
                print(f"{name}: MISSING ROW")
                continue
            last_run = await session.scalar(
                select(ScanRun)
                .where(ScanRun.company_id == company.id)
                .order_by(ScanRun.started_at.desc())
                .limit(1)
            )
            open_n = await session.scalar(
                select(func.count()).select_from(Job).where(
                    Job.company_id == company.id, Job.lifecycle_status == "open"
                )
            )
            intern = await session.scalar(
                select(func.count()).select_from(Job).where(
                    Job.company_id == company.id,
                    Job.employment_type == "internship",
                    Job.lifecycle_status == "open",
                )
            )
            india_i = await session.scalar(
                select(func.count()).select_from(Job).where(
                    Job.company_id == company.id,
                    Job.employment_type == "internship",
                    Job.india_scope.in_(("india_based", "remote_india", "remote_global_india_ok")),
                    Job.lifecycle_status == "open",
                )
            )
            verified = company.last_success_at.isoformat() if company.last_success_at else "never"
            run_line = ""
            if last_run:
                run_line = (
                    f"last_scan={last_run.status.value} seen={last_run.jobs_seen} "
                    f"at={last_run.finished_at.isoformat() if last_run.finished_at else '?'}"
                )
            live = (
                company.is_enabled
                and company.parser_status.value == "enabled"
                and company.last_error is None
                and company.last_success_at is not None
            )
            print(f"## {name}")
            print(f"  source: {company.career_page_url}")
            print(f"  adapter: {company.adapter_key} | live={live} | enabled={company.is_enabled}")
            print(f"  last_success_at: {verified} | status={company.last_scan_status}")
            print(f"  {run_line}")
            print(f"  open={open_n} internships={intern} india_internships={india_i}")
            if company.last_error:
                print(f"  last_error: {company.last_error[:200]}")
            print()
        print(f"Report generated {now.isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from sqlalchemy import func, select
from app.database import SessionLocal
from app.models.company import Company
from app.models.job import Job
from app.models.scan_run import ScanRun
from app.services.company_registry import ACTIVE_REGISTRY_COMPANIES
from app.discovery.lifecycle_status import OPEN

async def main():
    async with SessionLocal() as s:
        print("=== Lifecycle (all jobs) ===")
        for st in ("open", "possibly_closed", "closed"):
            n = await s.scalar(select(func.count()).select_from(Job).where(Job.lifecycle_status == st))
            print(f"  {st}: {n}")
        miss = await s.scalar(select(func.count()).select_from(Job).where(Job.missed_scan_count > 0))
        print(f"  missed_scan_count>0: {miss}")

        print("\n=== Employment type (open, registry companies) ===")
        for et in ("internship", "full_time", "unknown", "contract"):
            n = await s.scalar(
                select(func.count())
                .select_from(Job)
                .join(Company)
                .where(
                    Company.name.in_(ACTIVE_REGISTRY_COMPANIES),
                    Job.lifecycle_status == OPEN,
                    Job.employment_type == et,
                )
            )
            print(f"  {et}: {n}")

        print("\n=== India scope (open internships, registry) ===")
        for scope in ("india_based", "remote_india", "remote_global_india_ok", "outside_india", "unknown"):
            n = await s.scalar(
                select(func.count())
                .select_from(Job)
                .join(Company)
                .where(
                    Company.name.in_(ACTIVE_REGISTRY_COMPANIES),
                    Job.lifecycle_status == OPEN,
                    Job.employment_type == "internship",
                    Job.india_scope == scope,
                )
            )
            print(f"  {scope}: {n}")

        feed = await s.scalar(
            select(func.count()).select_from(Job).where(
                Job.employment_type == "internship",
                Job.india_scope.in_(("india_based", "remote_india", "remote_global_india_ok")),
                Job.lifecycle_status == OPEN,
            )
        )
        print(f"\n=== Default feed count (internship+India+open): {feed} ===\n")

        print("=== Per company (open) ===")
        for name in sorted(ACTIVE_REGISTRY_COMPANIES):
            c = await s.scalar(select(Company).where(Company.name == name))
            if not c:
                continue
            open_n = await s.scalar(
                select(func.count()).select_from(Job).where(Job.company_id == c.id, Job.lifecycle_status == OPEN)
            )
            intern = await s.scalar(
                select(func.count()).select_from(Job).where(
                    Job.company_id == c.id, Job.employment_type == "internship", Job.lifecycle_status == OPEN
                )
            )
            india_i = await s.scalar(
                select(func.count()).select_from(Job).where(
                    Job.company_id == c.id,
                    Job.employment_type == "internship",
                    Job.india_scope.in_(("india_based", "remote_india", "remote_global_india_ok")),
                    Job.lifecycle_status == OPEN,
                )
            )
            pc = await s.scalar(
                select(func.count()).select_from(Job).where(
                    Job.company_id == c.id, Job.lifecycle_status == "possibly_closed"
                )
            )
            last = await s.scalar(
                select(ScanRun).where(ScanRun.company_id == c.id).order_by(ScanRun.finished_at.desc()).limit(1)
            )
            print(
                f"{name}: open={open_n} intern={intern} india_intern={india_i} "
                f"possibly_closed={pc} last_scan={last.status.value if last else '?'} seen={last.jobs_seen if last else '?'}"
            )


if __name__ == "__main__":
    asyncio.run(main())

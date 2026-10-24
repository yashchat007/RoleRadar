"""Print per-company india_scope breakdown for active jobs."""

import asyncio
from collections import defaultdict

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.company import Company
from app.models.enums import ListingStatus
from app.models.job import Job


async def main() -> None:
    async with SessionLocal() as session:
        rows = await session.execute(
            select(Company.name, Job.india_scope, func.count())
            .join(Job, Job.company_id == Company.id)
            .where(Job.listing_status == ListingStatus.active)
            .group_by(Company.name, Job.india_scope)
            .order_by(Company.name, Job.india_scope)
        )
        by_company: dict[str, dict[str | None, int]] = defaultdict(dict)
        totals: dict[str | None, int] = defaultdict(int)
        for name, scope, count in rows.all():
            by_company[name][scope] = count
            totals[scope] += count

        print("Per company (active jobs by india_scope):")
        for name in sorted(by_company):
            parts = ", ".join(f"{s or 'null'}={c}" for s, c in sorted(by_company[name].items()))
            print(f"  {name}: {parts}")

        print("\nTotals:")
        for scope in sorted(totals, key=lambda x: (x is None, x or "")):
            print(f"  {scope}: {totals[scope]}")

        india_eligible = sum(
            totals.get(s, 0)
            for s in ("india_based", "remote_india", "remote_global_india_ok")
        )
        print(f"\nIndia-eligible (default Discover): {india_eligible}")
        print(f"Unknown: {totals.get('unknown', 0)}")
        print(f"Outside India: {totals.get('outside_india', 0)}")


if __name__ == "__main__":
    asyncio.run(main())

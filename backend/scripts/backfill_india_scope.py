import asyncio

from sqlalchemy import select

from app.database import SessionLocal
from app.discovery.india_location import classify_india_scope
from app.models.job import Job


async def main() -> None:
    async with SessionLocal() as session:
        jobs = list((await session.scalars(select(Job))).all())
        for job in jobs:
            scope, loc_hint = classify_india_scope(job)
            job.india_scope = scope.value
            if loc_hint and not job.location:
                job.location = loc_hint
            if job.location_meta and isinstance(job.location_meta, dict):
                meta = job.location_meta
                if meta.get("normalized_location") and not job.location:
                    job.location = meta["normalized_location"]
        await session.commit()
        print(f"Backfilled india_scope for {len(jobs)} jobs")


if __name__ == "__main__":
    asyncio.run(main())

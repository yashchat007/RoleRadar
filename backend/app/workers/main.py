import asyncio
import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.discovery.orchestrator import scan_enabled_companies
from app.models.company import Company

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roleradar.worker")


async def scheduled_scan() -> None:
    async with SessionLocal() as session:
        companies = await session.scalars(select(Company).where(Company.is_enabled.is_(True)))
        enabled_list = list(companies.all())
        if not enabled_list:
            logger.info("No enabled companies; worker idle")
            return
        logger.info("Starting scheduled scan for %s companies", len(enabled_list))
        await scan_enabled_companies(session)


def main() -> None:
    asyncio.run(scheduled_scan())


if __name__ == "__main__":
    main()

"""Re-scan all enabled company sources (updates locations via adapters)."""

import asyncio
import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.discovery.orchestrator import scan_company
from app.models.company import Company

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    async with SessionLocal() as session:
        companies = await session.scalars(select(Company).where(Company.is_enabled.is_(True)))
        for company in companies.all():
            logger.info("Scanning %s (%s)...", company.name, company.adapter_key)
            run = await scan_company(session, company)
            logger.info(
                "%s: status=%s seen=%s created=%s updated=%s closed=%s err=%s",
                company.name,
                run.status,
                run.jobs_seen,
                run.jobs_created,
                run.jobs_updated,
                run.jobs_closed,
                run.error_message,
            )


if __name__ == "__main__":
    asyncio.run(main())

"""Validate pilot adapters (Stripe, Atlassian) and record Cloudflare failure reason."""

import asyncio
import logging

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.discovery.validation import validate_company_adapter
from app.models.company import Company
from app.services.seed import seed_companies, sync_pilot_adapter_keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PILOTS = ("Stripe", "Atlassian", "Cloudflare")


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_companies(session)
        await sync_pilot_adapter_keys(session)

    async with SessionLocal() as session:
        for name in PILOTS:
            company = await session.scalar(select(Company).where(Company.name == name))
            if not company:
                logger.error("Missing company seed: %s", name)
                continue
            logger.info("Validating %s (%s)...", name, company.adapter_key)
            result = await validate_company_adapter(session, company)
            logger.info(
                "%s: passed=%s jobs_sampled=%s message=%s",
                name,
                result.passed,
                result.jobs_sampled,
                result.message,
            )


if __name__ == "__main__":
    asyncio.run(main())

"""Live-validate adapters for all eight registry companies."""

import asyncio
import logging

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.discovery.validation import validate_company_adapter
from app.models.company import Company
from app.services.company_registry import ACTIVE_REGISTRY_COMPANIES
from app.services.seed import apply_active_company_registry, seed_companies, sync_pilot_adapter_keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_companies(session)
        await sync_pilot_adapter_keys(session)
        await apply_active_company_registry(session)

        for name in sorted(ACTIVE_REGISTRY_COMPANIES):
            company = await session.scalar(select(Company).where(Company.name == name))
            if not company:
                logger.error("Missing company row: %s", name)
                continue
            if not company.adapter_key:
                logger.warning("%s: no adapter_key — pending", name)
                continue
            logger.info("Validating %s (%s)...", name, company.adapter_key)
            result = await validate_company_adapter(session, company)
            await session.refresh(company)
            logger.info(
                "%s: passed=%s sampled=%s enabled=%s status=%s err=%s",
                name,
                result.passed,
                result.jobs_sampled,
                company.is_enabled,
                company.parser_status,
                company.last_error,
            )


if __name__ == "__main__":
    asyncio.run(main())

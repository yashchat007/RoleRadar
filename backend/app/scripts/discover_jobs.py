"""
Run official-source discovery for active registry companies.

Usage (from backend/ with venv active):
  set PYTHONPATH=.
  python -m app.scripts.discover_jobs
"""

import argparse
import asyncio
import logging
import sys

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.discovery.employment_type import classify_employment_type
from app.discovery.lifecycle_status import OPEN
from app.discovery.orchestrator import scan_company
from app.models.company import Company
from app.models.job import Job
from app.scripts.discovery_lock import acquire_discovery_lock, release_discovery_lock
from app.scripts.runtime import (
    EXIT_BUSY,
    EXIT_CONFIG,
    check_database_connection,
    finish_script,
    log_configuration_status,
    setup_script_logging,
)
from app.services.company_registry import ACTIVE_REGISTRY_COMPANIES
from app.services.seed import apply_active_company_registry, seed_companies, sync_pilot_adapter_keys

logger = logging.getLogger("roleradar.discover_jobs")


async def backfill_employment_types(session) -> int:
    jobs = (await session.scalars(select(Job))).all()
    n = 0
    for job in jobs:
        et = classify_employment_type(job)
        if job.employment_type != et:
            job.employment_type = et
            n += 1
        if not job.lifecycle_status:
            job.lifecycle_status = OPEN
    return n


async def run(only_company: str | None = None) -> int:
    db_err = await check_database_connection()
    if db_err:
        logger.error(db_err)
        return EXIT_CONFIG

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from app.scripts.schema_patches import apply_schema_patches

        await apply_schema_patches(conn)

    exit_code = 0
    async with SessionLocal() as session:
        await seed_companies(session)
        await sync_pilot_adapter_keys(session)
        await apply_active_company_registry(session)

        if only_company:
            company = await session.scalar(
                select(Company).where(
                    Company.name == only_company,
                    Company.name.in_(ACTIVE_REGISTRY_COMPANIES),
                )
            )
            active = [company] if company else []
        else:
            companies = await session.scalars(
                select(Company).where(
                    Company.name.in_(ACTIVE_REGISTRY_COMPANIES),
                    Company.is_enabled.is_(True),
                )
            )
            active = list(companies.all())
        if not active:
            logger.error("No enabled companies in the active registry")
            return 2

        for company in active:
            logger.info("Scanning %s (%s)...", company.name, company.adapter_key)
            try:
                run_row = await scan_company(session, company)
                logger.info(
                    "%s: status=%s seen=%s created=%s updated=%s closed=%s duration_ms=%s err=%s",
                    company.name,
                    run_row.status,
                    run_row.jobs_seen,
                    run_row.jobs_created,
                    run_row.jobs_updated,
                    run_row.jobs_closed,
                    run_row.duration_ms,
                    run_row.error_message,
                )
                if run_row.error_message:
                    exit_code = 1
            except Exception:
                logger.exception("Scan failed for %s", company.name)
                exit_code = 1

        n = await backfill_employment_types(session)
        await session.commit()
        if n:
            logger.info("Backfilled employment_type on %s jobs", n)

    return exit_code


def main() -> None:
    setup_script_logging("discover_jobs")
    log_configuration_status(logger)
    if not acquire_discovery_lock(logger):
        finish_script(logger, EXIT_BUSY)
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", help="Scan only this company name")
    args = parser.parse_args()
    code = 1
    try:
        code = asyncio.run(run(args.company))
    except KeyboardInterrupt:
        logger.warning("Interrupted")
        code = 130
    except Exception:
        logger.exception("Fatal error in discover_jobs")
        code = 1
    finally:
        release_discovery_lock()
    finish_script(logger, code)


if __name__ == "__main__":
    main()

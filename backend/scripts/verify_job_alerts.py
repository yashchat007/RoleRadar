"""
Verify internship alert delivery via Mailpit using real DB qualifying jobs only.

Usage:
  PYTHONPATH=. python scripts/verify_job_alerts.py
  PYTHONPATH=. python scripts/verify_job_alerts.py --dry-run
"""

import argparse
import asyncio
import sys

from sqlalchemy import func, select

from app.database import SessionLocal
from app.discovery.lifecycle_status import OPEN
from app.models.job import Job
from app.services.job_alerts import send_job_alerts
from app.services.user_bootstrap import ensure_dev_user


async def main(dry_run: bool) -> int:
    async with SessionLocal() as session:
        user = await ensure_dev_user(session)
        pending = await session.scalar(
            select(func.count()).select_from(Job).where(
                Job.employment_type == "internship",
                Job.india_scope.in_(("india_based", "remote_india", "remote_global_india_ok")),
                Job.lifecycle_status == OPEN,
            )
        )
        print(f"Qualifying open internships (India): {pending}")
        if pending == 0:
            print("No qualifying jobs to alert — run discovery first or check classification.")
            return 2
        sent, failed, errors = await send_job_alerts(session, user, dry_run=dry_run)
        print(f"sent={sent} failed={failed} errors={errors}")
        if dry_run:
            return 0
        if failed:
            return 3
        if sent == 0:
            return 4
        return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    sys.exit(asyncio.run(main(args.dry_run)))

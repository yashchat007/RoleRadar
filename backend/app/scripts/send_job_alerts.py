"""
Send email alerts for new qualifying internships (idempotent).

Usage:
  set PYTHONPATH=.
  python -m app.scripts.send_job_alerts
  python -m app.scripts.send_job_alerts --dry-run
"""

import argparse
import asyncio
import logging
import sys

from app.database import SessionLocal
from app.scripts.runtime import (
    EXIT_CONFIG,
    check_database_connection,
    finish_script,
    log_configuration_status,
    setup_script_logging,
    validate_smtp_for_alerts,
)
from app.services.job_alerts import send_job_alerts
from app.services.user_bootstrap import ensure_dev_user

logger = logging.getLogger("roleradar.send_job_alerts")


async def run(dry_run: bool) -> int:
    db_err = await check_database_connection()
    if db_err:
        logger.error(db_err)
        return EXIT_CONFIG

    smtp_err = validate_smtp_for_alerts(dry_run)
    if smtp_err:
        logger.error(smtp_err)
        return EXIT_CONFIG

    async with SessionLocal() as session:
        user = await ensure_dev_user(session)
        if not dry_run and not user.email_digest_enabled:
            logger.info("Email digest disabled for %s — exiting 0 (no send)", user.email)
            return 0

        sent, failed, errors = await send_job_alerts(session, user, dry_run=dry_run)
        if dry_run:
            if errors:
                logger.info(errors[0])
            logger.info("Dry run complete - no email sent (sent=%s failed=%s)", sent, failed)
            return 0

        if errors and failed:
            logger.error("Alert delivery failed: %s", errors[0])
            return 3
        logger.info("Sent=%s failed=%s", sent, failed)
        return 0 if failed == 0 else 3


def main() -> None:
    setup_script_logging("send_job_alerts")
    log_configuration_status(logger)
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Log recipients and counts only; never send SMTP")
    args = parser.parse_args()
    try:
        code = asyncio.run(run(args.dry_run))
    except KeyboardInterrupt:
        logger.warning("Interrupted")
        code = 130
    except Exception:
        logger.exception("Fatal error in send_job_alerts")
        code = 1
    finish_script(logger, code)


if __name__ == "__main__":
    main()

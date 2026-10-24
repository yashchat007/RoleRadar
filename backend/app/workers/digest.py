import asyncio
import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from app.services.digest import run_watch_notifications, send_daily_digest
from app.services.user_bootstrap import DEV_EMAIL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roleradar.digest")


async def run_once() -> None:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == DEV_EMAIL))
        if not user:
            logger.info("No dev user for digest")
            return
        if not user.email_digest_enabled:
            logger.info("Daily digest disabled for %s — skipping", user.email)
            return
        result = await send_daily_digest(session, user)
        if result.sent:
            logger.info("Daily digest sent to %s", user.email)
        elif result.status == "smtp_error":
            logger.error("Digest SMTP failed for %s: %s", user.email, result.smtp_error)
        else:
            logger.info("Digest not sent for %s (%s)", user.email, result.status)
        n = await run_watch_notifications(session, user)
        if n:
            logger.info("Sent %s watch notification(s)", n)


def main() -> None:
    asyncio.run(run_once())


if __name__ == "__main__":
    main()

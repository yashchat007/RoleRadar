from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.digest import DigestSendOut
from app.services.digest import run_watch_notifications, send_daily_digest

router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/send", response_model=DigestSendOut)
async def send_digest_now(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DigestSendOut:
    """Dev/trigger: send daily digest email to current user via SMTP (Mailpit)."""
    result = await send_daily_digest(db, user, force=True)
    watches = await run_watch_notifications(db, user)
    if result.status == "smtp_error":
        raise HTTPException(
            status_code=503,
            detail=result.smtp_error or "SMTP delivery failed. Start Mailpit on port 1025 or configure SMTP.",
        )
    return DigestSendOut(
        digest_sent=result.sent,
        digest_status=result.status,
        digest_detail=result.detail,
        watch_emails=watches,
        smtp_error=result.smtp_error,
    )

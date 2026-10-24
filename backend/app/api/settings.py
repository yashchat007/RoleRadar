from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsOut, SettingsPatch

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings(user: User = Depends(get_current_user)) -> SettingsOut:
    return SettingsOut(
        email=user.email,
        theme=user.theme,
        email_digest_enabled=user.email_digest_enabled,
    )


@router.patch("", response_model=SettingsOut)
async def patch_settings(
    body: SettingsPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SettingsOut:
    if body.theme is not None:
        if body.theme not in ("light", "dark", "system"):
            raise HTTPException(status_code=400, detail="theme must be light, dark, or system")
        user.theme = body.theme
    if body.email_digest_enabled is not None:
        user.email_digest_enabled = body.email_digest_enabled
    await db.commit()
    await db.refresh(user)
    return SettingsOut(
        email=user.email,
        theme=user.theme,
        email_digest_enabled=user.email_digest_enabled,
    )

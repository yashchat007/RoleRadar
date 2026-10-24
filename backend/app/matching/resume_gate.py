"""Whether the user profile includes parsed resume evidence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.resume import Resume


def profile_has_resume_evidence(profile: Profile | None) -> bool:
    if not profile:
        return False
    for field in ("skills", "education", "experience", "projects"):
        for item in getattr(profile, field) or []:
            if isinstance(item, dict) and item.get("from_resume"):
                return True
    return False


async def user_has_parsed_resume(session: AsyncSession, user_id) -> bool:
    resume = await session.scalar(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc()).limit(1)
    )
    if not resume:
        return False
    profile = await session.scalar(select(Profile).where(Profile.user_id == user_id))
    return profile_has_resume_evidence(profile)

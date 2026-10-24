from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.user import User

DEV_EMAIL = "dev@roleradar.local"


async def ensure_dev_user(session: AsyncSession) -> User:
    user = await session.scalar(select(User).where(User.email == DEV_EMAIL))
    if user:
        profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
        if not profile:
            session.add(
                Profile(
                    user_id=user.id,
                    preferences={
                        "open_to_remote": True,
                        "india_only": True,
                        "target_level": "internship",
                        "target_profile": "technical",
                        "preferred_role_families": [
                            "Software Engineering",
                            "Data/ML",
                            "Cybersecurity",
                            "IT/Infrastructure",
                        ],
                    },
                )
            )
            await session.commit()
            await session.refresh(user)
        return user
    user = User(email=DEV_EMAIL)
    session.add(user)
    await session.flush()
    session.add(
        Profile(
            user_id=user.id,
            preferences={
                "open_to_remote": True,
                "india_only": True,
                "target_level": "internship",
                "target_profile": "technical",
                "preferred_role_families": [
                    "Software Engineering",
                    "Data/ML",
                    "Cybersecurity",
                    "IT/Infrastructure",
                ],
            },
        )
    )
    await session.commit()
    await session.refresh(user)
    return user

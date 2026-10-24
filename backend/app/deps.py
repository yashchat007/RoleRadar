from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.user_bootstrap import ensure_dev_user


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    return await ensure_dev_user(db)

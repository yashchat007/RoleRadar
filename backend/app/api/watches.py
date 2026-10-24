import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.watch import Watch
from app.schemas.watch import WatchCreate, WatchOut

router = APIRouter(prefix="/watches", tags=["watches"])


@router.get("", response_model=list[WatchOut])
async def list_watches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Watch]:
    result = await db.scalars(select(Watch).where(Watch.user_id == user.id).order_by(Watch.created_at.desc()))
    return list(result.all())


@router.post("", response_model=WatchOut)
async def create_watch(
    body: WatchCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Watch:
    canonical = json.dumps(body.filters or {}, sort_keys=True, default=str)
    existing = await db.scalars(select(Watch).where(Watch.user_id == user.id))
    for row in existing.all():
        if json.dumps(row.filters or {}, sort_keys=True, default=str) == canonical:
            raise HTTPException(status_code=409, detail="A watch with the same filters already exists")
    watch = Watch(user_id=user.id, name=body.name, filters=body.filters)
    db.add(watch)
    await db.commit()
    await db.refresh(watch)
    return watch


@router.delete("/{watch_id}")
async def delete_watch(
    watch_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    watch = await db.scalar(select(Watch).where(Watch.id == watch_id, Watch.user_id == user.id))
    if not watch:
        raise HTTPException(status_code=404, detail="Watch not found")
    await db.delete(watch)
    await db.commit()
    return {"deleted": True}

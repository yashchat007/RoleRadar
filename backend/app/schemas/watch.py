import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WatchOut(BaseModel):
    id: uuid.UUID
    name: str
    filters: dict
    created_at: datetime
    last_notified_at: datetime | None


class WatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    filters: dict = Field(default_factory=dict)

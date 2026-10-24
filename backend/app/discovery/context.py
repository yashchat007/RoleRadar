from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from app.models.company import Company

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class ScanContext:
    company: Company
    http: httpx.AsyncClient | None
    user_agent: str
    page: Page | None = None
    max_jobs: int | None = None

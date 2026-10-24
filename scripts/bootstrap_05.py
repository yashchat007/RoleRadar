import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("backend/app/discovery/types.py", """from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedJob:
    source_job_key: str
    title: str
    location: str | None
    remote_flag: bool | None
    description_sections: dict
    posted_at: datetime | None
    deadline_at: datetime | None
    apply_url: str
    listing_url: str
    content_hash: str


@dataclass
class AdapterResult:
    jobs: list[NormalizedJob] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fatal_error: str | None = None


@dataclass
class InspectionReport:
    extraction_mode: str
    allowed_hosts: list[str]
    notes: str = ""
""")

w("backend/app/discovery/compliance.py", """from urllib.parse import urlparse

from app.config import settings


def is_host_blocklisted(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return any(host == blocked or host.endswith("." + blocked) for blocked in settings.discovery_blocklist_hosts)


def assert_official_url(url: str, allowed_hosts: frozenset[str]) -> None:
    if is_host_blocklisted(url):
        raise ValueError(f"Blocked job source host: {url}")
    host = urlparse(url).hostname or ""
    if not any(host == h or host.endswith("." + h) for h in allowed_hosts):
        raise ValueError(f"URL host not allowlisted for company: {url}")
""")

w("backend/app/discovery/registry.py", """from collections.abc import Callable

from app.discovery.adapters.cloudflare import CloudflareOfficialAdapter
from app.discovery.adapters.stripe import StripeOfficialAdapter
from app.discovery.adapters.atlassian import AtlassianOfficialAdapter

ADAPTERS: dict[str, Callable[[], object]] = {
    "cloudflare_official": CloudflareOfficialAdapter,
    "stripe_official": StripeOfficialAdapter,
    "atlassian_official": AtlassianOfficialAdapter,
}


def get_adapter(adapter_key: str):
    factory = ADAPTERS.get(adapter_key)
    if not factory:
        raise KeyError(adapter_key)
    return factory()
""")

w("backend/app/discovery/adapters/base.py", """from abc import ABC, abstractmethod

from app.discovery.types import AdapterResult, InspectionReport


class OfficialSiteAdapter(ABC):
    adapter_key: str
    official_hosts: frozenset[str]

    @abstractmethod
    async def inspect(self) -> InspectionReport: ...

    @abstractmethod
    async def extract_listings(self) -> AdapterResult: ...
""")

w("backend/app/discovery/adapters/cloudflare.py", """from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.types import AdapterResult, InspectionReport


class CloudflareOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "cloudflare_official"
    official_hosts = frozenset({"www.cloudflare.com", "cloudflare.com"})

    async def inspect(self) -> InspectionReport:
        return InspectionReport(
            extraction_mode="static_html",
            allowed_hosts=list(self.official_hosts),
            notes="Pilot adapter stub; implement HTML extraction from official careers pages.",
        )

    async def extract_listings(self) -> AdapterResult:
        return AdapterResult(fatal_error="Adapter not yet validated for scheduled scans")
""")

w("backend/app/discovery/adapters/stripe.py", """from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.types import AdapterResult, InspectionReport


class StripeOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "stripe_official"
    official_hosts = frozenset({"stripe.com"})

    async def inspect(self) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Pilot adapter stub; Playwright on stripe.com/jobs only.",
        )

    async def extract_listings(self) -> AdapterResult:
        return AdapterResult(fatal_error="Adapter not yet validated for scheduled scans")
""")

w("backend/app/discovery/adapters/atlassian.py", """from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.types import AdapterResult, InspectionReport


class AtlassianOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "atlassian_official"
    official_hosts = frozenset({"www.atlassian.com", "atlassian.com"})

    async def inspect(self) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Pilot adapter stub; DOM extraction on atlassian.com careers paths only.",
        )

    async def extract_listings(self) -> AdapterResult:
        return AdapterResult(fatal_error="Adapter not yet validated for scheduled scans")
""")

w("backend/app/workers/main.py", """import asyncio
import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.models.company import Company

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("roleradar.worker")


async def run_once() -> None:
    async with SessionLocal() as session:
        companies = await session.scalars(select(Company).where(Company.is_enabled.is_(True)))
        enabled = list(companies.all())
        if not enabled:
            logger.info("No enabled companies; worker idle")
            return
        for company in enabled:
            logger.info("Scan scheduled for %s (%s)", company.name, company.adapter_key)


def main() -> None:
    asyncio.run(run_once())


if __name__ == "__main__":
    main()
""")

w("backend/app/schemas/__init__.py", "")
w("backend/app/services/__init__.py", "")

print("discovery ok")

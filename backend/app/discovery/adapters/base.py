from abc import ABC, abstractmethod

from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport


class OfficialSiteAdapter(ABC):
    adapter_key: str
    official_hosts: frozenset[str]
    # Official search facet URLs; scans are not full-company inventories.
    discovery_search_urls: tuple[str, ...] = ()

    @abstractmethod
    async def inspect(self, ctx: ScanContext) -> InspectionReport: ...

    @abstractmethod
    async def extract_listings(self, ctx: ScanContext) -> AdapterResult: ...

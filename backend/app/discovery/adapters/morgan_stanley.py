import re

from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_search_facets
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(r"^https://morganstanley\.eightfold\.ai/careers/job/\d+", re.I)
SEARCH_URLS = (
    "https://morganstanley.eightfold.ai/careers?query=intern%20india",
    "https://morganstanley.eightfold.ai/careers?query=intern%20bengaluru",
    "https://morganstanley.eightfold.ai/careers?query=intern%20mumbai",
)


class MorganStanleyOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "morgan_stanley_official"
    official_hosts = frozenset({"morganstanley.eightfold.ai"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Eightfold intern+India city facets.",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Morgan Stanley extraction")
        urls, titles, warnings, facet_by_url = await harvest_search_facets(
            ctx.page, SEARCH_URLS, LISTING_RE, scroll_rounds=16, page_load_ms=6000
        )
        return await facet_harvest_to_jobs(
            ctx, urls, self.official_hosts, titles, self.adapter_key, warnings, facet_by_url=facet_by_url
        )

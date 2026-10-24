import re

from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_search_facets
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(r"^https://apply\.careers\.microsoft\.com/careers/job/\d+", re.I)
SEARCH_URLS = (
    "https://apply.careers.microsoft.com/careers?query=intern&location=India",
    "https://apply.careers.microsoft.com/careers?query=internship&location=India",
    "https://apply.careers.microsoft.com/careers?query=intern&location=Bengaluru,%20India",
)


class MicrosoftOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "microsoft_official"
    official_hosts = frozenset({"apply.careers.microsoft.com", "careers.microsoft.com"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="India intern search facets on apply.careers.microsoft.com.",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Microsoft extraction")
        urls, titles, warnings, facet_by_url = await harvest_search_facets(
            ctx.page, SEARCH_URLS, LISTING_RE, scroll_rounds=16, page_load_ms=6000
        )
        return await facet_harvest_to_jobs(
            ctx, urls, self.official_hosts, titles, self.adapter_key, warnings, facet_by_url=facet_by_url
        )

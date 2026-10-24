import re

from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_browser import title_from_slug
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_search_facets
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(r"^https://higher\.gs\.com/roles/\d+", re.I)
SEARCH_URLS = (
    "https://higher.gs.com/results?keyword=intern&location=Bengaluru",
    "https://higher.gs.com/results?keyword=intern&location=India",
    "https://higher.gs.com/results?keyword=intern",
)


class GoldmanSachsOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "goldman_official"
    official_hosts = frozenset({"higher.gs.com"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="higher.gs.com intern facets (campus; not full firm inventory).",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Goldman Sachs extraction")
        urls, titles, warnings, facet_by_url = await harvest_search_facets(
            ctx.page, SEARCH_URLS, LISTING_RE, scroll_rounds=14, page_load_ms=7000
        )
        for u in urls:
            titles.setdefault(u, title_from_slug(u))
        return await facet_harvest_to_jobs(
            ctx, urls, self.official_hosts, titles, self.adapter_key, warnings, facet_by_url=facet_by_url
        )

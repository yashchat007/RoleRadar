import re

from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_amazon_search
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(r"^https://www\.amazon\.jobs/en/jobs/\d+/[a-z0-9-]+", re.I)
SEARCH_URLS = ("https://www.amazon.jobs/en/search?base_query=intern&loc_query=India",)


class AmazonOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "amazon_official"
    official_hosts = frozenset({"www.amazon.jobs", "amazon.jobs"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="amazon.jobs intern+India with offset pagination.",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Amazon extraction")
        urls, titles, warnings, facet_by_url = await harvest_amazon_search(
            ctx.page, LISTING_RE, base_query="intern", loc_query="India", max_pages=30
        )
        return await facet_harvest_to_jobs(
            ctx,
            urls,
            self.official_hosts,
            titles,
            self.adapter_key,
            warnings,
            facet_by_url=facet_by_url,
            enrich_max=80,
        )

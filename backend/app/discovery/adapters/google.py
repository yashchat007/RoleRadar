import re

from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_search_facets
from app.discovery.context import ScanContext
from app.discovery.india_location import location_from_listing_url
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(
    r"^https://www\.google\.com/about/careers/applications/jobs/results/\d+-[a-z0-9-]+",
    re.I,
)
SEARCH_URLS = (
    "https://www.google.com/about/careers/applications/jobs/results?location=India&employment_type=INTERN",
    "https://www.google.com/about/careers/applications/jobs/results?location=Bengaluru,%20India&employment_type=INTERN",
    "https://www.google.com/about/careers/applications/jobs/results?location=Hyderabad,%20India&employment_type=INTERN",
)


class GoogleOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "google_official"
    official_hosts = frozenset({"www.google.com", "google.com"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="India INTERN facets on google.com/about/careers (not full company inventory).",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Google extraction")
        urls, titles, warnings, facet_by_url = await harvest_search_facets(
            ctx.page, SEARCH_URLS, LISTING_RE, scroll_rounds=20, page_load_ms=5000
        )
        result = await facet_harvest_to_jobs(
            ctx, urls, self.official_hosts, titles, self.adapter_key, warnings, facet_by_url=facet_by_url
        )
        for job in result.jobs:
            loc = location_from_listing_url(job.listing_url)
            if loc and not job.location:
                job.location = loc
        return result

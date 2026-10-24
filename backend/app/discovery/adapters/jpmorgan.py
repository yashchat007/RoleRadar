import re

from app.config import settings
from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_browser import title_from_slug
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_search_facets
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(
    r"^https://jpmc\.fa\.oraclecloud\.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/\d+",
    re.I,
)
# Official India internship search (country locationId) — primary facet.
INDIA_INTERN_JOBS = (
    "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?"
    "keyword=intern&location=India&locationId=300000000289360&locationLevel=country&mode=location"
)
SEARCH_URLS = (
    INDIA_INTERN_JOBS,
    "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?"
    "keyword=intern&location=India",
)


class JPMorganOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "jpmorgan_official"
    official_hosts = frozenset({"jpmc.fa.oraclecloud.com"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Oracle CX India intern search (country locationId) with load-more scroll.",
            inventory_complete=False,
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for JPMorgan extraction")
        urls, titles, warnings, facet_by_url = await harvest_search_facets(
            ctx.page,
            SEARCH_URLS,
            LISTING_RE,
            scroll_rounds=32,
            page_load_ms=8000,
            click_load_more=True,
        )
        clean_urls = list(dict.fromkeys(u.split("?")[0] for u in urls))
        clean_facets = {
            u.split("?")[0].rstrip("/"): facet_by_url.get(u.split("?")[0].rstrip("/"), "")
            for u in urls
        }
        warnings.append(f"JPM: {len(clean_urls)} unique job URL(s) after dedupe across facets")
        return await facet_harvest_to_jobs(
            ctx,
            clean_urls,
            self.official_hosts,
            titles,
            self.adapter_key,
            warnings,
            title_resolver=lambda url: title_from_slug(url),
            facet_by_url=clean_facets,
            safety_max=settings.discovery_jpm_safety_max_jobs_per_scan,
        )

import re

from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_browser import (
    build_jobs_from_listing_urls,
    collect_hrefs,
    link_text_by_href,
    scroll_page,
    title_from_slug,
    unique_matching_urls,
)
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(r"^https://jobs\.apple\.com/en-us/details/\d+-\d+/[a-z0-9-]+", re.I)
SEARCH_URLS = (
    "https://jobs.apple.com/en-us/search?location=india-INDC",
    "https://jobs.apple.com/en-us/search?location=united-states-USA",
)


class AppleOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "apple_official"
    official_hosts = frozenset({"jobs.apple.com"})

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Listings on jobs.apple.com/en-us/details/{id}-{ref}/{slug}",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Apple extraction")
        page = ctx.page
        urls: list[str] = []
        titles: dict[str, str] = {}
        for search_url in SEARCH_URLS:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=120_000)
            await page.wait_for_timeout(8000)
            await scroll_page(page, 8)
            hrefs = await collect_hrefs(page)
            for u in unique_matching_urls(hrefs, LISTING_RE):
                if u not in urls:
                    urls.append(u)
            titles.update(await link_text_by_href(page))
        return await build_jobs_from_listing_urls(
            ctx,
            urls,
            self.official_hosts,
            titles,
            title_resolver=title_from_slug,
            adapter_key=self.adapter_key,
        )

import re

from app.config import settings
from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.context import ScanContext
from app.discovery.location_extract import extract_location_from_current_page
from app.discovery.normalize import canonicalize_url, content_hash, source_job_key_from_url
from app.discovery.types import AdapterResult, InspectionReport, NormalizedJob

DETAIL_PATH = re.compile(r"/company/careers/details/\d+")


class AtlassianOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "atlassian_official"
    official_hosts = frozenset({"www.atlassian.com", "atlassian.com"})

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Job index at atlassian.com/company/careers/all-jobs with detail pages under /details/{id}",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Atlassian extraction")

        page = ctx.page
        index_url = "https://www.atlassian.com/company/careers/all-jobs"
        await page.goto(index_url, wait_until="domcontentloaded", timeout=120_000)
        await page.wait_for_timeout(6000)

        hrefs = await page.eval_on_selector_all(
            "a[href*='/company/careers/details/']",
            "els => els.map(e => e.href)",
        )
        detail_urls = []
        for href in hrefs:
            url = canonicalize_url(href.split("#")[0])
            if DETAIL_PATH.search(url):
                detail_urls.append(url)
        detail_urls = sorted(set(detail_urls))

        if not detail_urls:
            return AdapterResult(fatal_error="No atlassian.com career detail URLs found")

        jobs: list[NormalizedJob] = []
        cap = ctx.max_jobs or settings.discovery_max_jobs_per_scan
        limit = min(len(detail_urls), cap)
        warnings: list[str] = []

        for listing_url in detail_urls[:limit]:
            await page.goto(listing_url, wait_until="domcontentloaded", timeout=120_000)
            await page.wait_for_timeout(1500)
            title = ""
            if await page.locator("h1").count():
                title = (await page.locator("h1").first.inner_text()).strip()
            if not title:
                warnings.append(f"Missing title for {listing_url}")
                continue
            facts = await extract_location_from_current_page(page, listing_url, self.adapter_key)
            location = facts.normalized_location
            remote_flag = True if facts.work_mode == "remote" else False if facts.work_mode else None
            description = {"summary": title}
            jobs.append(
                NormalizedJob(
                    source_job_key=source_job_key_from_url(listing_url),
                    title=title,
                    location=location,
                    remote_flag=remote_flag,
                    description_sections=description,
                    posted_at=None,
                    deadline_at=None,
                    apply_url=listing_url,
                    listing_url=listing_url,
                    content_hash=content_hash(title, location, description),
                    location_meta=facts.to_meta(),
                )
            )

        if not jobs:
            return AdapterResult(fatal_error="Could not parse any Atlassian job titles from detail pages")

        if len(detail_urls) > limit:
            warnings.append(f"Truncated to {limit} detail pages (found {len(detail_urls)})")

        return AdapterResult(jobs=jobs, warnings=warnings)

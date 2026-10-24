import re

from app.config import settings
from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.context import ScanContext
from app.discovery.location_extract import enrich_jobs_with_detail_locations
from app.discovery.normalize import canonicalize_url, content_hash, source_job_key_from_url
from app.discovery.types import AdapterResult, InspectionReport, NormalizedJob

LISTING_PATH = re.compile(r"/careers/listing/[^/]+/\d+")


class StripeOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "stripe_official"
    official_hosts = frozenset({"stripe.com"})

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes="Listings rendered on stripe.com/jobs/search; detail pages on stripe.com/careers/listing/…",
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Stripe extraction")

        page = ctx.page
        search_url = ctx.company.career_page_url.rstrip("/")
        if not search_url.endswith("/search"):
            search_url = "https://stripe.com/jobs/search"

        await page.goto(search_url, wait_until="domcontentloaded", timeout=90_000)
        for _ in range(12):
            await page.mouse.wheel(0, 2400)
            await page.wait_for_timeout(600)

        raw_items = await page.eval_on_selector_all(
            "a[href*='/careers/listing/']",
            """els => els.map(e => ({
                href: e.href,
                text: (e.innerText || '').trim()
            }))""",
        )

        by_url: dict[str, str] = {}
        for item in raw_items:
            href = canonicalize_url(item["href"])
            if not LISTING_PATH.search(href):
                continue
            title = item["text"].split("\n")[0].strip()
            if title:
                by_url[href] = title

        if not by_url:
            return AdapterResult(fatal_error="No stripe.com listing URLs found on jobs search page")

        jobs: list[NormalizedJob] = []
        cap = ctx.max_jobs or settings.discovery_max_jobs_per_scan
        limit = min(len(by_url), cap)
        for listing_url in list(by_url.keys())[:limit]:
            title = by_url[listing_url]
            description = {"summary": title}
            jobs.append(
                NormalizedJob(
                    source_job_key=source_job_key_from_url(listing_url),
                    title=title,
                    location=None,
                    remote_flag=None,
                    description_sections=description,
                    posted_at=None,
                    deadline_at=None,
                    apply_url=listing_url,
                    listing_url=listing_url,
                    content_hash=content_hash(title, None, description),
                )
            )

        warnings: list[str] = []
        if len(by_url) > limit:
            warnings.append(f"Truncated to {limit} listings (found {len(by_url)})")

        warnings.extend(await enrich_jobs_with_detail_locations(page, jobs, self.adapter_key))

        return AdapterResult(jobs=jobs, warnings=warnings)

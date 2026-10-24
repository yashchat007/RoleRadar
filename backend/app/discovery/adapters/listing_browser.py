"""Shared helpers for official-site job link extraction via Playwright."""

import re
from collections.abc import Callable

from app.config import settings
from app.discovery.context import ScanContext
from app.discovery.location_extract import enrich_jobs_with_detail_locations
from app.discovery.normalize import (
    canonicalize_url,
    content_hash,
    requisition_id_from_url,
    source_job_key_from_url,
    validate_job_urls,
)
from app.discovery.types import AdapterResult, NormalizedJob

_INDIA_FACET = re.compile(
    r"india|bengaluru|bangalore|hyderabad|mumbai|gurugram|gurgaon|delhi|pune|chennai",
    re.I,
)
_INTERN_FACET = re.compile(r"intern|internship|employment_type=intern", re.I)


def meta_from_discovery_facet(facet_url: str | None) -> dict:
    if not facet_url:
        return {}
    meta: dict = {
        "discovery_facet_url": facet_url,
        "evidence": f"official_search_facet={facet_url}",
    }
    # Search facet URL alone is not proof a listing is India-based (e.g. India search returning Riyadh).
    if _INDIA_FACET.search(facet_url):
        meta["discovery_facet_india_hint"] = True
    if _INTERN_FACET.search(facet_url):
        meta["employment_type_hint"] = "internship"
    return meta


async def scroll_page(page, rounds: int = 8) -> None:
    for _ in range(rounds):
        await page.mouse.wheel(0, 2200)
        await page.wait_for_timeout(500)


def unique_matching_urls(hrefs: list[str], pattern: re.Pattern[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for href in hrefs:
        url = canonicalize_url(href.split("#")[0])
        path_only = url.split("?")[0]
        if not pattern.search(path_only):
            continue
        req = requisition_id_from_url(path_only)
        dedupe_key = f"req:{req}" if req else path_only.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        out.append(url)
    return out


async def collect_hrefs(page) -> list[str]:
    return await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")


async def link_text_by_href(page) -> dict[str, str]:
    pairs = await page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => ({href: e.href, text: (e.innerText || '').trim()}))",
    )
    out: dict[str, str] = {}
    for row in pairs:
        href = row.get("href") or ""
        text = (row.get("text") or "").strip()
        if href and text and len(text) > 2:
            out[canonicalize_url(href.split("#")[0])] = text.split("\n")[0].strip()
    return out


def title_from_slug(url: str) -> str:
    path = url.split("?")[0].rstrip("/").split("/")[-1]
    if path.isdigit():
        return f"Role {path}"
    return path.replace("-", " ").strip().title()


async def build_jobs_from_listing_urls(
    ctx: ScanContext,
    listing_urls: list[str],
    allowed_hosts: frozenset[str],
    titles: dict[str, str],
    title_resolver: Callable[[str], str] | None = None,
    adapter_key: str = "",
    enrich_locations: bool = True,
    safety_max: int | None = None,
    facet_by_url: dict[str, str] | None = None,
    enrich_max: int | None = None,
) -> AdapterResult:
    if not listing_urls:
        return AdapterResult(fatal_error="No official job listing URLs matched")

    cap = safety_max or ctx.max_jobs or settings.discovery_safety_max_jobs_per_scan
    limit = min(len(listing_urls), cap)
    jobs: list[NormalizedJob] = []
    warnings: list[str] = []

    for listing_url in listing_urls[:limit]:
        title = titles.get(listing_url) or (title_resolver(listing_url) if title_resolver else title_from_slug(listing_url))
        if not title or title.lower() in ("apply", "learn more"):
            warnings.append(f"Skipped weak title for {listing_url}")
            continue
        description = {"summary": title}
        url_key = listing_url.split("?")[0].rstrip("/")
        facet_url = (facet_by_url or {}).get(url_key)
        job = NormalizedJob(
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
            location_meta=meta_from_discovery_facet(facet_url),
        )
        try:
            validate_job_urls(job, allowed_hosts)
        except ValueError as e:
            warnings.append(str(e))
            continue
        jobs.append(job)

    if not jobs:
        return AdapterResult(fatal_error="No ingestible jobs after URL validation", warnings=warnings)

    if enrich_locations and ctx.page is not None and adapter_key:
        cap = enrich_max or settings.discovery_detail_enrich_max_jobs
        warnings.extend(
            await enrich_jobs_with_detail_locations(ctx.page, jobs, adapter_key, max_jobs=cap)
        )

    if len(listing_urls) > limit:
        warnings.append(f"Truncated to {limit} listings (found {len(listing_urls)})")

    return AdapterResult(jobs=jobs, warnings=warnings)

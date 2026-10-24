"""Exhaustive facet harvesting with scroll/pagination and explicit coverage reporting."""

from __future__ import annotations

import re
from collections.abc import Callable

from app.config import settings
from app.discovery.playwright_retry import goto_with_retry
from app.discovery.adapters.listing_browser import (
    build_jobs_from_listing_urls,
    collect_hrefs,
    link_text_by_href,
    unique_matching_urls,
)
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult


async def _try_click_load_more(page) -> bool:
    """Oracle CX and similar sites expose explicit load-more controls beyond scroll."""
    selectors = (
        "button:has-text('Show More')",
        "button:has-text('Show more')",
        "button:has-text('Load More')",
        "button:has-text('Load more')",
        "[data-automation-id='loadMoreJobsButton']",
        "[aria-label*='Load more']",
        "[aria-label*='Show more']",
    )
    for sel in selectors:
        loc = page.locator(sel).first
        try:
            if await loc.count() == 0 or not await loc.is_visible():
                continue
            await loc.click(timeout=8000)
            await page.wait_for_timeout(1800)
            return True
        except Exception:
            continue
    return False


async def scroll_collect_listings(
    page,
    listing_re: re.Pattern[str],
    *,
    max_rounds: int = 18,
    stagnant_limit: int = 4,
    wheel_delta: int = 2400,
    pause_ms: int = 600,
    click_load_more: bool = False,
) -> list[str]:
    """Scroll until listing URL count stops growing or limits hit."""
    seen: set[str] = set()
    stagnant = 0
    for _ in range(max_rounds):
        hrefs = await collect_hrefs(page)
        batch = unique_matching_urls(hrefs, listing_re)
        before = len(seen)
        for u in batch:
            seen.add(u.split("?")[0].rstrip("/"))
        if len(seen) == before:
            if click_load_more and await _try_click_load_more(page):
                stagnant = 0
                continue
            stagnant += 1
            if stagnant >= stagnant_limit:
                break
        else:
            stagnant = 0
        await page.mouse.wheel(0, wheel_delta)
        await page.wait_for_timeout(pause_ms)
    return sorted(seen)


async def harvest_search_facets(
    page,
    search_urls: tuple[str, ...] | list[str],
    listing_re: re.Pattern[str],
    *,
    scroll_rounds: int = 18,
    page_load_ms: int = 5000,
    between_facet_ms: int = 800,
    click_load_more: bool = False,
) -> tuple[list[str], dict[str, str], list[str], dict[str, str]]:
    """Visit each official search facet; merge unique listing URLs and link titles."""
    warnings: list[str] = []
    merged: list[str] = []
    titles: dict[str, str] = {}
    facet_by_url: dict[str, str] = {}
    for facet_url in search_urls:
        await goto_with_retry(
            page,
            facet_url,
            timeout_ms=120_000,
            max_attempts=settings.discovery_playwright_goto_max_attempts,
            label=facet_url[:80],
        )
        await page.wait_for_timeout(page_load_ms)
        facet_urls = await scroll_collect_listings(
            page, listing_re, max_rounds=scroll_rounds, click_load_more=click_load_more
        )
        warnings.append(f"Facet {facet_url} harvested {len(facet_urls)} listing URL(s)")
        for u in facet_urls:
            key = u.split("?")[0].rstrip("/")
            facet_by_url.setdefault(key, facet_url)
            if u not in merged:
                merged.append(u)
        titles.update(await link_text_by_href(page))
        await page.wait_for_timeout(between_facet_ms)
    warnings.insert(0, f"Harvest: discovered {len(merged)} unique listing URL(s) across {len(search_urls)} facet(s)")
    return merged, titles, warnings, facet_by_url


async def harvest_amazon_search(
    page,
    listing_re: re.Pattern[str],
    *,
    base_query: str = "intern",
    loc_query: str = "India",
    page_size: int = 10,
    max_pages: int = 25,
) -> tuple[list[str], dict[str, str], list[str], dict[str, str]]:
    warnings: list[str] = []
    merged: list[str] = []
    titles: dict[str, str] = {}
    for page_idx in range(max_pages):
        offset = page_idx * page_size
        url = (
            f"https://www.amazon.jobs/en/search?base_query={base_query}"
            f"&loc_query={loc_query}&offset={offset}"
        )
        await goto_with_retry(
            page,
            url,
            timeout_ms=120_000,
            max_attempts=settings.discovery_playwright_goto_max_attempts,
            label=f"amazon offset={offset}",
        )
        await page.wait_for_timeout(4000)
        hrefs = await collect_hrefs(page)
        batch = unique_matching_urls(hrefs, listing_re)
        new = [u for u in batch if u not in merged]
        warnings.append(f"Amazon offset={offset}: {len(batch)} links ({len(new)} new)")
        if not new and page_idx > 0:
            break
        for u in new:
            merged.append(u)
        titles.update(await link_text_by_href(page))
        if len(batch) < page_size:
            break
    warnings.insert(0, f"Harvest: discovered {len(merged)} unique Amazon listing URL(s)")
    facet_url = f"https://www.amazon.jobs/en/search?base_query={base_query}&loc_query={loc_query}"
    facet_by_url = {u.split("?")[0].rstrip("/"): facet_url for u in merged}
    return merged, titles, warnings, facet_by_url


async def facet_harvest_to_jobs(
    ctx: ScanContext,
    urls: list[str],
    allowed_hosts: frozenset[str],
    titles: dict[str, str],
    adapter_key: str,
    warnings: list[str],
    *,
    title_resolver: Callable[[str], str] | None = None,
    enrich_locations: bool = True,
    facet_by_url: dict[str, str] | None = None,
    safety_max: int | None = None,
    enrich_max: int | None = None,
    allow_empty_harvest: bool = False,
) -> AdapterResult:
    if not urls:
        if allow_empty_harvest:
            warnings.append("Harvest: 0 official listing URLs (facet returned no matching jobs)")
            return AdapterResult(jobs=[], warnings=warnings)
        return AdapterResult(fatal_error="No official job listing URLs matched", warnings=warnings)

    safety = safety_max or settings.discovery_safety_max_jobs_per_scan
    if len(urls) > safety:
        warnings.append(
            f"Truncated to {safety} listings (discovered {len(urls)}); safety cap — facet inventory incomplete"
        )
    else:
        warnings.append(f"Harvest: ingesting {min(len(urls), safety)} of {len(urls)} discovered URL(s)")

    return await build_jobs_from_listing_urls(
        ctx,
        urls,
        allowed_hosts,
        titles,
        title_resolver=title_resolver,
        adapter_key=adapter_key,
        enrich_locations=enrich_locations,
        safety_max=safety,
        facet_by_url=facet_by_url,
        enrich_max=enrich_max,
    )

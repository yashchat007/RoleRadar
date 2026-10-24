import re

from app.config import settings
from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs
from app.discovery.context import ScanContext
from app.discovery.location_extract import extract_location_from_detail_page
from app.discovery.playwright_retry import goto_with_retry
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(r"^https://careers\.bankofamerica\.com/en-us/job-detail/\d+", re.I)
SEARCH_URLS = (
    "https://careers.bankofamerica.com/en-us/job-search?keywords=intern&locationsearch=India",
    "https://careers.bankofamerica.com/en-us/job-search?keywords=internship&locationsearch=India",
    "https://careers.bankofamerica.com/en-us/job-search?keywords=summer%20analyst&locationsearch=India",
    "https://careers.bankofamerica.com/en-us/job-search?keywords=intern&locationsearch=Bengaluru",
    "https://careers.bankofamerica.com/en-us/job-search?keywords=summer%20analyst&locationsearch=Bengaluru",
)

_INDIA_SLUG_MARKERS = (
    "-india-",
    "-bengaluru-",
    "-mumbai-",
    "-chennai-",
    "-hyderabad-",
    "-gurugram-",
    "-gurgaon-",
    "-pune-",
    "-delhi-",
    "-new-delhi-",
    "-gandhinagar-",
)

_INTERN_CARD = re.compile(
    r"\b(intern|internship|summer\s+analyst|student|campus|graduate\s+program|veterans\s+associate)\b",
    re.I,
)
_INDIA_CARD = re.compile(r"\bIndia\b", re.I)


def _bofa_slug_indicates_india(url: str) -> bool:
    lower = url.lower().split("?")[0]
    return any(marker in lower for marker in _INDIA_SLUG_MARKERS) or lower.rstrip("/").endswith("-india")


def _facts_india_eligible(facts) -> bool:
    if facts.india_eligible is True:
        return True
    if "India" in (facts.countries or []):
        return True
    loc = (facts.normalized_location or "").lower()
    return bool(re.search(r"\bindia\b", loc))


def _card_passes_intern_india(card_text: str) -> bool:
    if not _INDIA_CARD.search(card_text):
        return False
    return bool(_INTERN_CARD.search(card_text))


async def _harvest_bofa_search_pages(
    page,
    base_url: str,
    *,
    max_pages: int = 4,
    rows: int = 10,
    page_load_ms: int = 7000,
) -> tuple[list[str], dict[str, str], list[str]]:
    """Use official result-card text (not URL slug) for India + intern/student evidence."""
    warnings: list[str] = []
    urls: list[str] = []
    titles: dict[str, str] = {}
    for page_idx in range(max_pages):
        start = page_idx * rows
        sep = "&" if "?" in base_url else "?"
        url = f"{base_url}{sep}start={start}&rows={rows}"
        await goto_with_retry(page, url, label=f"BofA search start={start}")
        await page.wait_for_timeout(page_load_ms)
        rows_data = await page.evaluate(
            """() => {
              const out = [];
              document.querySelectorAll('a[href*="/job-detail/"]').forEach(a => {
                let node = a;
                let card = '';
                for (let i = 0; i < 8 && node; i++) {
                  const t = (node.innerText || '').trim();
                  if (t.length > 60) { card = t; break; }
                  node = node.parentElement;
                }
                const href = a.href.split('?')[0];
                const title = (a.innerText || '').trim().split('\\n')[0];
                out.push({href, card, title});
              });
              return out;
            }"""
        )
        kept = 0
        for row in rows_data:
            href = row.get("href") or ""
            card = row.get("card") or ""
            title = (row.get("title") or "").strip()
            if not LISTING_RE.search(href):
                continue
            if not _card_passes_intern_india(card):
                continue
            if href not in urls:
                urls.append(href)
                kept += 1
            if title:
                titles[href] = title
        warnings.append(f"BofA facet {url}: {kept} India+intern/student card(s) on page")
        if kept == 0 and page_idx > 0:
            break
    return urls, titles, warnings


class BankOfAmericaOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "bofa_official"
    official_hosts = frozenset({"careers.bankofamerica.com"})
    discovery_search_urls = SEARCH_URLS

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes=(
                "BofA intern/student facets with paginated search; India via official result-card "
                "location text and/or detail-page verification (not /job-search/india slug alone)."
            ),
            inventory_complete=False,
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Bank of America extraction")

        warnings: list[str] = []
        merged: list[str] = []
        titles: dict[str, str] = {}
        facet_by_url: dict[str, str] = {}

        for facet in SEARCH_URLS:
            batch, tmap, facet_warnings = await _harvest_bofa_search_pages(ctx.page, facet)
            warnings.extend(facet_warnings)
            for u in batch:
                key = u.split("?")[0].rstrip("/")
                facet_by_url.setdefault(key, facet)
                if u not in merged:
                    merged.append(u)
            titles.update(tmap)

        warnings.insert(0, f"BofA: {len(merged)} unique listing URL(s) with India+intern/student card evidence")

        if not merged:
            warnings.append(
                "BofA: no intern/student listings with India shown on official search cards "
                "(empty scan is not proof that no India internships exist)"
            )
            return await facet_harvest_to_jobs(
                ctx,
                [],
                self.official_hosts,
                titles,
                self.adapter_key,
                warnings,
                allow_empty_harvest=True,
            )

        slug_india = [u for u in merged if _bofa_slug_indicates_india(u)]
        verify_candidates = [u for u in merged if u not in slug_india]
        cap = settings.discovery_bofa_detail_verify_max_jobs
        if len(verify_candidates) > cap:
            warnings.append(
                f"BofA: detail verification capped at {cap} of {len(verify_candidates)} non-slug candidate(s)"
            )
        detail_india: list[str] = []
        for url in verify_candidates[:cap]:
            try:
                facts = await extract_location_from_detail_page(ctx.page, url, self.adapter_key)
                if _facts_india_eligible(facts):
                    detail_india.append(url)
                    warnings.append(f"BofA: detail-page India evidence for {url.split('/')[-1][:48]}")
            except Exception as e:
                warnings.append(f"BofA: detail verify failed for {url}: {type(e).__name__}")

        india_urls = list(dict.fromkeys(slug_india + detail_india))
        if len(india_urls) < len(merged):
            warnings.append(
                f"BofA: kept {len(india_urls)} listing(s) after slug/detail proof; "
                f"excluded {len(merged) - len(india_urls)} without corroborating India evidence"
            )
        if not india_urls:
            warnings.append("BofA: card harvest matched but slug/detail India proof failed")
            return await facet_harvest_to_jobs(
                ctx,
                [],
                self.official_hosts,
                titles,
                self.adapter_key,
                warnings,
                allow_empty_harvest=True,
            )

        india_facets: dict[str, str] = {}
        for u in india_urls:
            key = u.split("?")[0].rstrip("/")
            india_facets[key] = facet_by_url.get(key, SEARCH_URLS[0])
        return await facet_harvest_to_jobs(
            ctx,
            india_urls,
            self.official_hosts,
            titles,
            self.adapter_key,
            warnings,
            facet_by_url=india_facets,
            allow_empty_harvest=True,
        )

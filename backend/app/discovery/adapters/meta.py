import re

from app.config import settings
from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs, harvest_search_facets
from app.discovery.context import ScanContext
from app.discovery.location_extract import (
    _title_from_detail_page,
    extract_location_from_detail_page,
)
from app.discovery.types import AdapterResult, InspectionReport

LISTING_RE = re.compile(
    r"^https://www\.metacareers\.com/(?:profile/job_details|jobs)/\d+",
    re.I,
)
# India office + intern facets often show "0 Items" while global intern search has hundreds.
OFFICE_INTERN_FACETS = (
    "https://www.metacareers.com/jobsearch?q=intern&offices[0]=Gurgaon",
    "https://www.metacareers.com/jobsearch?q=intern&offices[0]=Bangalore",
    "https://www.metacareers.com/jobsearch?q=intern&offices[0]=Hyderabad",
)
SUPPLEMENTAL_FACETS = (
    "https://www.metacareers.com/careerprograms/students",
    "https://www.metacareers.com/jobsearch?q=intern",
)

_INTERN_TITLE = re.compile(
    r"\b(intern|internship|co-?op|student|university|graduate|phd\s+fellow)\b",
    re.I,
)


def _facts_india_eligible(facts) -> bool:
    if facts.india_eligible is True:
        return True
    if "India" in (facts.countries or []):
        return True
    loc = (facts.normalized_location or "").lower()
    return bool(re.search(r"\bindia\b", loc))


def _title_suggests_intern(title: str) -> bool:
    return bool(_INTERN_TITLE.search(title or ""))


class MetaOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "meta_official"
    official_hosts = frozenset({"www.metacareers.com", "metacareers.com"})
    discovery_search_urls = (*OFFICE_INTERN_FACETS, *SUPPLEMENTAL_FACETS)

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes=(
                "Meta: office intern facets + students + global intern harvest; "
                "India internship kept via official detail-page location/title evidence."
            ),
            inventory_complete=False,
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Meta extraction")

        warnings: list[str] = []
        merged: list[str] = []
        titles: dict[str, str] = {}
        facet_by_url: dict[str, str] = {}

        office_urls, office_titles, office_warn, office_facets = await harvest_search_facets(
            ctx.page,
            OFFICE_INTERN_FACETS,
            LISTING_RE,
            scroll_rounds=12,
            page_load_ms=7000,
        )
        warnings.extend(office_warn)
        if not office_urls and any("0 listing" in w or "harvested 0" in w.lower() for w in office_warn):
            warnings.append(
                "Meta: India office intern facets returned no listings in official UI (0 Items); "
                "this does not prove Meta has no India internships globally"
            )

        sup_urls, sup_titles, sup_warn, sup_facets = await harvest_search_facets(
            ctx.page,
            SUPPLEMENTAL_FACETS,
            LISTING_RE,
            scroll_rounds=28,
            page_load_ms=7000,
        )
        warnings.extend(sup_warn)

        for batch, tmap, fmap in (
            (office_urls, office_titles, office_facets),
            (sup_urls, sup_titles, sup_facets),
        ):
            for u in batch:
                key = u.split("?")[0].rstrip("/")
                if u not in merged:
                    merged.append(u)
                facet_by_url.setdefault(key, fmap.get(key, ""))
            titles.update(tmap)

        if not merged:
            warnings.append(
                "Meta: no official job_details URLs harvested; empty scan is not proof of zero open internships"
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

        verify_cap = settings.discovery_meta_detail_verify_max_jobs
        candidates = list(dict.fromkeys(merged))
        if len(candidates) > verify_cap:
            warnings.append(
                f"Meta: detail verification capped at {verify_cap} of {len(candidates)} harvested URL(s)"
            )

        india_intern_urls: list[str] = []
        for url in candidates[:verify_cap]:
            try:
                facts = await extract_location_from_detail_page(ctx.page, url, self.adapter_key)
            except Exception as e:
                warnings.append(f"Meta: detail verify failed for {url}: {type(e).__name__}")
                continue
            if not _facts_india_eligible(facts):
                continue
            title = await _title_from_detail_page(ctx.page) or titles.get(url, "")
            if not _title_suggests_intern(title):
                warnings.append(f"Meta: skipped India listing without intern/student title signal: {title[:60]}")
                continue
            india_intern_urls.append(url.split("?")[0].rstrip("/") + "/")

        if not india_intern_urls:
            warnings.append(
                f"Meta: harvested {len(candidates)} URL(s) but none passed India + intern/student detail checks"
            )

        return await facet_harvest_to_jobs(
            ctx,
            india_intern_urls,
            self.official_hosts,
            titles,
            self.adapter_key,
            warnings,
            facet_by_url=facet_by_url,
            allow_empty_harvest=True,
        )

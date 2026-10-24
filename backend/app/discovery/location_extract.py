"""Extract structured location facts from official job detail pages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.discovery.india_location import location_from_listing_url
from app.discovery.normalize import content_hash
from app.discovery.types import NormalizedJob

COUNTRY_ALIASES: dict[str, str] = {
    "india": "India",
    "united states": "United States",
    "usa": "United States",
    "us": "United States",
    "u.s.": "United States",
    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "canada": "Canada",
    "ireland": "Ireland",
    "singapore": "Singapore",
    "australia": "Australia",
    "germany": "Germany",
    "japan": "Japan",
}

WORK_MODE_REMOTE = re.compile(r"\bremote\b", re.I)
WORK_MODE_HYBRID = re.compile(r"\bhybrid\b", re.I)
US_ONLY = re.compile(
    r"\b(us[- ]only|united states only|must be (?:legally )?authorized to work in the (?:u\.?s\.?|united states))\b",
    re.I,
)
INDIA_REMOTE = re.compile(r"\bremote\b.*\bindia\b|\bindia\b.*\bremote\b", re.I)
GLOBAL_REMOTE = re.compile(r"\b(?:worldwide|anywhere|global)\b.*\bremote\b|\bremote\b.*\b(?:worldwide|anywhere|global)\b", re.I)


@dataclass
class LocationFacts:
    normalized_location: str | None = None
    countries: list[str] = field(default_factory=list)
    work_mode: str | None = None  # remote | onsite | hybrid
    india_eligible: bool | None = None
    evidence: str = ""
    source: str = ""
    india_site_locations: list[str] = field(default_factory=list)

    def to_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "normalized_location": self.normalized_location,
            "countries": self.countries,
            "work_mode": self.work_mode,
            "india_eligible": self.india_eligible,
            "evidence": self.evidence,
            "source": self.source,
        }
        if self.india_site_locations:
            meta["india_site_locations"] = self.india_site_locations
        return meta


def _normalize_countries(raw: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        key = item.strip().lower()
        label = COUNTRY_ALIASES.get(key, item.strip())
        if not label:
            continue
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out


def _countries_from_location_string(loc: str) -> list[str]:
    found: list[str] = []
    lower = loc.lower()
    for key, label in COUNTRY_ALIASES.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            found.append(label)
    if re.search(r"\bindia\b", lower):
        found.append("India")
    if re.search(r",\s*in\s*$", lower) or re.search(r"\bIN,\s", loc):
        found.append("India")
    if re.search(r"\b(us|usa|u\.s\.)\b", lower) or re.search(r",\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\s*$", loc):
        found.append("United States")
    return _normalize_countries(found)


def _parse_json_ld_job_locations(payload: Any) -> list[str]:
    locations: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            locations.extend(_parse_json_ld_job_locations(item))
        return locations
    if not isinstance(payload, dict):
        return locations
    if payload.get("@type") == "JobPosting" or "jobLocation" in payload:
        jl = payload.get("jobLocation")
        if isinstance(jl, list):
            for entry in jl:
                locations.extend(_extract_place(entry))
        elif jl:
            locations.extend(_extract_place(jl))
    if "@graph" in payload:
        locations.extend(_parse_json_ld_job_locations(payload["@graph"]))
    return locations


def _stringify_address_part(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("name", "addressCountry", "addressLocality", "addressRegion"):
            if value.get(key):
                return str(value[key]).strip()
    return str(value).strip() or None


def _extract_place(entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return []
    if entry.get("@type") == "Place":
        addr = entry.get("address")
        if isinstance(addr, dict):
            parts = [
                _stringify_address_part(addr.get("addressLocality")),
                _stringify_address_part(addr.get("addressRegion")),
                _stringify_address_part(addr.get("addressCountry")),
            ]
            text = ", ".join(p for p in parts if p)
            return [text] if text else []
        if entry.get("name"):
            return [str(entry["name"])]
    if entry.get("name"):
        return [str(entry["name"])]
    return []


async def _json_ld_locations(page) -> list[str]:
    raw_scripts = await page.eval_on_selector_all(
        'script[type="application/ld+json"]',
        "els => els.map(e => e.textContent || '')",
    )
    locations: list[str] = []
    for text in raw_scripts:
        text = (text or "").strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        locations.extend(_parse_json_ld_job_locations(data))
    return locations


def _line_after_label(text: str, labels: tuple[str, ...]) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        for label in labels:
            if stripped.lower().startswith(label.lower()):
                rest = stripped[len(label) :].strip(" :|-")
                if rest and len(rest) < 120:
                    return rest
    return None


def _looks_like_job_title_not_location(text: str) -> bool:
    lower = text.lower()
    if re.search(r"\bsummer\s+20\d{2}\b", lower) and not re.search(
        r"\b(india|karnataka|telangana|bengaluru|bangalore|hyderabad)\b", lower
    ):
        return True
    if re.search(r"\bphd\b", lower) and re.search(r"\bintern\b", lower):
        if not re.search(r"\b(india|karnataka|telangana|bengaluru|bangalore|hyderabad)\b", lower):
            return True
    return False


def _pick_primary_india_site(sites: list[str]) -> str:
    if not sites:
        return ""
    for pref in ("bengaluru", "bangalore", "hyderabad"):
        for site in sites:
            if pref in site.lower():
                return site
    return sites[0]


def _google_india_locations_from_body(body: str) -> list[str]:
    """Parse official Google careers detail pages (multi-location internships)."""
    found: list[str] = []
    for line in body.splitlines():
        candidate = line.strip().lstrip(";").strip()
        if not candidate or len(candidate) > 90:
            continue
        if not re.search(r",\s*India\s*$", candidate, re.I):
            continue
        if not re.search(
            r"\b(bengaluru|bangalore|hyderabad|mumbai|gurugram|gurgaon|pune|chennai|delhi|noida|karnataka|telangana)\b",
            candidate,
            re.I,
        ):
            continue
        if _looks_like_job_title_not_location(candidate):
            continue
        found.append(candidate)
    return list(dict.fromkeys(found))


def _sanitize_location_candidate(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip().split("\n")[0].strip()
    if len(cleaned) > 120:
        return None
    lower = cleaned.lower()
    if lower.startswith("this role") or lower.startswith("to help our teams"):
        return None
    if lower in ("see full role description", "read more", "apply now"):
        return None
    if _looks_like_job_title_not_location(cleaned):
        return None
    if re.search(r"\b(intern|internship|engineer|analyst|scientist|phd)\b", lower) and "," not in cleaned:
        if not re.search(
            r"\b(india|bengaluru|bangalore|hyderabad|mumbai|gurugram|gurgaon|delhi|pune|chennai)\b",
            lower,
        ):
            return None
    return cleaned


def _infer_work_mode(location: str | None, extra: str) -> str | None:
    blob = f"{location or ''} {extra}"
    if WORK_MODE_HYBRID.search(blob):
        return "hybrid"
    if WORK_MODE_REMOTE.search(blob):
        return "remote"
    if location:
        return "onsite"
    return None


def _infer_india_eligible(
    countries: list[str],
    location: str | None,
    work_mode: str | None,
    evidence_blob: str,
) -> bool | None:
    if US_ONLY.search(evidence_blob) and "India" not in countries and not (
        location and re.search(r"\bindia\b", location, re.I)
    ):
        return False
    if "India" in countries:
        return True
    if location and re.search(r"\bindia\b", location, re.I):
        return True
    if INDIA_REMOTE.search(evidence_blob):
        return True
    if work_mode == "remote" and GLOBAL_REMOTE.search(evidence_blob):
        return True
    if countries and "India" not in countries and all(c != "India" for c in countries):
        if work_mode != "remote":
            return False
    return None


def _location_fact_quality(f: LocationFacts) -> int:
    loc = f.normalized_location or ""
    if not loc or _looks_like_job_title_not_location(loc):
        return 0
    score = 1
    if "India" in f.countries or re.search(r"\bindia\b", loc, re.I):
        score += 3
    if re.search(r"\b(bengaluru|bangalore|hyderabad|mumbai|gurugram)\b", loc, re.I):
        score += 2
    if f.source == "google_official_body":
        score += 2
    return score


def merge_location_facts(*facts: LocationFacts) -> LocationFacts:
    merged = LocationFacts()
    best_loc: str | None = None
    best_score = -1
    for f in facts:
        if f.normalized_location:
            q = _location_fact_quality(f)
            if q > best_score:
                best_score = q
                best_loc = f.normalized_location
        for c in f.countries:
            if c not in merged.countries:
                merged.countries.append(c)
        if f.work_mode and not merged.work_mode:
            merged.work_mode = f.work_mode
        if f.india_eligible is not None and merged.india_eligible is None:
            merged.india_eligible = f.india_eligible
        if f.evidence and not merged.evidence:
            merged.evidence = f.evidence
        if f.source and not merged.source:
            merged.source = f.source
        for site in f.india_site_locations:
            if site not in merged.india_site_locations:
                merged.india_site_locations.append(site)
    if best_loc:
        merged.normalized_location = best_loc
    if merged.india_site_locations and not merged.countries:
        merged.countries = ["India"]
    if merged.india_site_locations and (
        not merged.normalized_location
        or _looks_like_job_title_not_location(merged.normalized_location)
    ):
        merged.normalized_location = _pick_primary_india_site(merged.india_site_locations)
    if merged.normalized_location and not merged.countries:
        merged.countries = _countries_from_location_string(merged.normalized_location)
    blob = f"{merged.normalized_location or ''} {' '.join(merged.countries)} {merged.evidence}"
    if merged.india_eligible is None:
        merged.india_eligible = _infer_india_eligible(
            merged.countries, merged.normalized_location, merged.work_mode, blob
        )
    if merged.work_mode is None:
        merged.work_mode = _infer_work_mode(merged.normalized_location, merged.evidence)
    return merged


SITE_SELECTORS: dict[str, list[str]] = {
    "stripe_official": [
        "[data-testid='job-location']",
        "[class*='JobLocation']",
        "li:has-text('Location')",
    ],
    "google_official": [
        "[data-job-location]",
    ],
    "microsoft_official": [
        "[data-ph-at-id*='location']",
        "[class*='location']",
    ],
    "meta_official": [
        "[data-testid='job-location']",
        "div:has-text('Location')",
    ],
    "amazon_official": [
        "#job-detail-location",
        ".location-and-id",
        "[class*='job-location']",
    ],
    "apple_official": [
        ".job-location",
        "[data-test-id='job-location']",
    ],
    "atlassian_official": [
        "[data-testid='job-location']",
        "p:has-text('Location')",
    ],
    "jpmorgan_official": [
        "[data-automation-id='jobLocation']",
        "[class*='job-location']",
        "span:has-text('Location')",
    ],
    "goldman_official": [
        "[data-testid='job-location']",
        "[class*='location']",
    ],
    "bofa_official": [
        "[class*='job-location']",
        "span:has-text('Location')",
    ],
    "morgan_stanley_official": [
        "[data-testid='job-location']",
        "[class*='location']",
    ],
}


async def _dom_location_hints(page, adapter_key: str) -> LocationFacts:
    facts = LocationFacts(source="detail_page_dom")
    selectors = SITE_SELECTORS.get(adapter_key, [])
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count():
                text = (await loc.inner_text()).strip()
                candidate = _sanitize_location_candidate(text)
                if candidate:
                    facts.normalized_location = candidate
                    facts.evidence = f"selector:{sel}={facts.normalized_location}"
                    facts.countries = _countries_from_location_string(facts.normalized_location)
                    return facts
        except Exception:
            continue

    body = (await page.inner_text("body"))[:12_000]
    for label in ("Location:", "Job location:", "Locations:", "Office location:"):
        line = _line_after_label(body, (label,))
        line = _sanitize_location_candidate(line)
        if line:
            facts.normalized_location = line
            facts.evidence = f"label:{label} {line}"
            facts.countries = _countries_from_location_string(line)
            return facts
    return facts


def _employment_hint_from_body(body: str) -> str | None:
    import re

    m = re.search(r"employment type\s*[:\s]*(full[- ]?time|internship|part[- ]?time)", body[:8000], re.I)
    if not m:
        return None
    val = m.group(1).lower()
    if "intern" in val:
        return "internship"
    if "full" in val:
        return "full_time"
    return None


async def extract_location_from_current_page(page, listing_url: str, adapter_key: str) -> LocationFacts:
    url_loc = location_from_listing_url(listing_url)
    url_facts = LocationFacts(
        normalized_location=url_loc,
        countries=_countries_from_location_string(url_loc or ""),
        evidence=f"listing_url_query location={url_loc}" if url_loc else "",
        source="listing_url_query" if url_loc else "",
    )

    ld_locs = await _json_ld_locations(page)
    ld_facts = LocationFacts(source="detail_page_json_ld")
    if ld_locs:
        first = _sanitize_location_candidate(ld_locs[0])
        if first and not first.startswith("{"):
            ld_facts.normalized_location = first
            ld_facts.evidence = f"json_ld jobLocation={first}"
        ld_facts.countries = _normalize_countries(
            [c for loc in ld_locs for c in _countries_from_location_string(loc)]
        )

    dom_facts = await _dom_location_hints(page, adapter_key)
    body_snippet = (await page.inner_text("body"))[:10_000]
    emp_hint = _employment_hint_from_body(body_snippet)

    google_facts = LocationFacts()
    if adapter_key == "google_official":
        india_sites = _google_india_locations_from_body(body_snippet)
        if india_sites:
            primary = _pick_primary_india_site(india_sites)
            google_facts = LocationFacts(
                normalized_location=primary,
                countries=["India"],
                evidence=f"google_official_body_locations={india_sites!r}",
                source="google_official_body",
                india_site_locations=india_sites,
            )

    merged = merge_location_facts(url_facts, ld_facts, dom_facts, google_facts)
    if emp_hint:
        merged.evidence = f"{merged.evidence}; employment_type={emp_hint}".strip("; ")
    if not merged.source:
        merged.source = "detail_page_dom"
    blob = f"{merged.normalized_location or ''} {merged.evidence}"
    merged.work_mode = _infer_work_mode(merged.normalized_location, blob)
    merged.india_eligible = _infer_india_eligible(
        merged.countries, merged.normalized_location, merged.work_mode, blob
    )
    return merged


async def extract_location_from_detail_page(page, listing_url: str, adapter_key: str) -> LocationFacts:
    await page.goto(listing_url, wait_until="domcontentloaded", timeout=120_000)
    wait_ms = (
        3500
        if adapter_key in ("jpmorgan_official", "goldman_official", "bofa_official", "google_official")
        else 1200
    )
    await page.wait_for_timeout(wait_ms)
    return await extract_location_from_current_page(page, listing_url, adapter_key)


async def _title_from_detail_page(page) -> str | None:
    og = page.locator("meta[property='og:title']")
    if await og.count():
        raw = (await og.first.get_attribute("content")) or ""
        title = raw.split(" - ")[0].strip()
        if title and len(title) > 3:
            return title
    headings = page.locator("h1")
    n = await headings.count()
    best = ""
    for i in range(min(n, 8)):
        text = (await headings.nth(i).inner_text()).strip().split("\n")[0].strip()
        if len(text) > len(best) and text.lower() not in ("404", "see full role description", "careers"):
            best = text
    return best or None


async def _maybe_refresh_title(page, job: NormalizedJob) -> None:
    import re

    weak = job.title.lower() in (
        "see full role description",
        "...read more",
        "read more",
        "apply",
    ) or len(job.title) < 4 or bool(re.match(r"^Role\s+\d+$", (job.title or "").strip(), re.I))
    if not weak:
        return
    title = await _title_from_detail_page(page)
    if title and len(title) > 3:
        job.title = title
        desc = job.description_sections if isinstance(job.description_sections, dict) else {}
        body = str(desc.get("summary", ""))
        if body.startswith("Role ") or body == job.title:
            job.description_sections = {**desc, "summary": job.title}


async def enrich_jobs_with_detail_locations(
    page,
    jobs: list[NormalizedJob],
    adapter_key: str,
    *,
    max_jobs: int | None = None,
) -> list[str]:
    """Visit each listing URL and attach location + location_meta. Returns warnings."""
    warnings: list[str] = []
    limit = max_jobs if max_jobs is not None else len(jobs)
    if limit < len(jobs):
        warnings.append(
            f"Detail enrichment capped at {limit} of {len(jobs)} listings (discovery_detail_enrich_max_jobs)"
        )
    for job in jobs[:limit]:
        try:
            facts = await extract_location_from_detail_page(page, job.listing_url, adapter_key)
            await _maybe_refresh_title(page, job)
            if facts.normalized_location:
                job.location = facts.normalized_location
            meta = facts.to_meta()
            if "employment_type=internship" in facts.evidence:
                meta["employment_type_hint"] = "internship"
            elif "employment_type=full_time" in facts.evidence:
                meta["employment_type_hint"] = "full_time"
            prior = job.location_meta if isinstance(job.location_meta, dict) else {}
            merged = {**prior, **meta}
            if prior.get("india_eligible") is True and meta.get("india_eligible") is not False:
                merged["india_eligible"] = True
            if prior.get("discovery_facet_india_hint"):
                merged["discovery_facet_india_hint"] = True
            if prior.get("employment_type_hint") and not meta.get("employment_type_hint"):
                merged["employment_type_hint"] = prior["employment_type_hint"]
            if prior.get("discovery_facet_url"):
                merged["discovery_facet_url"] = prior["discovery_facet_url"]
            if prior.get("evidence") and meta.get("evidence"):
                merged["evidence"] = f"{prior['evidence']}; {meta['evidence']}"
            elif prior.get("evidence") and not merged.get("evidence"):
                merged["evidence"] = prior["evidence"]
            job.location_meta = merged
            if facts.work_mode == "remote":
                job.remote_flag = True
            elif facts.work_mode in ("onsite", "hybrid"):
                job.remote_flag = False
            job.content_hash = content_hash(job.title, job.location, job.description_sections)
        except Exception as e:
            warnings.append(f"Location enrich failed for {job.listing_url}: {e}")
    return warnings

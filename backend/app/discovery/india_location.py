"""Classify official listings for India-first discovery."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.discovery.types import NormalizedJob
from app.models.job import Job

INDIA_SCOPE_VALUES = (
    "india_based",
    "remote_india",
    "remote_global_india_ok",
    "outside_india",
    "unknown",
)

VERIFIED_INDIA_SCOPES = (
    "india_based",
    "remote_india",
    "remote_global_india_ok",
)


class IndiaScope(str, Enum):
    india_based = "india_based"
    remote_india = "remote_india"
    remote_global_india_ok = "remote_global_india_ok"
    outside_india = "outside_india"
    unknown = "unknown"


INDIA_CITY_ALIASES: dict[str, str] = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "mumbai": "Mumbai",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "chennai": "Chennai",
    "noida": "Noida",
    "new delhi": "New Delhi",
    "delhi": "New Delhi",
    "kolkata": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "bhopal": "Bhopal",
    "kochi": "Kochi",
}

OUTSIDE_INDIA_MARKERS = (
    r"\bus[- ]only\b",
    r"\bunited states only\b",
    r"\bmust be (?:legally )?authorized to work in the (?:u\.?s\.?|united states)\b",
)

# Explicit non-India locations — used before weak facet hints.
OUTSIDE_LOCATION_RE = re.compile(
    r"\b("
    r"riyadh|jeddah|dammam|saudi arabia|"
    r"dubai|abu dhabi|united arab emirates|\buae\b|"
    r"singapore|hong kong|tokyo|seoul|"
    r"seattle|san francisco|menlo park|sunnyvale|mountain view|"
    r"new york|austin|boston|chicago|los angeles|"
    r"toronto|vancouver|london|dublin|berlin|paris|zurich|sydney|"
    r"united states|\bu\.?s\.?a?\.?\b|"
    r"united kingdom|\buk\b|canada|germany|australia|china|japan"
    r")\b",
    re.I,
)

INDIA_REMOTE_MARKERS = (
    r"\bremote.*\bindia\b",
    r"\bindia\b.*\bremote\b",
    r"\bwork from home.*\bindia\b",
)

GLOBAL_REMOTE_INDIA_OK = (
    r"\bremote\b.*\b(?:worldwide|anywhere|global)\b",
    r"\b(?:worldwide|anywhere).*\bremote\b",
)


def location_from_listing_url(url: str) -> str | None:
    q = parse_qs(urlparse(url).query)
    loc = q.get("location", [None])[0]
    return loc.replace("+", " ") if loc else None


def _meta(job: NormalizedJob | Job) -> dict[str, Any]:
    raw = getattr(job, "location_meta", None)
    return raw if isinstance(raw, dict) else {}


def _structured_blob(job: NormalizedJob | Job) -> str:
    """Evidence used for classification — excludes full job descriptions."""
    url_loc = location_from_listing_url(getattr(job, "listing_url", "") or "")
    meta = _meta(job)
    parts = [
        job.title or "",
        job.location or "",
        url_loc or "",
        meta.get("normalized_location") or "",
        meta.get("evidence") or "",
        " ".join(meta.get("countries") or []),
        meta.get("work_mode") or "",
    ]
    return " ".join(str(p) for p in parts if p).lower()


def _has_india_city(text: str) -> str | None:
    for key, label in INDIA_CITY_ALIASES.items():
        if re.search(rf"\b{re.escape(key)}\b", text, re.I):
            return label
    return None


def location_indicates_outside_india(location: str | None) -> bool:
    if not location or len(location) > 120:
        return False
    if _has_india_city(location):
        return False
    if re.search(r"\bindia\b", location, re.I):
        return False
    return bool(OUTSIDE_LOCATION_RE.search(location))


def extract_location_hint(text: str) -> str | None:
    city = _has_india_city(text)
    if city:
        return city
    if re.search(r"\bindia\b", text, re.I):
        return "India"
    if re.search(r"\bremote\b.*\bindia\b|\bindia\b.*\bremote\b", text, re.I):
        return "Remote (India)"
    return None


def _explicit_outside_from_evidence(
    job: NormalizedJob | Job,
    loc: str,
    countries: list[str],
    text: str,
) -> bool:
    if _meta(job).get("india_eligible") is False:
        return True
    if countries and all(c != "India" for c in countries):
        return True
    if location_indicates_outside_india(loc):
        return True
    if location_indicates_outside_india(_meta(job).get("normalized_location")):
        return True
    for pattern in OUTSIDE_INDIA_MARKERS:
        if re.search(pattern, text, re.I):
            if "india" not in countries and not _has_india_city(text):
                return True
    url_loc = location_from_listing_url(getattr(job, "listing_url", "") or "")
    if url_loc and re.search(r"\b(united states|usa|u\.s\.)\b", url_loc, re.I):
        return True
    return False


def classify_india_scope(job: NormalizedJob | Job) -> tuple[IndiaScope, str | None]:
    meta = _meta(job)
    loc = (job.location or meta.get("normalized_location") or "").strip()
    url_loc = location_from_listing_url(getattr(job, "listing_url", "") or "")
    text = _structured_blob(job)
    countries = [str(c) for c in (meta.get("countries") or [])]
    work_mode = meta.get("work_mode")
    india_eligible = meta.get("india_eligible")

    if _explicit_outside_from_evidence(job, loc, countries, text):
        if url_loc and re.search(r"\b(united states|usa|u\.s\.)\b", url_loc, re.I):
            return IndiaScope.outside_india, url_loc
        return IndiaScope.outside_india, loc or (countries[0] if countries else None)

    if url_loc and re.search(r"\bindia\b", url_loc, re.I):
        city = _has_india_city(url_loc)
        if city:
            return IndiaScope.india_based, city
        return IndiaScope.india_based, url_loc

    site_locs = meta.get("india_site_locations")
    if isinstance(site_locs, list) and site_locs:
        primary = str(site_locs[0])
        city = _has_india_city(primary) or _has_india_city(" ".join(str(s) for s in site_locs))
        if city:
            return IndiaScope.india_based, city
        if any(re.search(r"\bindia\b", str(s), re.I) for s in site_locs):
            return IndiaScope.india_based, primary

    if "India" in countries:
        if work_mode == "remote" or re.search(r"\bremote\b", loc, re.I):
            for pat in INDIA_REMOTE_MARKERS:
                if re.search(pat, text, re.I) or re.search(pat, loc, re.I):
                    return IndiaScope.remote_india, loc or "Remote (India)"
            if work_mode == "remote":
                return IndiaScope.remote_india, loc or "Remote (India)"
        city = _has_india_city(loc) or _has_india_city(text)
        if city:
            return IndiaScope.india_based, city
        return IndiaScope.india_based, loc or "India"

    city = _has_india_city(loc) or _has_india_city(text)
    if city:
        return IndiaScope.india_based, city

    if re.search(r"\bindia\b", loc, re.I):
        if job.remote_flag or work_mode == "remote" or re.search(r"\bremote\b", loc, re.I):
            return IndiaScope.remote_india, loc or "Remote (India)"
        return IndiaScope.india_based, loc

    if job.remote_flag or work_mode == "remote" or re.search(r"\bremote\b", loc, re.I):
        for pat in INDIA_REMOTE_MARKERS:
            if re.search(pat, text, re.I) or re.search(pat, loc, re.I):
                return IndiaScope.remote_india, loc or "Remote (India)"
        for pat in GLOBAL_REMOTE_INDIA_OK:
            if re.search(pat, text, re.I):
                return IndiaScope.remote_global_india_ok, loc or "Remote (global)"

    if india_eligible is True:
        if work_mode == "remote":
            for pat in INDIA_REMOTE_MARKERS:
                if re.search(pat, text, re.I) or re.search(pat, loc, re.I):
                    return IndiaScope.remote_india, loc or "Remote (India)"
            return IndiaScope.unknown, loc or None
        city = _has_india_city(loc) or _has_india_city(text)
        if city or re.search(r"\bindia\b", loc, re.I):
            return IndiaScope.india_based, loc or city or "India"
        return IndiaScope.unknown, loc or None

    if loc and len(loc) < 80:
        us_markers = re.search(
            r"\b(seattle|san francisco|austin|new york|menlo park|sunnyvale|toronto|london|dublin|berlin|zurich|sydney)\b",
            loc,
            re.I,
        )
        if us_markers and not _has_india_city(loc):
            return IndiaScope.outside_india, loc

    if loc and len(loc) < 80:
        return IndiaScope.unknown, loc

    return IndiaScope.unknown, None


def india_scope_in_default_results(scope: IndiaScope | str) -> bool:
    s = scope.value if isinstance(scope, IndiaScope) else scope
    return s in VERIFIED_INDIA_SCOPES


def classify_career_level(title: str) -> str | None:
    t = title.lower()
    if re.search(r"\bintern(ship)?\b", t):
        return "Internship"
    if re.search(r"\b(new grad|university grad|graduate|entry[- ]level|early career)\b", t):
        return "Entry level"
    if re.search(r"\b(senior|staff|principal|director|vp |vice president|lead manager)\b", t):
        return "Senior+"
    return None


def display_location_label(scope: IndiaScope | str, location: str | None) -> str:
    s = scope.value if isinstance(scope, IndiaScope) else scope
    if s == IndiaScope.india_based.value:
        return location or "India"
    if s == IndiaScope.remote_india.value:
        return "Remote · India"
    if s == IndiaScope.remote_global_india_ok.value:
        return "Remote · India eligible"
    if s == IndiaScope.outside_india.value:
        return location or "Outside India"
    return "Location unknown"

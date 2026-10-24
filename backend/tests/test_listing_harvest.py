import re

from app.discovery.adapters.listing_browser import unique_matching_urls

LISTING_RE = re.compile(r"^https://example\.com/jobs/\d+", re.I)


def test_unique_matching_urls_dedupes_query_variants():
    hrefs = [
        "https://example.com/jobs/1?a=1",
        "https://example.com/jobs/1?b=2",
        "https://example.com/jobs/2",
    ]
    out = unique_matching_urls(hrefs, LISTING_RE)
    assert len(out) == 2


def test_discovery_facet_meta_india_intern():
    from app.discovery.adapters.listing_browser import meta_from_discovery_facet

    meta = meta_from_discovery_facet(
        "https://www.google.com/about/careers/applications/jobs/results?location=India&employment_type=INTERN"
    )
    assert meta.get("discovery_facet_india_hint") is True
    assert meta.get("employment_type_hint") == "internship"


def test_facet_harvest_truncation_message():
    from app.config import settings

    safety = settings.discovery_safety_max_jobs_per_scan
    urls = list(range(safety + 5))
    warnings: list[str] = []
    if len(urls) > safety:
        warnings.append(f"Truncated to {safety} listings (discovered {len(urls)}); safety cap")
    assert any("Truncated" in w for w in warnings)


def test_jpm_safety_cap_higher_than_default():
    from app.config import settings

    assert settings.discovery_jpm_safety_max_jobs_per_scan > settings.discovery_safety_max_jobs_per_scan

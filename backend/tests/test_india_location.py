import uuid
from datetime import UTC, datetime

from app.discovery.india_location import (
    IndiaScope,
    classify_india_scope,
    india_scope_in_default_results,
    location_from_listing_url,
    location_indicates_outside_india,
)
from app.models.job import Job


def _job(
    title: str,
    location: str | None = None,
    listing_url: str = "https://example.com/j/1",
    location_meta: dict | None = None,
) -> Job:
    return Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key="k",
        title=title,
        location=location,
        remote_flag=None,
        description_sections={},
        listing_url=listing_url,
        apply_url=listing_url,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
        location_meta=location_meta,
    )


def test_bengaluru_alias():
    scope, label = classify_india_scope(_job("Software Engineer Intern", "Bangalore, India"))
    assert scope == IndiaScope.india_based
    assert label == "Bengaluru"
    assert india_scope_in_default_results(scope)


def test_riyadh_excluded_even_with_facet_hint():
    job = _job(
        "Software Development Engineer Internship",
        "Riyadh, Saudi Arabia",
        listing_url="https://www.amazon.jobs/en/jobs/123?offset=0",
        location_meta={
            "discovery_facet_india_hint": True,
            "discovery_facet_url": "https://www.amazon.jobs/en/search?loc_query=India",
            "countries": ["Saudi Arabia"],
            "india_eligible": False,
        },
    )
    scope, _ = classify_india_scope(job)
    assert scope == IndiaScope.outside_india
    assert not india_scope_in_default_results(scope)


def test_us_only_excluded():
    scope, _ = classify_india_scope(_job("New Grad Engineer", "San Francisco, CA — US only"))
    assert scope == IndiaScope.outside_india
    assert not india_scope_in_default_results(scope)


def test_unknown_location_excluded_by_default():
    scope, _ = classify_india_scope(_job("Software Engineer Intern", None))
    assert scope == IndiaScope.unknown
    assert not india_scope_in_default_results(scope)


def test_remote_india_included():
    scope, _ = classify_india_scope(_job("Backend Intern", "Remote - India"))
    assert scope == IndiaScope.remote_india
    assert india_scope_in_default_results(scope)


def test_remote_from_india_explicit():
    job = _job(
        "Engineering Intern",
        "Remote (India)",
        location_meta={
            "countries": ["India"],
            "work_mode": "remote",
            "normalized_location": "Remote - India",
            "india_eligible": True,
            "evidence": "detail_page",
        },
    )
    scope, _ = classify_india_scope(job)
    assert scope in (IndiaScope.remote_india, IndiaScope.india_based)
    assert india_scope_in_default_results(scope)


def test_google_url_location_param():
    url = "https://www.google.com/about/careers/applications/jobs/results/1-engineer?location=India"
    assert location_from_listing_url(url) == "India"
    scope, _ = classify_india_scope(_job("Engineer", None, listing_url=url))
    assert scope == IndiaScope.india_based


def test_located_in_seattle_not_india():
    job = _job("Data Engineer, 2027 Graduate U.S.", "Seattle, WA")
    job.location_meta = {
        "countries": ["United States"],
        "work_mode": "onsite",
        "india_eligible": False,
        "evidence": "json_ld jobLocation=Seattle, WA, US",
        "source": "detail_page_json_ld",
    }
    scope, _ = classify_india_scope(job)
    assert scope == IndiaScope.outside_india


def test_us_url_query_outside_india():
    url = "https://www.google.com/about/careers/applications/jobs/results/1-engineer?location=United%20States"
    scope, label = classify_india_scope(_job("Engineer", None, listing_url=url))
    assert scope == IndiaScope.outside_india
    assert label == "United States"


def test_location_indicates_outside_india_helper():
    assert location_indicates_outside_india("Riyadh, Saudi Arabia")
    assert not location_indicates_outside_india("Bengaluru, India")

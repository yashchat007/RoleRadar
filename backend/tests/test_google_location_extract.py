from app.discovery.india_location import IndiaScope, classify_india_scope
from app.discovery.location_extract import (
    _google_india_locations_from_body,
    _looks_like_job_title_not_location,
    _sanitize_location_candidate,
)
from tests.test_india_location import _job


def test_rejects_title_as_location():
    title = "Silicon Engineering Intern, PhD, Summer 2027"
    assert _looks_like_job_title_not_location(title)
    assert _sanitize_location_candidate(title) is None


def test_google_body_parser_multi_site():
    body = """
    Locations
    Bengaluru, Karnataka, India
    ; Hyderabad, Telangana, India
    Note: By applying to this position
    """
    sites = _google_india_locations_from_body(body)
    assert len(sites) == 2
    assert "Bengaluru" in sites[0]
    assert "Hyderabad" in sites[1]


def test_classify_google_intern_with_site_locations_meta():
    job = _job("Silicon Engineering Intern Phd Summer 2027", "Bengaluru, Karnataka, India")
    job.employment_type = "internship"
    job.location_meta = {
        "countries": ["India"],
        "india_site_locations": [
            "Bengaluru, Karnataka, India",
            "Hyderabad, Telangana, India",
        ],
        "normalized_location": "Bengaluru, Karnataka, India",
        "source": "google_official_body",
    }
    scope, label = classify_india_scope(job)
    assert scope == IndiaScope.india_based
    assert label == "Bengaluru"


def test_phd_intern_stays_internship_type():
    from app.discovery.employment_type import classify_employment_type

    job = _job("Software Engineering Phd Intern Summer 2027", "Hyderabad, Telangana, India")
    job.location_meta = {"employment_type_hint": "internship"}
    assert classify_employment_type(job) == "internship"

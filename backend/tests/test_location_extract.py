from app.discovery.location_extract import LocationFacts, merge_location_facts, _countries_from_location_string
from app.discovery.india_location import IndiaScope, classify_india_scope
from tests.test_india_location import _job


def test_countries_from_bengaluru_string():
    assert "India" in _countries_from_location_string("Bengaluru, Karnataka, India")


def test_merge_json_ld_and_url_query():
    url = LocationFacts(
        normalized_location="India",
        countries=["India"],
        source="listing_url_query",
        evidence="listing_url_query location=India",
    )
    ld = LocationFacts(
        normalized_location="Bengaluru, Karnataka, India",
        countries=["India"],
        work_mode="onsite",
        india_eligible=True,
        source="detail_page_json_ld",
        evidence="json_ld jobLocation=Bengaluru",
    )
    merged = merge_location_facts(url, ld)
    assert merged.normalized_location == "Bengaluru, Karnataka, India"
    assert "India" in merged.countries
    assert merged.india_eligible is True


def test_classify_uses_location_meta_countries():
    job = _job("Software Engineer Intern", "Bengaluru")
    job.location_meta = {
        "countries": ["India"],
        "work_mode": "onsite",
        "india_eligible": True,
        "evidence": "json_ld jobLocation=Bengaluru, India",
        "source": "detail_page_json_ld",
    }
    scope, label = classify_india_scope(job)
    assert scope == IndiaScope.india_based
    assert label == "Bengaluru"


def test_classify_meta_us_only_ineligible():
    job = _job("Account Executive", "San Francisco, CA")
    job.location_meta = {
        "countries": ["United States"],
        "work_mode": "onsite",
        "india_eligible": False,
        "evidence": "label:Location: US only",
        "source": "detail_page_dom",
    }
    scope, _ = classify_india_scope(job)
    assert scope == IndiaScope.outside_india

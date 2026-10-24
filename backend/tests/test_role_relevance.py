import uuid
from datetime import UTC, datetime

from app.matching.engine import compute_match
from app.matching.role_family import classify_job_role_family
from app.matching.skills import skill_hits_in_posting
from app.models.job import Job
from app.models.profile import Profile


def _technical_profile() -> Profile:
    return Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=[
            {"name": "Python", "from_resume": True, "source": {"quote": "Python"}},
            {"name": "FastAPI", "from_resume": True},
            {"name": "Git", "from_resume": True},
        ],
        education=[{"institution": "State University B.S. CS 2024", "end_year": 2024, "from_resume": True}],
        experience=[
            {
                "title": "Software Engineer Intern",
                "company": "Acme",
                "start_year": 2023,
                "end_year": 2024,
                "from_resume": True,
            }
        ],
        projects=[],
        preferences={
            "target_profile": "technical",
            "target_level": "internship",
            "preferred_role_families": ["Software Engineering", "Data/ML"],
            "open_to_remote": True,
        },
    )


def _job(title: str, extra: str = "") -> Job:
    return Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key="k",
        title=title,
        location="India",
        remote_flag=False,
        description_sections={"summary": extra},
        listing_url="https://www.atlassian.com/company/careers/details/1",
        apply_url="https://www.atlassian.com/company/careers/details/1",
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )


def test_sales_role_classified_and_ranked_below_engineering():
    sales = compute_match(_job("Solution Sales Executive - Service Collection (India)"), _technical_profile(), resume_available=True)
    swe = compute_match(_job("Software Engineer Intern"), _technical_profile(), resume_available=True)
    assert classify_job_role_family(_job("Solution Sales Executive")) == "Sales"
    assert sales.score < swe.score
    assert sales.role_family == "Sales"
    assert any("Role family" in r for r in sales.top_reasons)


def test_location_token_not_counted_as_skill_hit():
    profile = _technical_profile()
    profile.skills = [{"name": "india", "from_resume": True}]
    hits = skill_hits_in_posting({"india"}, "Solution Sales Executive based in India")
    assert hits == []


def test_engineering_fixture_from_official_style_title():
    job = _job(
        "Backend Engineer, Payments",
        "Requirements: 3+ years Python experience. Bachelor degree.",
    )
    result = compute_match(job, _technical_profile(), resume_available=True)
    assert result.role_family == "Software Engineering"
    assert result.score is not None and result.score >= 45

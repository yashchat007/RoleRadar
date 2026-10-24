from app.discovery.employment_type import classify_employment_type
from app.discovery.types import NormalizedJob
from app.discovery.normalize import content_hash


def _job(title: str, summary: str = "") -> NormalizedJob:
    desc = {"summary": summary} if summary else {"summary": title}
    return NormalizedJob(
        source_job_key="k",
        title=title,
        location=None,
        remote_flag=None,
        description_sections=desc,
        posted_at=None,
        deadline_at=None,
        apply_url="https://example.com/apply",
        listing_url="https://example.com/job",
        content_hash=content_hash(title, None, desc),
    )


def test_internship_from_title():
    assert classify_employment_type(_job("Software Engineering Intern")) == "internship"


def test_graduate_alone_not_internship():
    assert classify_employment_type(_job("University Graduate Software Engineer")) == "full_time"


def test_senior_engineer_full_time():
    assert classify_employment_type(_job("Senior Software Engineer")) == "full_time"


def test_unknown_when_ambiguous():
    assert classify_employment_type(_job("Engineer")) == "unknown"

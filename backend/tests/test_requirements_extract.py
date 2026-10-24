import uuid
from datetime import UTC, datetime

from app.discovery.job_title import normalize_job_title
from app.matching.requirements import extract_requirement_phrases
from app.models.job import Job


def test_title_not_extracted_as_requirement():
    title = "109375266236572358 Silicon Engineering Intern PhD"
    display, _ = normalize_job_title(title, "https://www.google.com/about/careers/applications/jobs/results/109375266236572358-x")
    job = Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key="k",
        title=display,
        description_sections={"summary": display},
        listing_url="https://www.google.com/about/careers/applications/jobs/results/109375266236572358-x",
        apply_url="https://example.com",
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )
    phrases = extract_requirement_phrases(job)
    assert not any(p.lower() == display.lower() for p in phrases)

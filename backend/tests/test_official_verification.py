import uuid
from datetime import UTC, datetime

import pytest
from unittest.mock import MagicMock

from app.discovery.lifecycle_status import OPEN, POSSIBLY_CLOSED
from app.discovery.official_verify import official_page_indicates_open, reopen_after_official_verification
from app.models.enums import ListingStatus
from app.models.job import Job


def _job() -> Job:
    now = datetime.now(UTC)
    return Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key="k",
        title="Research Scientist Intern",
        listing_url="https://www.metacareers.com/profile/job_details/1",
        apply_url="https://www.metacareers.com/profile/job_details/1",
        listing_status=ListingStatus.active,
        lifecycle_status=POSSIBLY_CLOSED,
        missed_scan_count=1,
        content_hash="x",
        first_seen_at=now,
        last_seen_at=now,
    )


def test_official_page_indicates_open_requires_apply_and_title():
    assert official_page_indicates_open(
        {
            "http_status": 200,
            "h1": "Software Engineer",
            "has_apply_cta": True,
            "closed_hint": False,
            "login_wall": False,
        }
    )
    assert not official_page_indicates_open({"http_status": 200, "h1": "X", "has_apply_cta": False})
    assert not official_page_indicates_open({"http_status": 404, "h1": "Gone", "has_apply_cta": True})


@pytest.mark.asyncio
async def test_reopen_after_official_verification():
    job = _job()
    session = MagicMock()
    evidence = {
        "http_status": 200,
        "h1": "Research Scientist Intern",
        "has_apply_cta": True,
        "closed_hint": False,
        "final_url": job.listing_url,
    }
    ok = await reopen_after_official_verification(session, job, evidence)
    assert ok
    assert job.lifecycle_status == OPEN
    assert job.missed_scan_count == 0
    assert job.last_verified_at is not None
    assert session.add.called

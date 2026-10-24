import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.discovery.discovery_scope import discovery_scope_key
from app.discovery.lifecycle import apply_scan_results
from app.discovery.lifecycle_status import OPEN, POSSIBLY_CLOSED
from app.discovery.types import NormalizedJob
from app.models.enums import ListingStatus
from app.models.job import Job


def _job(key: str, scope: str | None = None) -> Job:
    now = datetime.now(UTC)
    meta = {"discovery_scope_key": scope} if scope else {}
    return Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key=key,
        title="Old listing",
        listing_url="https://example.com/jobs/old",
        apply_url="https://example.com/jobs/old",
        listing_status=ListingStatus.active,
        lifecycle_status=OPEN,
        missed_scan_count=0,
        content_hash="old",
        location_meta=meta,
        first_seen_at=now,
        last_seen_at=now,
    )


def _incoming(key: str) -> NormalizedJob:
    return NormalizedJob(
        source_job_key=key,
        title="New",
        location="Bengaluru",
        remote_flag=False,
        description_sections={"summary": "intern"},
        posted_at=None,
        deadline_at=None,
        apply_url=f"https://example.com/jobs/{key}",
        listing_url=f"https://example.com/jobs/{key}",
        content_hash="new",
    )


@pytest.mark.asyncio
async def test_scope_mismatch_does_not_mark_possibly_closed():
    scope_a = discovery_scope_key("google_official", ("https://facet-a",))
    scope_b = discovery_scope_key("google_official", ("https://facet-b",))
    assert scope_a != scope_b

    existing = _job("stale", scope=scope_a)
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=existing)
    session.scalars = AsyncMock(return_value=MagicMock(all=lambda: [existing]))
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_scan_results(
        session,
        existing.company_id,
        [_incoming("fresh")],
        frozenset({"example.com"}),
        scan_succeeded=True,
        scan_complete=True,
        discovery_scope_key=scope_b,
    )
    assert existing.missed_scan_count == 0
    assert existing.lifecycle_status == OPEN


@pytest.mark.asyncio
async def test_same_scope_miss_marks_possibly_closed():
    scope = discovery_scope_key("meta_official", ("https://metacareers.com/jobsearch/",))
    existing = _job("gone", scope=scope)
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=existing)
    session.scalars = AsyncMock(return_value=MagicMock(all=lambda: [existing]))
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_scan_results(
        session,
        existing.company_id,
        [],
        frozenset({"example.com"}),
        scan_succeeded=True,
        scan_complete=True,
        discovery_scope_key=scope,
    )
    assert existing.missed_scan_count == 1
    assert existing.lifecycle_status == POSSIBLY_CLOSED

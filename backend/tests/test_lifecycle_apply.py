"""Lifecycle transition rules (in-memory, no DB)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.discovery.lifecycle import apply_scan_results
from app.discovery.lifecycle_status import CLOSED, MISSED_FOR_CLOSED, OPEN, POSSIBLY_CLOSED
from app.discovery.types import NormalizedJob
from app.models.enums import ListingStatus
from app.models.job import Job


def _job(key: str, **kwargs) -> Job:
    now = datetime.now(UTC)
    j = Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key=key,
        title=kwargs.get("title", "Test"),
        listing_url=f"https://example.com/jobs/{key}",
        apply_url=f"https://example.com/jobs/{key}",
        listing_status=ListingStatus.active,
        lifecycle_status=kwargs.get("lifecycle_status", OPEN),
        missed_scan_count=kwargs.get("missed_scan_count", 0),
        content_hash="old",
        first_seen_at=now,
        last_seen_at=now,
    )
    return j


def _incoming(key: str) -> NormalizedJob:
    return NormalizedJob(
        source_job_key=key,
        title="Incoming",
        location="Bengaluru, IN",
        remote_flag=False,
        description_sections={"summary": "internship"},
        posted_at=None,
        deadline_at=None,
        apply_url=f"https://example.com/jobs/{key}",
        listing_url=f"https://example.com/jobs/{key}",
        content_hash="new",
    )


@pytest.mark.asyncio
async def test_incomplete_scan_does_not_increment_misses():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.scalars = AsyncMock(return_value=MagicMock(all=lambda: [_job("missing")]))

    created, updated, closed = await apply_scan_results(
        session,
        uuid.uuid4(),
        [],
        frozenset({"example.com"}),
        scan_succeeded=True,
        scan_complete=False,
    )
    assert created == updated == closed == 0
    assert session.scalars.await_count == 0


@pytest.mark.asyncio
async def test_failed_scan_does_not_increment_misses():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.scalars = AsyncMock(return_value=MagicMock(all=lambda: [_job("missing")]))

    created, updated, closed = await apply_scan_results(
        session,
        uuid.uuid4(),
        [],
        frozenset({"example.com"}),
        scan_succeeded=False,
    )
    assert created == updated == closed == 0
    assert session.scalars.await_count == 0


@pytest.mark.asyncio
async def test_missing_job_becomes_possibly_closed_then_closed():
    existing = _job("gone", missed_scan_count=0)
    session = AsyncMock()

    async def scalar_side_effect(stmt):
        return existing

    session.scalar = AsyncMock(side_effect=scalar_side_effect)
    session.scalars = AsyncMock(return_value=MagicMock(all=lambda: [existing]))
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_scan_results(
        session,
        existing.company_id,
        [],
        frozenset({"example.com"}),
        scan_succeeded=True,
    )
    assert existing.missed_scan_count == 1
    assert existing.lifecycle_status == POSSIBLY_CLOSED

    await apply_scan_results(
        session,
        existing.company_id,
        [],
        frozenset({"example.com"}),
        scan_succeeded=True,
    )
    assert existing.missed_scan_count == 2
    assert existing.lifecycle_status == POSSIBLY_CLOSED

    await apply_scan_results(
        session,
        existing.company_id,
        [],
        frozenset({"example.com"}),
        scan_succeeded=True,
    )
    assert existing.missed_scan_count == MISSED_FOR_CLOSED
    assert existing.lifecycle_status == CLOSED


@pytest.mark.asyncio
async def test_seen_job_resets_miss_count():
    existing = _job("keep", missed_scan_count=2, lifecycle_status=POSSIBLY_CLOSED)
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=existing)
    session.scalars = AsyncMock(return_value=MagicMock(all=lambda: [existing]))
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_scan_results(
        session,
        existing.company_id,
        [_incoming("keep")],
        frozenset({"example.com"}),
        scan_succeeded=True,
    )
    assert existing.missed_scan_count == 0
    assert existing.lifecycle_status == OPEN

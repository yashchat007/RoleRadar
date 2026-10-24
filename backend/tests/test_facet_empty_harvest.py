import pytest

from app.discovery.adapters.listing_harvest import facet_harvest_to_jobs
from app.discovery.context import ScanContext


@pytest.mark.asyncio
async def test_allow_empty_harvest_returns_success_shape():
    ctx = ScanContext(company=None, http=None, user_agent="", page=None)
    result = await facet_harvest_to_jobs(
        ctx,
        [],
        frozenset({"www.metacareers.com"}),
        {},
        "meta_official",
        [],
        allow_empty_harvest=True,
    )
    assert result.fatal_error is None
    assert result.jobs == []
    assert any("0 official listing" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_empty_harvest_without_flag_is_fatal():
    ctx = ScanContext(company=None, http=None, user_agent="", page=None)
    result = await facet_harvest_to_jobs(
        ctx,
        [],
        frozenset({"www.metacareers.com"}),
        {},
        "meta_official",
        [],
    )
    assert result.fatal_error == "No official job listing URLs matched"

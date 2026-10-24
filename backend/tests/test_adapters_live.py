import pytest

from app.discovery.adapters.stripe import StripeOfficialAdapter
from app.discovery.browser import browser_page
from app.discovery.context import ScanContext
from app.models.company import Company


@pytest.mark.live
@pytest.mark.asyncio
async def test_stripe_adapter_finds_official_listings():
    company = Company(
        name="Stripe",
        career_page_url="https://stripe.com/jobs/search",
        adapter_key="stripe_official",
    )
    adapter = StripeOfficialAdapter()
    async with browser_page() as page:
        ctx = ScanContext(company=company, http=None, user_agent="", page=page, max_jobs=5)
        result = await adapter.extract_listings(ctx)
    assert result.fatal_error is None
    assert len(result.jobs) >= 1
    for job in result.jobs:
        assert "stripe.com" in job.apply_url

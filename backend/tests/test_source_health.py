import uuid
from datetime import datetime

from app.models.company import Company
from app.models.enums import LastScanStatus, ParserStatus
from app.services.source_health import collect_source_status_messages, company_source_state


def _company(
    name: str,
    *,
    adapter_key: str | None = None,
    parser_status: ParserStatus = ParserStatus.pending_validation,
    is_enabled: bool = False,
    last_scan_status: LastScanStatus | None = None,
    last_error: str | None = None,
) -> Company:
    return Company(
        id=uuid.uuid4(),
        name=name,
        career_page_url="https://example.com/careers",
        adapter_key=adapter_key,
        parser_status=parser_status,
        is_enabled=is_enabled,
        last_scan_status=last_scan_status,
        last_error=last_error,
        last_success_at=None,
        last_error_at=None,
    )


def test_pending_adapter_is_reported_not_silent():
    messages = collect_source_status_messages(
        [_company("Stripe", adapter_key="stripe_official")]
    )
    assert any("Stripe" in m and "pending validation" in m for m in messages)


def test_enabled_without_scan_is_reported():
    messages = collect_source_status_messages(
        [
            _company(
                "Stripe",
                adapter_key="stripe_official",
                parser_status=ParserStatus.enabled,
                is_enabled=True,
                last_scan_status=None,
            )
        ]
    )
    assert any("never scanned" in m for m in messages)


def test_company_source_state_scan_ok():
    c = _company(
        "Stripe",
        adapter_key="stripe_official",
        parser_status=ParserStatus.enabled,
        is_enabled=True,
        last_scan_status=LastScanStatus.success,
    )
    assert company_source_state(c) == "scan_ok"


def test_failed_validation_is_reported():
    messages = collect_source_status_messages(
        [
            _company(
                "Cloudflare",
                adapter_key="cloudflare_official",
                parser_status=ParserStatus.failed,
                last_error="greenhouse links only",
            )
        ]
    )
    assert any("failed" in m and "greenhouse" in m for m in messages)

"""Human-readable source health lines for APIs (jobs meta, Today, etc.)."""

from app.models.company import Company
from app.models.enums import LastScanStatus, ParserStatus


def company_source_state(company: Company) -> str:
    if company.parser_status == ParserStatus.failed:
        return "validation_failed"
    if company.parser_status == ParserStatus.disabled:
        return "disabled"
    if company.is_enabled:
        if company.last_scan_status == LastScanStatus.error:
            return "scan_failed"
        if company.last_scan_status in (LastScanStatus.success, LastScanStatus.partial):
            return "scan_ok"
        if company.last_scan_status is None:
            return "enabled_never_scanned"
        if company.last_scan_status == LastScanStatus.skipped:
            return "scan_skipped"
        return "enabled"
    if company.adapter_key and company.parser_status == ParserStatus.pending_validation:
        return "pending_validation"
    if company.parser_status == ParserStatus.validating:
        return "validating"
    return "pending_validation"


def collect_source_status_messages(companies: list[Company]) -> list[str]:
    """Sources that are not in a healthy, ingesting state — never treated as OK by silence."""
    messages: list[str] = []
    for c in sorted(companies, key=lambda x: x.name):
        if c.parser_status == ParserStatus.failed:
            detail = c.last_error or "validation failed"
            messages.append(f"{c.name}: failed ({detail})")
            continue
        if c.parser_status == ParserStatus.disabled:
            messages.append(f"{c.name}: disabled")
            continue
        if c.is_enabled:
            if c.last_scan_status == LastScanStatus.error:
                detail = c.last_error or "scan error"
                messages.append(f"{c.name}: scan error ({detail})")
            elif c.last_scan_status is None:
                messages.append(f"{c.name}: enabled but never scanned")
            elif c.last_scan_status == LastScanStatus.skipped:
                messages.append(f"{c.name}: scan skipped")
            continue
        if c.adapter_key and c.parser_status == ParserStatus.pending_validation:
            messages.append(f"{c.name}: pending validation (adapter {c.adapter_key})")
        elif c.adapter_key and c.parser_status == ParserStatus.validating:
            messages.append(f"{c.name}: validation in progress")
    return messages

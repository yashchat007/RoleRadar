import logging
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.discovery.browser import browser_page
from app.discovery.context import ScanContext
from app.discovery.http_client import discovery_http_client
from app.discovery.discovery_scope import discovery_scope_key
from app.discovery.lifecycle import apply_scan_results
from app.discovery.registry import get_adapter
from app.models.company import Company
from app.models.enums import ExtractionMode, LastScanStatus
from app.models.scan_run import ScanRun

logger = logging.getLogger(__name__)


def _allowed_hosts(company: Company, adapter_hosts: frozenset[str]) -> frozenset[str]:
    if company.allowed_hosts:
        return frozenset(company.allowed_hosts)
    return adapter_hosts


async def scan_company(session: AsyncSession, company: Company) -> ScanRun:
    t0 = time.perf_counter()
    run = ScanRun(
        company_id=company.id,
        started_at=datetime.now(UTC),
        status=LastScanStatus.error,
    )
    session.add(run)
    await session.flush()

    def finish(error: str | None = None) -> ScanRun:
        run.finished_at = datetime.now(UTC)
        run.duration_ms = int((time.perf_counter() - t0) * 1000)
        if error:
            run.error_message = error
            company.last_scan_status = LastScanStatus.error
            company.last_error = error
            company.last_error_at = run.finished_at
        return run

    if not company.adapter_key:
        finish("No adapter_key configured")
        await session.commit()
        return run

    try:
        adapter = get_adapter(company.adapter_key)
    except KeyError:
        finish(f"Unknown adapter: {company.adapter_key}")
        await session.commit()
        return run

    async with discovery_http_client() as http:
        inspection = await adapter.inspect(ScanContext(company=company, http=http, user_agent=""))
        company.allowed_hosts = inspection.allowed_hosts or list(adapter.official_hosts)
        company.extraction_mode = (
            ExtractionMode.browser_render
            if inspection.extraction_mode == "browser_render"
            else ExtractionMode.static_html
        )
        hosts = _allowed_hosts(company, adapter.official_hosts)

        async def extract_with(page=None) -> None:
            result = await adapter.extract_listings(
                ScanContext(company=company, http=http, user_agent="", page=page)
            )
            if result.fatal_error:
                finish(result.fatal_error)
                return

            truncated = any(
                w.startswith("Truncated to ") for w in result.warnings
            )
            scope_key = discovery_scope_key(adapter.adapter_key, adapter.discovery_search_urls)
            inventory_complete = inspection.inventory_complete
            created, updated, closed = await apply_scan_results(
                session,
                company.id,
                result.jobs,
                hosts,
                scan_succeeded=result.fatal_error is None and len(result.jobs) > 0,
                scan_complete=not truncated and inventory_complete,
                discovery_scope_key=scope_key or None,
            )
            run.status = LastScanStatus.partial if truncated else LastScanStatus.success
            run.jobs_seen = len(result.jobs)
            run.jobs_created = created
            run.jobs_updated = updated
            run.jobs_closed = closed
            run.extraction_mode_used = company.extraction_mode
            company.last_scan_status = run.status
            company.last_success_at = datetime.now(UTC)
            company.last_error = None
            company.last_error_at = None
            if result.warnings:
                logger.info("%s scan warnings: %s", company.name, "; ".join(result.warnings))
            harvest_summary = next(
                (w for w in result.warnings if w.startswith("Harvest:")),
                f"Harvested {len(result.jobs)} job(s)",
            )
            finish()
            cfg = dict(company.config or {})
            cfg["last_harvest"] = {
                "summary": harvest_summary,
                "jobs_seen": len(result.jobs),
                "truncated": any(w.startswith("Truncated to ") for w in result.warnings),
                "duration_ms": run.duration_ms,
            }
            company.config = cfg

        if company.extraction_mode == ExtractionMode.browser_render:
            async with browser_page() as page:
                await extract_with(page)
        else:
            await extract_with(None)

    await session.commit()

    if run.status in (LastScanStatus.success, LastScanStatus.partial) and run.jobs_seen:
        from app.services.match_service import recompute_matches_for_user
        from app.services.user_bootstrap import DEV_EMAIL
        from app.models.user import User

        user = await session.scalar(select(User).where(User.email == DEV_EMAIL))
        if user:
            await recompute_matches_for_user(session, user.id)

    return run


async def scan_enabled_companies(session: AsyncSession) -> list[uuid.UUID]:
    companies = await session.scalars(select(Company).where(Company.is_enabled.is_(True)))
    ids: list[uuid.UUID] = []
    for company in companies.all():
        await scan_company(session, company)
        ids.append(company.id)
    return ids

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.discovery.browser import browser_page
from app.discovery.context import ScanContext
from app.discovery.http_client import discovery_http_client
from app.discovery.orchestrator import scan_company
from app.discovery.normalize import validate_job_urls
from app.discovery.registry import get_adapter
from app.models.company import Company
from app.models.enums import ExtractionMode, ParserStatus


@dataclass
class ValidationResult:
    passed: bool
    message: str
    jobs_sampled: int = 0


async def validate_company_adapter(session: AsyncSession, company: Company) -> ValidationResult:
    if not company.adapter_key:
        return ValidationResult(False, "adapter_key is not set")

    try:
        adapter = get_adapter(company.adapter_key)
    except KeyError:
        return ValidationResult(False, f"Unknown adapter_key: {company.adapter_key}")

    async with discovery_http_client() as http:
        inspection = await adapter.inspect(ScanContext(company=company, http=http, user_agent=""))
        company.allowed_hosts = inspection.allowed_hosts
        company.extraction_mode = (
            ExtractionMode.browser_render
            if inspection.extraction_mode == "browser_render"
            else ExtractionMode.static_html
        )
        company.parser_status = ParserStatus.validating

        async def extract(page=None):
            ctx = ScanContext(
                company=company,
                http=http,
                user_agent="",
                page=page,
                max_jobs=settings.discovery_validation_max_jobs,
            )
            return await adapter.extract_listings(ctx)

        if company.extraction_mode == ExtractionMode.browser_render:
            async with browser_page() as page:
                result = await extract(page)
        else:
            result = await extract(None)

    if result.fatal_error:
        company.parser_status = ParserStatus.failed
        company.is_enabled = False
        company.last_error = result.fatal_error
        await session.commit()
        return ValidationResult(False, result.fatal_error)

    if len(result.jobs) < 1:
        company.parser_status = ParserStatus.failed
        company.is_enabled = False
        company.last_error = "Validation found zero ingestible jobs"
        await session.commit()
        return ValidationResult(False, company.last_error)

    allowed = frozenset(adapter.official_hosts)
    for job in result.jobs[:8]:
        try:
            validate_job_urls(job, allowed)
        except ValueError as e:
            msg = str(e)
            company.parser_status = ParserStatus.failed
            company.is_enabled = False
            company.last_error = msg
            await session.commit()
            return ValidationResult(False, msg)

    company.parser_status = ParserStatus.enabled
    company.is_enabled = True
    company.last_error = None
    await session.commit()

    await scan_company(session, company)

    return ValidationResult(
        passed=True,
        message="Adapter validated and initial scan completed",
        jobs_sampled=len(result.jobs),
    )

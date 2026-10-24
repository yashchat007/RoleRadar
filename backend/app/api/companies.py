import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.models.enums import ListingStatus, ParserStatus
from app.models.job import Job
from app.schemas.company import CompanyOut
from app.schemas.company_discover import CompanyDiscoverCard
from app.services.company_brand import company_logo_url
from app.services.company_priority import discover_company_sort_key, technical_priority_rank
from app.services.company_registry import ACTIVE_REGISTRY_COMPANIES
from app.services.source_health import company_source_state
from app.discovery.lifecycle_status import OPEN
from app.models.enums import LastScanStatus

router = APIRouter(prefix="/companies", tags=["companies"])


def _status_label(company: Company) -> str:
    if company.last_scan_status == LastScanStatus.partial:
        return "Partial scan"
    if company.last_scan_status == LastScanStatus.error:
        return "Scan failed"
    if company.last_scan_status == LastScanStatus.success:
        return "Scan OK"
    if company.last_scan_status is None and company.is_enabled:
        return "Not scanned"
    return company.last_scan_status.value if company.last_scan_status else "Unknown"


@router.get("/discover", response_model=list[CompanyDiscoverCard])
async def list_companies_for_discover(db: AsyncSession = Depends(get_db)) -> list[CompanyDiscoverCard]:
    counts = dict(
        (await db.execute(
            select(Job.company_id, func.count())
            .where(
                Job.listing_status == ListingStatus.active,
                Job.lifecycle_status == OPEN,
                Job.employment_type == "internship",
                Job.india_scope.in_(("india_based", "remote_india", "remote_global_india_ok")),
            )
            .group_by(Job.company_id)
        )).all()
    )
    companies = [
        c
        for c in (await db.scalars(select(Company))).all()
        if c.name in ACTIVE_REGISTRY_COMPANIES
    ]
    companies.sort(key=lambda c: discover_company_sort_key(c.name))
    cards: list[CompanyDiscoverCard] = []
    for c in companies:
        job_count = counts.get(c.id, 0) if c.is_enabled and c.parser_status == ParserStatus.enabled else 0
        coverage = None
        last_scan_jobs_seen = None
        if isinstance(c.config, dict):
            harvest = c.config.get("last_harvest") or {}
            if isinstance(harvest, dict):
                coverage = harvest.get("summary")
                last_scan_jobs_seen = harvest.get("jobs_seen")
        status_label = _status_label(c)
        cards.append(
            CompanyDiscoverCard(
                id=c.id,
                name=c.name,
                career_page_url=c.career_page_url,
                parser_status=c.parser_status,
                is_enabled=c.is_enabled,
                last_scan_status=c.last_scan_status,
                active_job_count=job_count,
                india_internship_count=job_count,
                source_state=company_source_state(c),
                last_scan_at=c.last_success_at,
                coverage_note=coverage,
                status_label=status_label,
                last_scan_jobs_seen=last_scan_jobs_seen,
                company_logo_url=company_logo_url(c.career_page_url),
                priority_rank=technical_priority_rank(c.name),
            )
        )
    return cards


@router.get("", response_model=list[CompanyOut])
async def list_companies(db: AsyncSession = Depends(get_db)) -> list[Company]:
    result = await db.scalars(select(Company).order_by(Company.name))
    return list(result.all())


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Company:
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

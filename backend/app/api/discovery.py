import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.discovery.orchestrator import scan_company, scan_enabled_companies
from app.discovery.validation import validate_company_adapter
from app.models.company import Company
from app.models.enums import ParserStatus
from app.models.scan_run import ScanRun
from app.schemas.discovery import CompanyHealthOut, DiscoveryStatusOut
from app.schemas.validation import ValidationOut

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/status", response_model=DiscoveryStatusOut)
async def discovery_status(db: AsyncSession = Depends(get_db)) -> DiscoveryStatusOut:
    enabled = await db.scalar(
        select(func.count()).select_from(Company).where(Company.is_enabled.is_(True))
    )
    pending = await db.scalar(
        select(func.count())
        .select_from(Company)
        .where(Company.parser_status == ParserStatus.pending_validation)
    )
    last_scan = await db.scalar(select(func.max(ScanRun.started_at)))
    return DiscoveryStatusOut(
        enabled_companies=enabled or 0,
        pending_validation=pending or 0,
        scanning=False,
        last_aggregate_scan_at=last_scan,
    )


@router.get("/health", response_model=list[CompanyHealthOut])
async def companies_health(db: AsyncSession = Depends(get_db)) -> list[CompanyHealthOut]:
    companies = await db.scalars(select(Company).order_by(Company.name))
    return [
        CompanyHealthOut(
            company_id=c.id,
            name=c.name,
            parser_status=c.parser_status,
            last_scan_status=c.last_scan_status,
            last_success_at=c.last_success_at,
            last_error=c.last_error,
            is_enabled=c.is_enabled,
        )
        for c in companies.all()
    ]


@router.post("/scan")
async def run_discovery_scan(db: AsyncSession = Depends(get_db)) -> dict:
    ids = await scan_enabled_companies(db)
    return {"scanned_company_ids": [str(i) for i in ids], "count": len(ids)}


@router.post("/companies/{company_id}/validate", response_model=ValidationOut)
async def validate_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ValidationOut:
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    result = await validate_company_adapter(db, company)
    return ValidationOut(
        passed=result.passed,
        message=result.message,
        jobs_sampled=result.jobs_sampled,
    )


@router.post("/companies/{company_id}/scan")
async def scan_one_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if not company.is_enabled:
        raise HTTPException(status_code=400, detail="Company is not enabled for scheduled scans")
    run = await scan_company(db, company)
    return {
        "scan_run_id": str(run.id),
        "status": run.status.value,
        "jobs_seen": run.jobs_seen,
        "error_message": run.error_message,
    }

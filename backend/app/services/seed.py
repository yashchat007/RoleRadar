import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.enums import ParserStatus
from app.services.company_registry import ACTIVE_REGISTRY_COMPANIES, CAREER_URLS


async def seed_companies(session: AsyncSession) -> int:
    seed_path = Path(__file__).resolve().parents[2] / "data" / "companies.seed.json"
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    created = 0
    for row in data:
        existing = await session.scalar(select(Company).where(Company.name == row["name"]))
        if existing:
            if row.get("adapter_key") and not existing.adapter_key:
                existing.adapter_key = row["adapter_key"]
            continue
        session.add(
            Company(
                name=row["name"],
                career_page_url=row["career_page_url"],
                adapter_key=row.get("adapter_key"),
                parser_status=ParserStatus(row.get("parser_status", "pending_validation")),
                is_enabled=bool(row.get("is_enabled", False)),
            )
        )
        created += 1
    await session.commit()
    return created


async def apply_active_company_registry(session: AsyncSession) -> None:
    """Disable scheduled discovery for companies outside the eight-company registry."""
    companies = await session.scalars(select(Company))
    for company in companies.all():
        in_registry = company.name in ACTIVE_REGISTRY_COMPANIES
        official_url = CAREER_URLS.get(company.name)
        if official_url:
            company.career_page_url = official_url
        if not in_registry:
            company.is_enabled = False
            if company.parser_status == ParserStatus.enabled:
                company.parser_status = ParserStatus.disabled
    await session.commit()


async def sync_pilot_adapter_keys(session: AsyncSession) -> None:
    """Apply adapter_key from seed to existing pilot rows (idempotent)."""
    seed_path = Path(__file__).resolve().parents[2] / "data" / "companies.seed.json"
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in data}
    companies = await session.scalars(select(Company))
    for company in companies.all():
        row = by_name.get(company.name)
        if row and row.get("adapter_key"):
            company.adapter_key = row["adapter_key"]
    await session.commit()

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("backend/app/services/seed.py", """import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.enums import ParserStatus


async def seed_companies(session: AsyncSession) -> int:
    seed_path = Path(__file__).resolve().parents[2] / "data" / "companies.seed.json"
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    created = 0
    for row in data:
        exists = await session.scalar(select(Company).where(Company.name == row["name"]))
        if exists:
            continue
        session.add(
            Company(
                name=row["name"],
                career_page_url=row["career_page_url"],
                parser_status=ParserStatus(row.get("parser_status", "pending_validation")),
                is_enabled=bool(row.get("is_enabled", False)),
            )
        )
        created += 1
    await session.commit()
    return created
""")

w("backend/app/api/health.py", """from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
""")

w("backend/app/api/companies.py", """import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])


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
""")

w("backend/app/api/discovery.py", """from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.models.enums import ParserStatus
from app.models.scan_run import ScanRun
from app.schemas.discovery import CompanyHealthOut, DiscoveryStatusOut

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
""")

w("backend/app/main.py", """from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import companies, discovery, health
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_companies


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_companies(session)
    yield


app = FastAPI(title="RoleRadar API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
""")

print("api ok")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import bookmarks, companies, digest, discovery, health, jobs, profile, today, tracker, watches
from app.api import settings as settings_api
from app.config import settings
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.models.job_notification import JobNotification  # noqa: F401 — register metadata
from app.services.seed import seed_companies, sync_pilot_adapter_keys
from app.services.user_bootstrap import ensure_dev_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("ALTER TABLE job_matches ADD COLUMN IF NOT EXISTS role_family VARCHAR(64)")
        )
        await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS india_scope VARCHAR(32)"))
        await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location_meta JSONB"))
        await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS employment_type VARCHAR(32)"))
        await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(32)"))
        await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ"))
        await conn.execute(
            text(
                "UPDATE jobs SET lifecycle_status = 'open' WHERE lifecycle_status IS NULL AND listing_status = 'active'"
            )
        )
        from app.scripts.schema_patches import apply_schema_patches

        await apply_schema_patches(conn)
    async with SessionLocal() as session:
        await seed_companies(session)
        await sync_pilot_adapter_keys(session)
        await ensure_dev_user(session)
        from app.services.seed import apply_active_company_registry

        await apply_active_company_registry(session)
        from sqlalchemy import select

        from app.discovery.employment_type import classify_employment_type
        from app.discovery.india_location import classify_india_scope
        from app.models.job import Job

        jobs = (await session.scalars(select(Job))).all()
        for job in jobs:
            if not job.employment_type:
                job.employment_type = classify_employment_type(job)
            if not job.lifecycle_status and job.listing_status.value == "active":
                job.lifecycle_status = "open"
            scope, loc_hint = classify_india_scope(job)
            if job.india_scope != scope.value:
                job.india_scope = scope.value
            if loc_hint and not job.location:
                job.location = loc_hint
        await session.commit()
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
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(today.router, prefix="/api/v1")
app.include_router(tracker.router, prefix="/api/v1")
app.include_router(bookmarks.router, prefix="/api/v1")
app.include_router(settings_api.router, prefix="/api/v1")
app.include_router(watches.router, prefix="/api/v1")
app.include_router(digest.router, prefix="/api/v1")

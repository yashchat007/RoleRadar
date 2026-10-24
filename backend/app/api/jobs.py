import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.discovery.india_location import VERIFIED_INDIA_SCOPES, display_location_label
from app.discovery.lifecycle_status import OPEN
from app.matching.eligibility_display import derive_eligibility_label, eligibility_label_text
from app.matching.role_family import classify_job_role_family
from app.services.company_brand import company_logo_url
from app.models.company import Company
from app.models.enums import ListingStatus
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user import User
from app.schemas.job import JobListMeta, JobListResponse, JobOut
from app.schemas.match import JobWithMatchOut, MatchOut
from app.matching.resume_gate import profile_has_resume_evidence
from app.models.profile import Profile
from app.services.match_service import ensure_fresh_match
from app.services.source_health import collect_source_status_messages

router = APIRouter(prefix="/jobs", tags=["jobs"])

ALLOWED_PAGE_SIZES = {10, 15, 20}


def _sort_label(sort: str) -> str:
    labels = {
        "resume_match": "Sorted by best resume match",
        "preference_match": "Sorted by preference match",
        "newest": "Sorted by newest",
        "title": "Sorted by title",
        "best_match": "Sorted by best match",
    }
    return labels.get(sort, sort)


def _effective_sort(sort: str, has_resume: bool) -> str:
    if sort in ("auto", "best_match", ""):
        return "resume_match" if has_resume else "preference_match"
    return sort


# Defense-in-depth when stored india_scope is stale but location text is explicit.
_INDIA_ONLY_LOCATION_BLOCK_RE = (
    r"(riyadh|jeddah|saudi arabia|dubai|abu dhabi|\buae\b|singapore|"
    r"seattle|san francisco|menlo park|sunnyvale|new york|austin|"
    r"united states|\bu\.?s\.?a?\.?\b|united kingdom|\buk\b|canada|germany|australia)"
)


async def _jobs_list_meta(
    db: AsyncSession,
    *,
    matching_total: int,
    page: int,
    page_size: int,
    hidden_ineligible: int,
    sort_label: str,
    has_resume: bool = False,
) -> JobListMeta:
    db_total = await db.scalar(select(func.count()).select_from(Job)) or 0
    companies = await db.scalars(select(Company))
    total_pages = max(1, math.ceil(matching_total / page_size)) if matching_total else 0
    return JobListMeta(
        total=db_total,
        matching_total=matching_total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        visible_count=min(page_size, max(0, matching_total - (page - 1) * page_size)),
        sources_degraded=collect_source_status_messages(companies.all()),
        hidden_ineligible_count=hidden_ineligible,
        sort_label=sort_label,
        has_resume=has_resume,
    )


@router.get("/meta", response_model=JobListMeta)
async def jobs_meta(db: AsyncSession = Depends(get_db)) -> JobListMeta:
    active = await db.scalar(
        select(func.count()).select_from(Job).where(Job.listing_status == ListingStatus.active)
    )
    return await _jobs_list_meta(
        db,
        matching_total=active or 0,
        page=1,
        page_size=10,
        hidden_ineligible=0,
        sort_label=None,
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    company_id: uuid.UUID | None = Query(default=None),
    active_only: bool = Query(default=True),
    hide_ineligible: bool = Query(default=True),
    min_score: int | None = Query(default=None),
    sort: str = Query(default="auto"),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10),
    india_only: bool = Query(default=True),
    internships_only: bool = Query(default=True),
) -> JobListResponse:
    if page_size not in ALLOWED_PAGE_SIZES:
        raise HTTPException(status_code=400, detail="page_size must be 10, 15, or 20")

    profile = await db.scalar(select(Profile).where(Profile.user_id == user.id))
    has_resume = profile_has_resume_evidence(profile)

    filters = []
    if active_only:
        filters.append(Job.listing_status == ListingStatus.active)
        filters.append(Job.lifecycle_status == OPEN)
    if internships_only:
        filters.append(Job.employment_type == "internship")
    if company_id:
        filters.append(Job.company_id == company_id)
    if india_only:
        filters.append(Job.india_scope.in_(VERIFIED_INDIA_SCOPES))
        filters.append(
            or_(
                Job.location.is_(None),
                ~func.lower(func.coalesce(Job.location, "")).op("~")(_INDIA_ONLY_LOCATION_BLOCK_RE),
            )
        )
    if q:
        needle = f"%{q.lower()}%"
        filters.append(
            or_(
                func.lower(Job.title).like(needle),
                func.lower(Company.name).like(needle),
                func.lower(func.coalesce(Job.location, "")).like(needle),
            )
        )
    if hide_ineligible:
        filters.append(or_(JobMatch.id.is_(None), JobMatch.eligible.is_(True)))
    if min_score is not None:
        filters.append(JobMatch.score.is_not(None))
        filters.append(JobMatch.score >= min_score)

    hidden_ineligible = 0
    if hide_ineligible:
        hidden_stmt = (
            select(func.count())
            .select_from(Job)
            .join(Company, Company.id == Job.company_id)
            .join(JobMatch, (JobMatch.job_id == Job.id) & (JobMatch.user_id == user.id))
            .where(JobMatch.eligible.is_(False), *([Job.listing_status == ListingStatus.active] if active_only else []))
        )
        if company_id:
            hidden_stmt = hidden_stmt.where(Job.company_id == company_id)
        hidden_ineligible = await db.scalar(hidden_stmt) or 0

    count_stmt = (
        select(func.count())
        .select_from(Job)
        .join(Company, Company.id == Job.company_id)
        .outerjoin(JobMatch, (JobMatch.job_id == Job.id) & (JobMatch.user_id == user.id))
        .where(*filters)
    )
    matching_total = await db.scalar(count_stmt) or 0

    stmt = (
        select(Job, JobMatch, Company)
        .join(Company, Company.id == Job.company_id)
        .outerjoin(JobMatch, (JobMatch.job_id == Job.id) & (JobMatch.user_id == user.id))
        .where(*filters)
    )
    effective_sort = _effective_sort(sort, has_resume)
    if effective_sort == "resume_match":
        stmt = stmt.order_by(
            JobMatch.resume_match_available.desc(),
            JobMatch.score.desc().nulls_last(),
            JobMatch.preference_score.desc().nulls_last(),
            Job.title.asc(),
            Job.id.asc(),
        )
    elif effective_sort == "preference_match":
        stmt = stmt.order_by(
            JobMatch.preference_score.desc().nulls_last(),
            Job.title.asc(),
            Job.id.asc(),
        )
    elif effective_sort == "newest":
        stmt = stmt.order_by(Job.posted_at.desc().nulls_last(), Job.title.asc(), Job.id.asc())
    else:
        stmt = stmt.order_by(Job.title.asc(), Job.id.asc())

    offset = (page - 1) * page_size
    rows = (await db.execute(stmt.offset(offset).limit(page_size))).all()

    items: list[JobWithMatchOut] = []
    for job, match, company in rows:
        hard_eligible = match.eligible if match else None
        role_family = match.role_family if match and match.role_family else classify_job_role_family(job)
        top_reason = (match.top_reasons or [None])[0] if match else None
        label_key, label_detail = derive_eligibility_label(
            has_match=match is not None,
            has_resume=has_resume,
            hard_eligible=hard_eligible,
            eligibility_reasons=match.eligibility_reasons if match else None,
            requirements=match.requirements if match else None,
        )
        resume_score = match.score if match and match.resume_match_available else None
        items.append(
            JobWithMatchOut(
                id=job.id,
                company_id=job.company_id,
                company_name=company.name,
                title=job.title,
                location=job.location,
                listing_url=job.listing_url,
                apply_url=job.apply_url,
                deadline_at=job.deadline_at,
                posted_at=job.posted_at,
                score=resume_score,
                preference_score=match.preference_score if match else None,
                resume_match_available=bool(match and match.resume_match_available),
                eligible=hard_eligible,
                top_reason=top_reason,
                role_family=role_family,
                company_logo_url=company_logo_url(company.career_page_url),
                eligibility_label=eligibility_label_text(label_key),
                eligibility_detail=label_detail,
                location_display=display_location_label(job.india_scope or "unknown", job.location),
                career_level_label="Internship" if job.employment_type == "internship" else None,
            )
        )

    return JobListResponse(
        items=items,
        meta=await _jobs_list_meta(
            db,
            matching_total=matching_total,
            page=page,
            page_size=page_size,
            hidden_ineligible=hidden_ineligible,
            sort_label=_sort_label(effective_sort),
            has_resume=has_resume,
        ),
    )


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobOut:
    row = await db.execute(
        select(Job, Company).join(Company, Company.id == Job.company_id).where(Job.id == job_id)
    )
    result = row.first()
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    job, company = result
    return JobOut(
        id=job.id,
        company_id=job.company_id,
        company_name=company.name,
        title=job.title,
        location=job.location,
        remote_flag=job.remote_flag,
        listing_url=job.listing_url,
        apply_url=job.apply_url,
        listing_status=job.listing_status,
        description_sections=job.description_sections,
        posted_at=job.posted_at,
        deadline_at=job.deadline_at,
        last_seen_at=job.last_seen_at,
        last_verified_at=job.last_verified_at,
        lifecycle_status=job.lifecycle_status,
        requisition_id=job.requisition_id,
    )


@router.get("/{job_id}/match", response_model=MatchOut)
async def get_job_match(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchOut:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    match = await db.scalar(
        select(JobMatch).where(JobMatch.user_id == user.id, JobMatch.job_id == job_id)
    )
    profile = await db.scalar(select(Profile).where(Profile.user_id == user.id))
    has_resume = profile_has_resume_evidence(profile)
    if profile:
        match = await ensure_fresh_match(db, user.id, job, profile, match)
        await db.commit()
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not computed yet",
        )
    return MatchOut(
        job_id=job_id,
        score=match.score if match.resume_match_available else None,
        preference_score=match.preference_score,
        resume_match_available=bool(match.resume_match_available and has_resume),
        eligible=match.eligible,
        role_family=match.role_family or classify_job_role_family(job),
        eligibility_reasons=match.eligibility_reasons or [],
        factors=match.factors or [],
        requirements=match.requirements or [],
        gaps=match.gaps or [],
        top_reasons=match.top_reasons or [],
        computed_at=match.computed_at,
    )

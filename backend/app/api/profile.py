import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.user import User
from app.resume.extract_text import extract_text_from_bytes
from app.resume.parse import parse_resume_text
from app.schemas.profile import ProfileOut, ProfilePatch, ResumeStatusOut, ResumeUploadOut, SourceOut
from app.services.match_service import recompute_matches_for_user
from app.services.resume_profile import (
    clear_resume_derived_profile,
    mark_resume_entries,
    merge_resume_preferences,
)

router = APIRouter(tags=["profile"])

RESUME_DIR = Path(__file__).resolve().parents[2] / "data" / "resumes"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_RESUME_BYTES = 5 * 1024 * 1024


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    profile = await session_profile(db, user.id)
    return ProfileOut(
        skills=profile.skills or [],
        education=profile.education or [],
        experience=profile.experience or [],
        projects=profile.projects or [],
        preferences=profile.preferences or {},
        updated_at=profile.updated_at,
    )


@router.patch("/profile", response_model=ProfileOut)
async def patch_profile(
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    profile = await session_profile(db, user.id)
    if body.skills is not None:
        profile.skills = body.skills
    if body.education is not None:
        profile.education = body.education
    if body.experience is not None:
        profile.experience = body.experience
    if body.projects is not None:
        profile.projects = body.projects
    if body.preferences is not None:
        profile.preferences = {**(profile.preferences or {}), **body.preferences}
    profile.updated_at = datetime.now(UTC)
    await db.commit()
    await recompute_matches_for_user(db, user.id)
    return await get_profile(user=user, db=db)


@router.get("/resume", response_model=ResumeStatusOut)
async def get_resume_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeStatusOut:
    resume = await latest_resume(db, user.id)
    if not resume:
        return ResumeStatusOut(has_resume=False)
    return ResumeStatusOut(
        has_resume=True,
        resume_id=str(resume.id),
        filename=resume.filename,
        uploaded_at=resume.uploaded_at,
    )


@router.delete("/resume", status_code=204)
async def delete_resume(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    resume = await latest_resume(db, user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="No resume on file")
    profile = await session_profile(db, user.id)
    clear_resume_derived_profile(profile)
    profile.updated_at = datetime.now(UTC)
    try:
        Path(resume.storage_path).unlink(missing_ok=True)
    except OSError:
        pass
    await db.delete(resume)
    await db.commit()
    await recompute_matches_for_user(db, user.id)


@router.post("/resume", response_model=ResumeUploadOut)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeUploadOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Allowed types: PDF, DOCX, TXT")

    data = await file.read()
    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        raw_text = extract_text_from_bytes(file.filename, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if len(raw_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not extract enough text from resume")

    parsed = parse_resume_text(raw_text)
    profile = await session_profile(db, user.id)
    clear_resume_derived_profile(profile)
    profile.skills = (profile.skills or []) + mark_resume_entries([s.model_dump() for s in parsed.skills])
    profile.education = (profile.education or []) + mark_resume_entries(
        [e.model_dump() for e in parsed.education]
    )
    profile.experience = (profile.experience or []) + mark_resume_entries(
        [e.model_dump() for e in parsed.experience]
    )
    profile.projects = (profile.projects or []) + mark_resume_entries(
        [p.model_dump() for p in parsed.projects]
    )
    profile.preferences = merge_resume_preferences(profile.preferences or {}, parsed.preferences.model_dump())
    profile.updated_at = datetime.now(UTC)

    user_dir = RESUME_DIR / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    dest = user_dir / file.filename
    dest.write_bytes(data)

    old = await latest_resume(db, user.id)
    if old:
        try:
            Path(old.storage_path).unlink(missing_ok=True)
        except OSError:
            pass
        await db.delete(old)

    resume = Resume(
        user_id=user.id,
        filename=file.filename,
        storage_path=str(dest),
        raw_text=raw_text,
        parsed_at=datetime.now(UTC),
    )
    db.add(resume)
    await db.flush()
    resume_id = str(resume.id)
    await db.commit()

    matches = await recompute_matches_for_user(db, user.id)
    return ResumeUploadOut(
        resume_id=resume_id,
        filename=file.filename,
        parsed=True,
        skills_found=len(parsed.skills),
        matches_recomputed=matches,
    )


@router.get("/resume/source", response_model=SourceOut)
async def get_field_source(
    field_path: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SourceOut:
    """field_path examples: skills.0, experience.1, education.0"""
    profile = await session_profile(db, user.id)
    parts = field_path.split(".")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Use field_path like skills.0")
    section, idx_str = parts[0], parts[1]
    try:
        idx = int(idx_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid index") from None
    bucket = getattr(profile, section, None)
    if not isinstance(bucket, list) or idx >= len(bucket):
        raise HTTPException(status_code=404, detail="Field not found")
    entry = bucket[idx]
    source = entry.get("source") if isinstance(entry, dict) else None
    return SourceOut(field_path=field_path, source=source)


async def session_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


async def latest_resume(db: AsyncSession, user_id: uuid.UUID) -> Resume | None:
    return await db.scalar(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.uploaded_at.desc())
        .limit(1)
    )

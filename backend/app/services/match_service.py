from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.matching.engine import SCORING_VERSION, compute_match
from app.matching.fingerprint import job_content_fingerprint, profile_resume_fingerprint
from app.matching.resume_gate import profile_has_resume_evidence
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.profile import Profile


async def recompute_matches_for_user(session: AsyncSession, user_id, job_ids: list | None = None) -> int:
    profile = await session.scalar(select(Profile).where(Profile.user_id == user_id))
    if not profile:
        return 0

    resume_available = profile_has_resume_evidence(profile)
    profile_fp = profile_resume_fingerprint(profile)

    stmt = select(Job)
    if job_ids:
        stmt = stmt.where(Job.id.in_(job_ids))
    jobs = list((await session.scalars(stmt)).all())
    count = 0
    now = datetime.now(UTC)
    for job in jobs:
        result = compute_match(job, profile, resume_available=resume_available)
        job_fp = job_content_fingerprint(job)
        existing = await session.scalar(
            select(JobMatch).where(JobMatch.user_id == user_id, JobMatch.job_id == job.id)
        )
        if existing:
            existing.score = result.score
            existing.preference_score = result.preference_score
            existing.resume_match_available = result.resume_match_available
            existing.eligible = result.eligible
            existing.eligibility_reasons = result.eligibility_reasons
            existing.factors = result.factors
            existing.requirements = result.requirements
            existing.gaps = result.gaps
            existing.top_reasons = result.top_reasons
            existing.role_family = result.role_family
            existing.computed_at = now
            existing.scoring_version = result.scoring_version
            existing.job_content_fingerprint = job_fp
            existing.profile_resume_fingerprint = profile_fp
        else:
            session.add(
                JobMatch(
                    user_id=user_id,
                    job_id=job.id,
                    score=result.score,
                    preference_score=result.preference_score,
                    resume_match_available=result.resume_match_available,
                    eligible=result.eligible,
                    eligibility_reasons=result.eligibility_reasons,
                    factors=result.factors,
                    requirements=result.requirements,
                    gaps=result.gaps,
                    top_reasons=result.top_reasons,
                    role_family=result.role_family,
                    computed_at=now,
                    scoring_version=result.scoring_version,
                    job_content_fingerprint=job_fp,
                    profile_resume_fingerprint=profile_fp,
                )
            )
        count += 1
    await session.commit()
    return count


async def ensure_fresh_match(
    session: AsyncSession,
    user_id,
    job: Job,
    profile: Profile,
    match: JobMatch | None,
) -> JobMatch | None:
    """Recompute a single match when scoring version or fingerprints are stale."""
    if not profile_has_resume_evidence(profile):
        return match
    profile_fp = profile_resume_fingerprint(profile)
    job_fp = job_content_fingerprint(job)
    if match and match.scoring_version == SCORING_VERSION:
        if match.job_content_fingerprint == job_fp and match.profile_resume_fingerprint == profile_fp:
            return match
    result = compute_match(job, profile, resume_available=True)
    now = datetime.now(UTC)
    if match:
        match.score = result.score
        match.preference_score = result.preference_score
        match.resume_match_available = result.resume_match_available
        match.eligible = result.eligible
        match.eligibility_reasons = result.eligibility_reasons
        match.factors = result.factors
        match.requirements = result.requirements
        match.gaps = result.gaps
        match.top_reasons = result.top_reasons
        match.role_family = result.role_family
        match.computed_at = now
        match.scoring_version = result.scoring_version
        match.job_content_fingerprint = job_fp
        match.profile_resume_fingerprint = profile_fp
        return match
    new_match = JobMatch(
        user_id=user_id,
        job_id=job.id,
        score=result.score,
        preference_score=result.preference_score,
        resume_match_available=result.resume_match_available,
        eligible=result.eligible,
        eligibility_reasons=result.eligibility_reasons,
        factors=result.factors,
        requirements=result.requirements,
        gaps=result.gaps,
        top_reasons=result.top_reasons,
        role_family=result.role_family,
        computed_at=now,
        scoring_version=result.scoring_version,
        job_content_fingerprint=job_fp,
        profile_resume_fingerprint=profile_fp,
    )
    session.add(new_match)
    return new_match

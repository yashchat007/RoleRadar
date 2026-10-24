"""Fingerprints for stale match invalidation."""

import hashlib
import json

from app.matching.engine import SCORING_VERSION
from app.models.job import Job
from app.models.profile import Profile


def job_content_fingerprint(job: Job) -> str:
    payload = {
        "title": job.title,
        "location": job.location,
        "content_hash": job.content_hash,
        "description_sections": job.description_sections,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def profile_resume_fingerprint(profile: Profile) -> str:
    payload = {
        "skills": profile.skills,
        "experience": profile.experience,
        "education": profile.education,
        "projects": profile.projects,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def match_is_stale(
    *,
    scoring_version: int | None,
    job_fingerprint: str | None,
    profile_fingerprint: str | None,
    current_job_fp: str,
    current_profile_fp: str,
) -> bool:
    if scoring_version != SCORING_VERSION:
        return True
    if not job_fingerprint or job_fingerprint != current_job_fp:
        return True
    if not profile_fingerprint or profile_fingerprint != current_profile_fp:
        return True
    return False

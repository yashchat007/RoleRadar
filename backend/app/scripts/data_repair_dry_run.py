"""
Preview and apply narrowly scoped data-quality repairs (no job deletes).

Usage (from backend/):
  set PYTHONPATH=.
  python -m app.scripts.data_repair_dry_run
  python -m app.scripts.data_repair_dry_run --apply
"""

import argparse
import asyncio
import re

from sqlalchemy import func, select

from app.database import SessionLocal, engine
from app.discovery.job_title import normalize_job_title
from app.discovery.lifecycle_status import OPEN, POSSIBLY_CLOSED
from app.matching.requirements import extract_requirement_phrases
from app.models.enums import ListingStatus
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user import User
from app.scripts.schema_patches import apply_schema_patches
from app.services.match_service import recompute_matches_for_user


def _title_polluted(title: str) -> bool:
    """Leading 10+ digit token before human-readable title (Google-style anchor text)."""
    return bool(re.match(r"^\d{10,}\s+\S", title or ""))


async def dry_run() -> dict:
    report: dict = {}
    async with SessionLocal() as session:
        jobs = list((await session.scalars(select(Job))).all())
        polluted = [j for j in jobs if _title_polluted(j.title)]
        report["titles_polluted_by_requisition_prefix"] = len(polluted)
        report["title_examples"] = [j.title[:80] for j in polluted[:5]]

        would_repair: list[tuple[str, str, str | None]] = []
        for j in polluted:
            display, req_id = normalize_job_title(j.title, j.listing_url)
            if display != j.title:
                would_repair.append((j.title[:100], display[:100], req_id))
        report["titles_that_would_change"] = len(would_repair)
        report["title_before_after_samples"] = [
            {"before": b, "after": a, "requisition_id": r} for b, a, r in would_repair[:5]
        ]

        malformed_reqs = 0
        for j in jobs:
            display, _ = normalize_job_title(j.title, j.listing_url)
            for phrase in extract_requirement_phrases(j):
                if phrase.strip().lower() == display.strip().lower():
                    malformed_reqs += 1
                    break
        report["jobs_with_title_as_requirement"] = malformed_reqs

        dup_keys = await session.execute(
            select(Job.company_id, Job.source_job_key, func.count())
            .group_by(Job.company_id, Job.source_job_key)
            .having(func.count() > 1)
        )
        report["duplicate_source_job_keys"] = len(dup_keys.all())

        report["possibly_closed_jobs"] = (
            await session.scalar(
                select(func.count()).select_from(Job).where(Job.lifecycle_status == POSSIBLY_CLOSED)
            )
            or 0
        )
        report["active_open_jobs"] = (
            await session.scalar(
                select(func.count()).select_from(Job).where(
                    Job.listing_status == ListingStatus.active,
                    Job.lifecycle_status == OPEN,
                )
            )
            or 0
        )

        report["internships_india_scope_unknown"] = (
            await session.scalar(
                select(func.count()).select_from(Job).where(
                    Job.employment_type == "internship",
                    Job.india_scope == "unknown",
                )
            )
            or 0
        )

        report["job_matches_stale_resume_scores"] = (
            await session.scalar(
                select(func.count()).select_from(JobMatch).where(
                    JobMatch.score.is_not(None),
                    JobMatch.resume_match_available.is_(False),
                )
            )
            or 0
        )
        report["job_matches_with_preference_score"] = (
            await session.scalar(
                select(func.count()).select_from(JobMatch).where(JobMatch.preference_score.is_not(None))
            )
            or 0
        )

    return report


async def apply_repairs() -> int:
    """
    1. Schema patches (idempotent DDL).
    2. Strip requisition prefix from polluted titles only; set requisition_id when derived.
    3. Null resume match score where resume_match_available is false (keeps preference_score).
    4. Recompute all user matches from current profiles (no job/lifecycle changes).
    """
    async with engine.begin() as conn:
        await apply_schema_patches(conn)

    titles_changed = 0
    scores_cleared = 0
    async with SessionLocal() as session:
        jobs = list((await session.scalars(select(Job))).all())
        for job in jobs:
            if not _title_polluted(job.title):
                continue
            display, req_id = normalize_job_title(job.title, job.listing_url)
            if display != job.title:
                job.title = display
                titles_changed += 1
            if req_id and not job.requisition_id:
                job.requisition_id = req_id

        matches = list((await session.scalars(select(JobMatch))).all())
        for m in matches:
            if not m.resume_match_available and m.score is not None:
                m.score = None
                scores_cleared += 1

        await session.commit()

    users_recomputed = 0
    async with SessionLocal() as session:
        users = list((await session.scalars(select(User))).all())
        for user in users:
            await recompute_matches_for_user(session, user.id)
            users_recomputed += 1

    print(f"Applied: titles_changed={titles_changed}, stale_scores_cleared={scores_cleared}, users_recomputed={users_recomputed}")
    return titles_changed


async def main(apply: bool) -> None:
    report = await dry_run()
    print("=== Data repair dry-run ===")
    for key, val in report.items():
        print(f"{key}: {val}")
    if apply:
        print("Applying scoped repairs (polluted titles only, stale resume scores, then match recompute)...")
        await apply_repairs()
        print("Done. Post-repair dry-run:")
        after = await dry_run()
        for key, val in after.items():
            print(f"{key}: {val}")
    else:
        print("No changes applied. Pass --apply to run idempotent repairs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.apply))

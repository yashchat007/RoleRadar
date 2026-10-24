"""Idempotent PostgreSQL column patches for dev DBs created before model changes."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def apply_schema_patches(conn: AsyncConnection) -> None:
    statements = [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requisition_id VARCHAR(64)",
        "ALTER TABLE job_matches ALTER COLUMN score DROP NOT NULL",
        "ALTER TABLE job_matches ADD COLUMN IF NOT EXISTS preference_score INTEGER",
        "ALTER TABLE job_matches ADD COLUMN IF NOT EXISTS resume_match_available BOOLEAN DEFAULT FALSE",
        "ALTER TABLE job_matches ADD COLUMN IF NOT EXISTS scoring_version INTEGER",
        "ALTER TABLE job_matches ADD COLUMN IF NOT EXISTS job_content_fingerprint VARCHAR(32)",
        "ALTER TABLE job_matches ADD COLUMN IF NOT EXISTS profile_resume_fingerprint VARCHAR(32)",
    ]
    for stmt in statements:
        await conn.execute(text(stmt))

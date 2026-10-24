"""Deterministic employment-type classification from official listing evidence."""

from __future__ import annotations

import re

from app.discovery.types import NormalizedJob
from app.models.job import Job

INTERNSHIP_PATTERNS = (
    r"\bintern(ship)?\b",
    r"\bco-?op\b",
    r"\bsummer analyst\b",
    r"\bsummer associate\b",
    r"\bplacement student\b",
    r"\banalyst development program\b",
    r"\bgraduate program\b",
    r"\bstudent program\b",
)

FULL_TIME_PATTERNS = (
    r"\bfull[- ]?time\b",
    r"\bfte\b",
    r"\bpermanent (?:position|role)\b",
)

# Title-only seniority without intern → full-time (not internship).
SENIOR_TITLE = re.compile(
    r"\b(senior|staff|principal|director|vp|vice president|lead manager|manager,?)\b",
    re.I,
)


def _blob(job: NormalizedJob | Job) -> str:
    title = job.title or ""
    desc = job.description_sections if isinstance(job.description_sections, dict) else {}
    summary = str(desc.get("summary", ""))
    meta = getattr(job, "location_meta", None) or {}
    evidence = str(meta.get("evidence", "")) if isinstance(meta, dict) else ""
    return f"{title}\n{summary}\n{evidence}".lower()


def _employment_type_from_evidence(text: str) -> str | None:
    m = re.search(r"employment type\s*[:\s]*(full[- ]?time|internship|part[- ]?time|contract)", text, re.I)
    if m:
        val = m.group(1).lower().replace(" ", "")
        if "intern" in val:
            return "internship"
        if "full" in val:
            return "full_time"
        if "contract" in val:
            return "contract"
    if re.search(r"\bstudent program\b|\bsummer analyst program\b", text, re.I):
        return "internship"
    return None


def classify_employment_type(job: NormalizedJob | Job) -> str:
    """
    Returns: internship | full_time | contract | unknown
    Does not treat graduate / university / early career alone as internship.
    """
    meta = getattr(job, "location_meta", None) or {}
    if isinstance(meta, dict) and meta.get("employment_type_hint"):
        return str(meta["employment_type_hint"])

    text = _blob(job)
    title = (job.title or "").lower()

    hinted = _employment_type_from_evidence(text)
    if hinted:
        return hinted

    for pat in INTERNSHIP_PATTERNS:
        if re.search(pat, text, re.I):
            return "internship"

    for pat in FULL_TIME_PATTERNS:
        if re.search(pat, text, re.I):
            return "full_time"

    if SENIOR_TITLE.search(title) and not re.search(r"\bintern", title, re.I):
        return "full_time"

    if re.search(r"\b(software engineer|sde|swe)\b", title) and "intern" not in title:
        return "full_time"

    return "unknown"

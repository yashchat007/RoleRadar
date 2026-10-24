import re

from app.discovery.job_title import normalize_job_title, title_is_requirement_noise
from app.models.job import Job

REQUIREMENT_PATTERNS = [
    re.compile(r"\b(\d+)\+?\s*years?\b", re.I),
    re.compile(r"\b(bachelor|master|phd|doctorate|degree)\b", re.I),
    re.compile(r"\b(python|java|javascript|typescript|react|aws|sql|go|rust|c\+\+)\b", re.I),
    re.compile(r"\b(visa|sponsorship|authorized to work|citizen)\b", re.I),
    re.compile(r"\b(must|required|minimum|qualification)\b", re.I),
]

ROLE_FAMILY_LABELS = frozenset(
    s.lower()
    for s in (
        "Software Engineering",
        "Data Science",
        "Product Management",
        "Research",
        "Finance",
        "Operations",
        "Design",
        "Hardware",
        "Other",
    )
)


def job_text_blob(job: Job, *, include_title: bool = True) -> str:
    parts: list[str] = []
    if include_title:
        display, _ = normalize_job_title(job.title, job.listing_url)
        parts.append(display)
    if job.location:
        parts.append(job.location)
    sections = job.description_sections or {}
    for key in ("requirements", "summary", "description", "WhatYouDo", "qualifications"):
        val = sections.get(key)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            parts.extend(str(v) for v in val)
    return "\n".join(parts)


def posting_requirement_blob(job: Job) -> str:
    """Official posting text only — excludes title used as fake requirement."""
    sections = job.description_sections or {}
    parts: list[str] = []
    for key in ("requirements", "description", "WhatYouDo", "qualifications"):
        val = sections.get(key)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            parts.extend(str(v) for v in val)
    summary = sections.get("summary")
    if isinstance(summary, str) and summary.lower() not in (job.title or "").lower():
        display, _ = normalize_job_title(job.title, job.listing_url)
        if summary.strip().lower() != display.strip().lower():
            parts.append(summary)
    return "\n".join(parts)


def extract_requirement_phrases(job: Job) -> list[str]:
    display_title, _ = normalize_job_title(job.title, job.listing_url)
    blob = posting_requirement_blob(job)
    if not blob.strip():
        return []

    phrases: list[str] = []
    for line in re.split(r"[\n•;]", blob):
        line = line.strip(" -")
        if title_is_requirement_noise(line, display_title):
            continue
        if display_title.lower() in line.lower() and len(line) < len(display_title) + 30:
            continue
        if line.lower() in ROLE_FAMILY_LABELS:
            continue
        if not any(p.search(line) for p in REQUIREMENT_PATTERNS):
            if len(line) > 100:
                continue
        phrases.append(line)

    seen: set[str] = set()
    unique: list[str] = []
    for p in phrases:
        key = re.sub(r"\s+", " ", p.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique[:25]

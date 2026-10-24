"""Normalize official job titles and separate requisition IDs from display text."""

from __future__ import annotations

import re

from app.discovery.normalize import requisition_id_from_url

# Long numeric prefix before human title (e.g. Google link anchor text).
_REQUISITION_TITLE_PREFIX = re.compile(r"^(\d{12,})\s+(.+)$")
# Shorter numeric-only tokens at start (10+ digits).
_REQUISITION_TITLE_PREFIX_SHORT = re.compile(r"^(\d{10,})\s+(.+)$")


def normalize_job_title(title: str, listing_url: str | None = None) -> tuple[str, str | None]:
    """
    Return (display_title, requisition_id).
    Strips a leading requisition ID only when it matches URL evidence or is clearly numeric-only prefix.
    """
    raw = (title or "").strip()
    if not raw:
        return raw, requisition_id_from_url(listing_url or "") if listing_url else None

    url_req = requisition_id_from_url(listing_url or "") if listing_url else None

    for pattern in (_REQUISITION_TITLE_PREFIX, _REQUISITION_TITLE_PREFIX_SHORT):
        m = pattern.match(raw)
        if m:
            prefix, rest = m.group(1), m.group(2).strip()
            if url_req and prefix != url_req:
                continue
            if rest and not rest.isdigit():
                return rest, url_req or prefix

    if url_req and raw.startswith(url_req):
        remainder = raw[len(url_req) :].lstrip(" -–—:|")
        if remainder and not remainder.isdigit():
            return remainder, url_req

    return raw, url_req


def title_is_requirement_noise(text: str, display_title: str) -> bool:
    """True if a requirement line is really title/metadata, not a posting requirement."""
    t = text.strip()
    if not t or len(t) < 4:
        return True
    if t.lower() == display_title.strip().lower():
        return True
    if re.fullmatch(r"\d{8,}", t):
        return True
    if re.match(r"^https?://", t, re.I):
        return True
    return False

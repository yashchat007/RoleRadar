"""Stable keys for adapter search facets (not full-company inventories)."""

import hashlib
from typing import Sequence


def discovery_scope_key(adapter_key: str, search_urls: Sequence[str]) -> str:
    normalized = "|".join(sorted(u.strip() for u in search_urls if u.strip()))
    payload = f"{adapter_key}\n{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def scope_keys_match(job_scope: str | None, scan_scope: str | None) -> bool:
    """Miss logic applies only when the job was discovered under the same facet as this scan."""
    if not scan_scope:
        return True
    if not job_scope:
        return False
    return job_scope == scan_scope

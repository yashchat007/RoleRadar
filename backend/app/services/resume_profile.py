"""Merge and clear resume-derived profile fields without touching manual edits."""

from __future__ import annotations

from typing import Any

from app.models.profile import Profile

RESUME_PREF_KEYS = ("graduation_year", "requires_visa_sponsorship", "preferred_locations", "open_to_remote")


def mark_resume_entries(entries: list[Any]) -> list[dict]:
    out: list[dict] = []
    for entry in entries:
        if isinstance(entry, dict):
            row = dict(entry)
            row["from_resume"] = True
            out.append(row)
        else:
            out.append({"name": str(entry), "from_resume": True})
    return out


def clear_resume_derived_profile(profile: Profile) -> None:
    for field in ("skills", "education", "experience", "projects"):
        bucket = getattr(profile, field) or []
        setattr(
            profile,
            field,
            [x for x in bucket if isinstance(x, dict) and not x.get("from_resume")],
        )
    prefs = dict(profile.preferences or {})
    resume_keys = prefs.pop("_resume_preference_keys", []) or []
    for key in resume_keys:
        prefs.pop(key, None)
    profile.preferences = prefs


def merge_resume_preferences(existing: dict, parsed_prefs: dict) -> dict:
    merged = dict(existing or {})
    resume_keys: list[str] = list(merged.get("_resume_preference_keys") or [])
    for key in RESUME_PREF_KEYS:
        if key in parsed_prefs and parsed_prefs[key] is not None:
            merged[key] = parsed_prefs[key]
            if key not in resume_keys:
                resume_keys.append(key)
    merged["_resume_preference_keys"] = resume_keys
    return merged

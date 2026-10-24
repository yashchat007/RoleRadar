"""Skill overlap with evidence — avoids substring false positives (e.g. 'git' in unrelated words)."""

import re

from app.models.profile import Profile

# Location/geo tokens that should not count as technical skill hits in postings.
_NON_SKILL_TOKENS = frozenset(
    {
        "india",
        "remote",
        "usa",
        "uk",
        "canada",
        "europe",
        "germany",
        "australia",
        "singapore",
        "japan",
        "china",
        "dutch",
        "french",
        "spanish",
        "korean",
        "english",
        "speaking",
    }
)


def skill_names(profile: Profile) -> set[str]:
    names: set[str] = set()
    for s in profile.skills or []:
        if isinstance(s, dict):
            names.add(s.get("name", "").lower().strip())
        else:
            names.add(str(s).lower().strip())
    for p in profile.projects or []:
        if isinstance(p, dict):
            for sk in p.get("skills") or []:
                names.add(str(sk).lower().strip())
    return {n for n in names if n and n not in _NON_SKILL_TOKENS}


def skill_appears_in_text(skill: str, text: str) -> bool:
    skill = skill.lower().strip()
    if not skill or skill in _NON_SKILL_TOKENS:
        return False
    if len(skill) <= 2:
        return False
    if skill == "go":
        return bool(re.search(r"\bgo(lang)?\b", text, re.I))
    if skill == "r":
        return bool(re.search(r"\bR\b", text))
    return bool(re.search(rf"\b{re.escape(skill)}\b", text, re.I))


def skill_hits_in_posting(skills: set[str], blob: str) -> list[str]:
    lower = blob.lower()
    hits: list[str] = []
    for sk in sorted(skills):
        if skill_appears_in_text(sk, lower):
            hits.append(sk)
    return hits

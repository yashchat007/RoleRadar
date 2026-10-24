"""Classify postings into role families for relevance scoring (not eligibility)."""

from __future__ import annotations

import re
from enum import Enum

from app.matching.requirements import job_text_blob
from app.models.job import Job
from app.models.profile import Profile

ROLE_FAMILY_ORDER = [
    "Software Engineering",
    "Data/ML",
    "Cybersecurity",
    "IT/Infrastructure",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Customer Success",
    "Finance",
    "Other",
]

DEFAULT_TECHNICAL_FAMILIES = [
    "Software Engineering",
    "Data/ML",
    "Cybersecurity",
    "IT/Infrastructure",
]


class RoleFamily(str, Enum):
    software_engineering = "Software Engineering"
    data_ml = "Data/ML"
    cybersecurity = "Cybersecurity"
    it_infrastructure = "IT/Infrastructure"
    product = "Product"
    design = "Design"
    sales = "Sales"
    marketing = "Marketing"
    customer_success = "Customer Success"
    finance = "Finance"
    other = "Other"


_TITLE_RULES: list[tuple[RoleFamily, re.Pattern[str]]] = [
    (RoleFamily.sales, re.compile(r"\b(sales|account executive|ae\b|business development|bdr\b|sdr\b)\b", re.I)),
    (
        RoleFamily.customer_success,
        re.compile(
            r"\b(customer success|client success|digital success|solution sales|success manager|csm\b)\b",
            re.I,
        ),
    ),
    (RoleFamily.marketing, re.compile(r"\b(marketing|growth|brand|content marketing|demand gen)\b", re.I)),
    (RoleFamily.finance, re.compile(r"\b(finance|accounting|fp&a|financial analyst)\b", re.I)),
    (RoleFamily.design, re.compile(r"\b(designer|ux\b|ui\b|product design|visual design)\b", re.I)),
    (RoleFamily.product, re.compile(r"\b(product manager|product owner|pm\b)\b", re.I)),
    (RoleFamily.data_ml, re.compile(r"\b(data scientist|machine learning|ml engineer|ai engineer|analytics)\b", re.I)),
    (RoleFamily.cybersecurity, re.compile(r"\b(security engineer|cyber|infosec|soc analyst)\b", re.I)),
    (RoleFamily.it_infrastructure, re.compile(r"\b(devops|sre\b|site reliability|systems admin|it support)\b", re.I)),
    (
        RoleFamily.software_engineering,
        re.compile(
            r"\b(software engineer|swe\b|developer|engineer|intern\b|backend|frontend|full[- ]?stack)\b",
            re.I,
        ),
    ),
]


def classify_job_role_family(job: Job) -> str:
    title = job.title or ""
    blob = f"{title}\n{job_text_blob(job)}"
    for family, pattern in _TITLE_RULES:
        if pattern.search(title) or (family != RoleFamily.software_engineering and pattern.search(blob[:500])):
            return family.value
    if re.search(r"\bengineer\b", title, re.I):
        return RoleFamily.software_engineering.value
    return RoleFamily.other.value


def preferred_role_families(preferences: dict) -> list[str]:
    raw = preferences.get("preferred_role_families")
    if isinstance(raw, list) and raw:
        return [str(x) for x in raw]
    return list(DEFAULT_TECHNICAL_FAMILIES)


def profile_signals_technical(profile: Profile, preferences: dict) -> bool:
    prefs = preferences or {}
    if prefs.get("target_profile") == "technical":
        return True
    exp_titles = " ".join(
        (e.get("title") or "") for e in (profile.experience or []) if isinstance(e, dict)
    ).lower()
    if any(
        tok in exp_titles
        for tok in ("engineer", "developer", "intern", "swe", "software", "data scientist")
    ):
        return True
    skills = {s.get("name", "").lower() for s in (profile.skills or []) if isinstance(s, dict)}
    tech_markers = {"python", "java", "javascript", "typescript", "react", "sql", "c++", "golang", "rust"}
    return len(skills & tech_markers) >= 2


def role_relevance_score(
    job_family: str, job_title: str, profile: Profile, preferences: dict
) -> tuple[int, list[str]]:
    """0–100 relevance; separate from hard eligibility."""
    title_lower = (job_title or "").lower()
    preferred = {f.lower() for f in preferred_role_families(preferences)}
    family_key = job_family.lower()
    evidence: list[str] = []

    if family_key in preferred:
        evidence.append(f"Role family '{job_family}' is in your preferred families")
        base = 95
    elif job_family in (RoleFamily.sales.value, RoleFamily.customer_success.value, RoleFamily.marketing.value):
        if profile_signals_technical(profile, preferences):
            evidence.append(
                f"'{job_family}' is outside your preferred technical families; weak fit for your profile"
            )
            base = 12
        else:
            evidence.append(f"Role family '{job_family}' is not in your preferred list")
            base = 35
    elif job_family == RoleFamily.other.value:
        evidence.append("Role family could not be classified confidently from the posting title")
        base = 45
    else:
        evidence.append(f"Role family '{job_family}' is not among your preferred families")
        base = 40

    target_level = (preferences or {}).get("target_level")
    posting_title = (job_title or "").lower()
    internship_like = re.search(r"\b(intern|internship|graduate|new grad|university)\b", posting_title, re.I)
    if target_level in ("internship", "new_grad", "entry") and internship_like:
        base = min(100, base + 10)
        evidence.append("Posting level aligns with your target level preference")

    if target_level in ("internship", "new_grad", "entry") and re.search(
        r"\b(senior|staff|principal|director|vp |vice president)\b", title_lower
    ):
        base = min(base, 18)
        evidence.append("Senior-level title does not match your internship/entry target")

    return base, evidence

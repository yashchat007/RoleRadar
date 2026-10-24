from __future__ import annotations

import re
from dataclasses import dataclass

from app.matching.eligibility import check_eligibility
from app.matching.requirements import extract_requirement_phrases, job_text_blob
from app.matching.role_family import classify_job_role_family, role_relevance_score
from app.matching.skills import skill_appears_in_text, skill_hits_in_posting, skill_names
from app.models.job import Job
from app.models.profile import Profile

# Resume match uses posting + resume evidence only (preferences live in preference_score).
SCORING_VERSION = 2

RESUME_WEIGHTS = {
    "role_relevance": 0.30,
    "skills": 0.45,
    "experience": 0.15,
    "education": 0.10,
}

PREFERENCE_WEIGHTS = {
    "role_relevance": 0.55,
    "location": 0.30,
    "preferences": 0.15,
}


@dataclass
class MatchResult:
    score: int | None
    preference_score: int | None
    resume_match_available: bool
    eligible: bool
    eligibility_reasons: list[str]
    role_family: str
    factors: list[dict]
    requirements: list[dict]
    gaps: list[dict]
    top_reasons: list[str]
    scoring_version: int = SCORING_VERSION


def _years_experience(profile: Profile) -> float:
    total = 0.0
    for exp in profile.experience or []:
        if not isinstance(exp, dict) or not exp.get("from_resume"):
            continue
        start = exp.get("start_year")
        end = exp.get("end_year")
        if start and end and end >= start:
            total += end - start
        elif start:
            total += 1.0
    return total


def _education_level(profile: Profile) -> int:
    score = 0
    for ed in profile.education or []:
        if not isinstance(ed, dict) or not ed.get("from_resume"):
            continue
        line = (ed.get("institution") or "") + " " + (ed.get("degree") or "")
        if re.search(r"phd|doctorate", line, re.I):
            score = max(score, 3)
        elif re.search(r"master", line, re.I):
            score = max(score, 2)
        elif re.search(r"bachelor|b\.s|b\.a", line, re.I):
            score = max(score, 1)
    return score


def _resume_skills(profile: Profile) -> set[str]:
    return {
        s.get("name", "")
        for s in (profile.skills or [])
        if isinstance(s, dict) and s.get("from_resume") and s.get("name")
    }


def _evidence_for_skill(skill: str, profile: Profile) -> str | None:
    for s in profile.skills or []:
        if not isinstance(s, dict) or not s.get("from_resume"):
            continue
        if s.get("name", "").lower() == skill.lower():
            src = s.get("source") or {}
            quote = src.get("quote")
            if quote:
                return f"{s.get('name')}, mentioned in your resume: \"{quote}\""
            return f"{s.get('name')} listed from your resume"
    for p in profile.projects or []:
        if not isinstance(p, dict) or not p.get("from_resume"):
            continue
        if skill.lower() in (p.get("name") or "").lower() or skill.lower() in (p.get("description") or "").lower():
            return f"{skill}, referenced in project '{p.get('name')}'"
    return None


def _requirement_status(
    phrase: str,
    profile: Profile,
    skills: set[str],
    blob: str,
    *,
    resume_available: bool,
) -> tuple[str, str | None]:
    if not resume_available:
        return "not_in_profile", "Upload a resume to compare against this requirement"

    lower = phrase.lower()
    for sk in skills:
        if skill_appears_in_text(sk, lower):
            ev = _evidence_for_skill(sk, profile)
            return "met", ev or f"{sk.title()} listed in your profile with resume evidence"
    year_match = re.search(r"(\d+)\+?\s*years?", lower)
    if year_match:
        needed = int(year_match.group(1))
        have = _years_experience(profile)
        if have <= 0:
            return "unclear", "Years of experience not established from your resume"
        if have >= needed:
            return "met", f"About {have:.0f} years of experience on your resume"
        if have >= needed - 1:
            return "partial", f"Resume shows ~{have:.0f} years; posting asks for {needed}+"
        return "missing", f"Resume shows ~{have:.0f} years; posting asks for {needed}+"
    if re.search(r"bachelor|master|phd", lower):
        lvl = _education_level(profile)
        if lvl >= 1:
            return "met", "Education section on your resume"
        return "unclear", "Education requirements not clearly matched in resume"
    if re.search(r"visa|sponsorship|authorized to work|citizen", lower):
        return "unclear", "Work authorization requirement — confirm against your profile"
    return "unclear", None


def _preference_location_score(job: Job, prefs: dict) -> tuple[int, list[str]]:
    location_score = 50
    evidence = [job.location or "No location listed on posting"]
    if job.remote_flag:
        location_score = 100
        evidence = ["Posting is marked remote"]
    elif job.location:
        loc = job.location.lower()
        if prefs.get("open_to_remote") and "remote" in loc:
            location_score = 100
            evidence = ["Remote-friendly location matches your preference"]
        elif prefs.get("preferred_locations"):
            if any(p.lower() in loc for p in prefs["preferred_locations"]):
                location_score = 100
                evidence = ["Location matches a preferred location in your profile"]
            else:
                location_score = 25
                evidence = ["Location outside your preferred locations"]
    return location_score, evidence


def _posting_skill_targets(job: Job) -> set[str]:
    """Skills explicitly mentioned in requirements lines of the posting."""
    targets: set[str] = set()
    for phrase in extract_requirement_phrases(job):
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,24}", phrase):
            if token.lower() in {"and", "or", "the", "with", "year", "years", "degree"}:
                continue
            if len(token) >= 2:
                targets.add(token.lower())
    return targets


def _skills_score(
    job: Job, blob: str, resume_skills: set[str]
) -> tuple[int, list[str], list[str]]:
    hits = skill_hits_in_posting(resume_skills, blob)
    posting_targets = _posting_skill_targets(job)
    if posting_targets:
        matched_targets = [t for t in posting_targets if any(skill_appears_in_text(sk, t) for sk in resume_skills)]
        ratio = len(matched_targets) / max(1, len(posting_targets))
        score = int(round(min(1.0, ratio) * 100))
        evidence = (
            [f"Matched posting skill terms: {', '.join(matched_targets[:6])}"]
            if matched_targets
            else ["No overlap with skill terms called out in the posting"]
        )
        return score, evidence, hits
    if resume_skills:
        ratio = len(hits) / max(1, min(len(resume_skills), 12))
        score = int(round(min(1.0, ratio) * 100))
        evidence = (
            [f"Resume skills found in posting: {', '.join(hits[:5])}"]
            if hits
            else ["No resume skill keywords matched in posting text"]
        )
        return score, evidence, hits
    return 0, ["No resume skills to compare"], []


def _experience_score(job: Job, blob: str, years: float) -> tuple[int, list[str]]:
    m = re.search(r"(\d+)\+?\s*years?", blob.lower())
    if m:
        needed = int(m.group(1))
        if years <= 0:
            return 0, ["Years of experience not established from resume"]
        pct = min(1.0, years / needed)
        return int(round(pct * 100)), [f"Posting asks for {needed}+ years; resume shows ~{years:.0f}"]
    if re.search(r"\bintern(ship)?\b", (job.title or "") + blob, re.I):
        if years > 0:
            return 85, ["Internship posting with prior experience on resume"]
        return 40, ["Internship posting — limited experience on resume"]
    return 0, ["No explicit experience requirement in posting — not scored as a match"]


def compute_preference_match(job: Job, profile: Profile) -> tuple[int, list[dict], list[str]]:
    prefs = profile.preferences if isinstance(profile.preferences, dict) else {}
    role_family = classify_job_role_family(job)
    role_score, role_evidence = role_relevance_score(role_family, job.title, profile, prefs)
    loc_score, loc_evidence = _preference_location_score(job, prefs)
    pref_score = 85 if prefs.get("open_to_remote") or prefs.get("preferred_locations") else 60

    factors = [
        {
            "name": "Role relevance",
            "weight": PREFERENCE_WEIGHTS["role_relevance"],
            "score": role_score,
            "evidence": role_evidence,
            "kind": "preference",
        },
        {
            "name": "Location",
            "weight": PREFERENCE_WEIGHTS["location"],
            "score": loc_score,
            "evidence": loc_evidence,
            "kind": "preference",
        },
        {
            "name": "Preferences",
            "weight": PREFERENCE_WEIGHTS["preferences"],
            "score": pref_score,
            "evidence": ["Based on profile preferences (not resume skills)"],
            "kind": "preference",
        },
    ]
    weighted = sum(f["weight"] * f["score"] for f in factors)
    score = int(round(weighted))
    reasons = [f"Preference match uses role family ({role_family}) and location preferences only"]
    if role_score >= 70:
        reasons.append(role_evidence[0])
    return score, factors, reasons


def compute_match(job: Job, profile: Profile, *, resume_available: bool) -> MatchResult:
    prefs = profile.preferences if isinstance(profile.preferences, dict) else {}
    eligible, eligibility_reasons = check_eligibility(job, prefs)
    role_family = classify_job_role_family(job)
    preference_score, pref_factors, pref_reasons = compute_preference_match(job, profile)

    blob = job_text_blob(job)
    requirements_out: list[dict] = []
    skills = _resume_skills(profile) if resume_available else set()
    for phrase in extract_requirement_phrases(job):
        status, evidence = _requirement_status(
            phrase, profile, skills, blob.lower(), resume_available=resume_available
        )
        requirements_out.append(
            {"text": phrase, "status": status, "evidence": evidence, "source": "posting"}
        )

    if not resume_available:
        return MatchResult(
            score=None,
            preference_score=preference_score,
            resume_match_available=False,
            eligible=eligible,
            eligibility_reasons=eligibility_reasons,
            role_family=role_family,
            factors=pref_factors,
            requirements=requirements_out,
            gaps=[],
            top_reasons=pref_reasons[:4],
        )

    role_score, role_evidence = role_relevance_score(role_family, job.title, profile, prefs)
    years = _years_experience(profile)
    skills_score, skills_evidence, skill_hits = _skills_score(job, blob, skills)
    experience_score, exp_evidence = _experience_score(job, blob, years)
    edu_score = int(round(min(1.0, _education_level(profile) / 2) * 100)) if _education_level(profile) else 0

    factors = [
        {
            "name": "Role relevance",
            "weight": RESUME_WEIGHTS["role_relevance"],
            "score": role_score,
            "evidence": role_evidence,
            "kind": "resume",
        },
        {
            "name": "Skills",
            "weight": RESUME_WEIGHTS["skills"],
            "score": skills_score,
            "evidence": skills_evidence,
            "kind": "resume",
        },
        {
            "name": "Experience level",
            "weight": RESUME_WEIGHTS["experience"],
            "score": experience_score,
            "evidence": exp_evidence,
            "kind": "resume",
        },
        {
            "name": "Education",
            "weight": RESUME_WEIGHTS["education"],
            "score": edu_score,
            "evidence": (
                ["Education section parsed from resume"] if _education_level(profile) else ["No education on resume"]
            ),
            "kind": "resume",
        },
    ]

    weighted = sum(f["weight"] * f["score"] for f in factors)
    score = int(round(weighted))

    gaps: list[dict] = []
    for req in requirements_out:
        if req["status"] in ("missing", "partial"):
            delta = 8 if req["status"] == "missing" else 4
            gaps.append({"requirement": req["text"], "estimated_score_delta": delta, "status": req["status"]})
    gaps.sort(key=lambda g: g["estimated_score_delta"], reverse=True)

    top_reasons: list[str] = []
    top_reasons.append(f"Role family: {role_family} (relevance {role_score}/100)")
    if role_score >= 70:
        top_reasons.append(role_evidence[0])
    elif role_score <= 25:
        top_reasons.append(role_evidence[0])
    if skill_hits and skills_score >= 40:
        top_reasons.append(f"Skills overlap: {', '.join(skill_hits[:3])}")
    if experience_score >= 80 and years > 0:
        top_reasons.append("Experience level aligns with posting")
    if not top_reasons:
        top_reasons.append("Review requirements — limited evidence for strong fit")

    return MatchResult(
        score=score,
        preference_score=preference_score,
        resume_match_available=True,
        eligible=eligible,
        eligibility_reasons=eligibility_reasons,
        role_family=role_family,
        factors=factors,
        requirements=requirements_out,
        gaps=gaps[:8],
        top_reasons=top_reasons[:4],
    )

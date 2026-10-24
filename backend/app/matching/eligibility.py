from app.matching.requirements import job_text_blob
from app.models.job import Job


def check_eligibility(job: Job, preferences: dict) -> tuple[bool, list[str]]:
    """Hard gates only — do not infer missing profile fields as failures."""
    reasons: list[str] = []
    blob = job_text_blob(job).lower()
    prefs = preferences or {}

    if prefs.get("requires_visa_sponsorship"):
        blocking = (
            "no visa sponsorship",
            "unable to sponsor",
            "will not sponsor",
            "cannot sponsor",
            "without sponsorship",
        )
        if any(phrase in blob for phrase in blocking):
            reasons.append("Posting states visa sponsorship is not available")
            return False, reasons

    preferred = [loc.lower() for loc in prefs.get("preferred_locations") or [] if loc]
    if preferred and job.location:
        loc = job.location.lower()
        if not any(p in loc for p in preferred) and job.remote_flag is not True:
            if prefs.get("open_to_remote") and "remote" in loc:
                pass
            else:
                reasons.append(f"Location '{job.location}' is outside preferred locations")
                return False, reasons

    return True, reasons

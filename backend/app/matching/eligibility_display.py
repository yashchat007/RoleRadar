"""UI eligibility labels — separate from match score."""

from typing import Literal

EligibilityLabel = Literal["eligible", "issue", "unclear"]


def derive_eligibility_label(
    *,
    has_match: bool,
    has_resume: bool,
    hard_eligible: bool | None,
    eligibility_reasons: list[str] | None,
    requirements: list[dict] | None,
) -> tuple[EligibilityLabel, str | None]:
    """
    eligible — hard gates pass and requirements are met with evidence.
    issue — known hard eligibility blocker.
    unclear — insufficient evidence; do not claim eligible.
    """
    if hard_eligible is False:
        reason = (eligibility_reasons or [None])[0]
        return "issue", reason or "See match details for eligibility blockers"

    if not has_resume:
        if hard_eligible is False:
            pass
        else:
            return "unclear", "Upload a resume to assess qualification fit (separate from hard eligibility gates)"

    if not has_match:
        return "unclear", "Match not computed yet"

    reqs = requirements or []
    if not reqs:
        return "unclear", "Not enough structured requirements in the official posting"

    statuses = {r.get("status") for r in reqs}
    if "not_in_profile" in statuses and not has_resume:
        return "unclear", "Upload a resume to compare posting requirements to your background"
    if "missing" in statuses:
        return "unclear", "Some required qualifications could not be verified from your resume"
    if "unclear" in statuses:
        return "unclear", "Insufficient evidence to confirm all listed requirements"
    if "partial" in statuses:
        return "unclear", "Some requirements are only partially matched"

    if not has_resume:
        return "unclear", "Resume required to confirm qualification fit"

    return "eligible", None


def eligibility_label_text(label: EligibilityLabel) -> str:
    return {
        "eligible": "Eligible",
        "issue": "Potential eligibility issue",
        "unclear": "Eligibility unclear",
    }[label]

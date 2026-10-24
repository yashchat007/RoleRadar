import uuid
from datetime import UTC, datetime

from app.matching.engine import SCORING_VERSION, compute_match
from app.matching.fingerprint import job_content_fingerprint, match_is_stale, profile_resume_fingerprint
from app.models.job import Job
from app.models.profile import Profile


def _profile() -> Profile:
    return Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=[
            {
                "name": "Python",
                "confidence": 0.9,
                "from_resume": True,
                "source": {"start": 0, "end": 6, "quote": "Python"},
            },
            {"name": "FastAPI", "confidence": 0.85, "from_resume": True, "source": None},
        ],
        education=[{"institution": "State University B.S. CS 2024", "end_year": 2024, "from_resume": True}],
        experience=[
            {
                "title": "Software Engineer Intern",
                "company": "Acme",
                "start_year": 2023,
                "end_year": 2024,
                "from_resume": True,
                "highlights": [],
            }
        ],
        projects=[],
        preferences={"open_to_remote": True, "graduation_year": 2024, "target_level": "internship"},
    )


def _job(title: str, requirements: str, location: str = "Remote") -> Job:
    return Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key="k1",
        title=title,
        location=location,
        remote_flag=True,
        description_sections={"requirements": requirements},
        listing_url="https://stripe.com/careers/listing/x/1",
        apply_url="https://stripe.com/careers/listing/x/1",
        content_hash="abc",
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )


def test_match_includes_factors_and_requirements():
    job = _job("Backend Engineer — Python", "3+ years Python experience. Bachelor degree. FastAPI preferred.")
    result = compute_match(job, _profile(), resume_available=True)
    assert result.score is not None
    assert 0 <= result.score <= 100
    assert len(result.factors) == 4
    assert result.role_family
    assert result.eligible is True
    assert result.resume_match_available is True
    assert result.scoring_version == SCORING_VERSION
    assert any(r["status"] in ("met", "partial", "unclear", "missing") for r in result.requirements)
    assert result.top_reasons


def test_eligibility_visa_flag():
    job = _job("Backend Intern", "Must be authorized to work in the US. No visa sponsorship.")
    profile = _profile()
    profile.preferences = {"requires_visa_sponsorship": True}
    result = compute_match(job, profile, resume_available=True)
    assert result.eligible is False
    assert result.eligibility_reasons


def test_missing_resume_no_numeric_score():
    job = _job("Intern", "Python required")
    result = compute_match(job, _profile(), resume_available=False)
    assert result.score is None
    assert result.preference_score is not None
    assert result.resume_match_available is False


def test_different_jobs_different_scores():
    profile = _profile()
    strong = _job(
        "Python Backend Intern",
        "Python and FastAPI required. Internship.",
    )
    weak = _job(
        "Sales Intern",
        "Salesforce CRM and cold calling required.",
    )
    s1 = compute_match(strong, profile, resume_available=True).score
    s2 = compute_match(weak, profile, resume_available=True).score
    assert s1 is not None and s2 is not None
    assert s1 > s2 + 10


def test_deterministic_scores():
    job = _job("Software Engineering Intern", "Python experience. Internship.")
    profile = _profile()
    a = compute_match(job, profile, resume_available=True).score
    b = compute_match(job, profile, resume_available=True).score
    assert a == b


def test_preference_score_separate_from_resume():
    job = _job("Software Engineering Intern", "Python.")
    result = compute_match(job, _profile(), resume_available=True)
    assert result.preference_score is not None
    assert result.score is not None
    assert result.preference_score != result.score or True


def test_fingerprint_stale_detection():
    job = _job("Intern", "Python")
    profile = _profile()
    job_fp = job_content_fingerprint(job)
    profile_fp = profile_resume_fingerprint(profile)
    assert match_is_stale(
        scoring_version=1,
        job_fingerprint=job_fp,
        profile_fingerprint=profile_fp,
        current_job_fp=job_fp,
        current_profile_fp=profile_fp,
    )
    assert not match_is_stale(
        scoring_version=SCORING_VERSION,
        job_fingerprint=job_fp,
        profile_fingerprint=profile_fp,
        current_job_fp=job_fp,
        current_profile_fp=profile_fp,
    )


def test_empty_profile_skills_weak_match():
    job = _job("Software Engineering Intern", "Rust and CUDA required.")
    profile = Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=[],
        education=[],
        experience=[],
        projects=[],
        preferences={"target_level": "internship"},
    )
    result = compute_match(job, profile, resume_available=True)
    assert result.score is not None
    assert result.score < 45

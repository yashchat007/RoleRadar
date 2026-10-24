import uuid
from datetime import UTC, datetime

from app.matching.engine import compute_match
from app.matching.resume_gate import profile_has_resume_evidence
from app.models.job import Job
from app.models.profile import Profile


def _job() -> Job:
    return Job(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        source_job_key="k1",
        title="Software Engineering Intern",
        location="Bengaluru, India",
        description_sections={"requirements": "Bachelor degree. Python experience preferred."},
        listing_url="https://example.com/jobs/1",
        apply_url="https://example.com/jobs/1",
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )


def _profile_with_resume() -> Profile:
    return Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=[{"name": "Python", "from_resume": True, "source": {"quote": "Python"}}],
        education=[{"degree": "B.S. CS", "from_resume": True}],
        experience=[{"title": "Intern", "start_year": 2023, "end_year": 2024, "from_resume": True}],
        projects=[],
        preferences={"open_to_remote": True},
    )


def _profile_no_resume() -> Profile:
    return Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=[{"name": "Python"}],
        education=[],
        experience=[],
        projects=[],
        preferences={"open_to_remote": True, "preferred_locations": ["Bengaluru"]},
    )


def test_no_resume_evidence_gate():
    assert profile_has_resume_evidence(_profile_no_resume()) is False
    assert profile_has_resume_evidence(_profile_with_resume()) is True


def test_no_resume_does_not_return_resume_score():
    result = compute_match(_job(), _profile_no_resume(), resume_available=False)
    assert result.score is None
    assert result.resume_match_available is False
    assert result.preference_score is not None
    assert 0 <= result.preference_score <= 100
    assert all(r["status"] == "not_in_profile" for r in result.requirements)


def test_with_resume_returns_score():
    result = compute_match(_job(), _profile_with_resume(), resume_available=True)
    assert result.score is not None
    assert result.resume_match_available is True
    assert 0 <= result.score <= 100


def test_missing_resume_does_not_force_ineligible():
    job = _job()
    job.description_sections = {"requirements": "Open to all locations."}
    result = compute_match(job, _profile_no_resume(), resume_available=False)
    assert result.eligible is True

import uuid

from app.models.profile import Profile
from app.services.resume_profile import clear_resume_derived_profile, mark_resume_entries, merge_resume_preferences


def test_clear_resume_derived_keeps_manual_skills():
    profile = Profile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        skills=[
            {"name": "Python", "from_resume": True},
            {"name": "Rust", "from_resume": False},
        ],
        education=[],
        experience=[],
        projects=[],
        preferences={"preferred_role_families": ["Software Engineering"], "_resume_preference_keys": ["graduation_year"], "graduation_year": 2024},
    )
    clear_resume_derived_profile(profile)
    assert [s["name"] for s in profile.skills] == ["Rust"]
    assert "graduation_year" not in profile.preferences
    assert profile.preferences.get("preferred_role_families") == ["Software Engineering"]


def test_mark_resume_entries():
    rows = mark_resume_entries([{"name": "Go"}])
    assert rows[0]["from_resume"] is True


def test_merge_resume_preferences_tracks_keys():
    merged = merge_resume_preferences({"open_to_remote": True}, {"graduation_year": 2025})
    assert merged["graduation_year"] == 2025
    assert "graduation_year" in merged["_resume_preference_keys"]

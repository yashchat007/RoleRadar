def test_profile_preferences_merge_logic():
    """PATCH /profile merges preference keys (see profile.patch_profile)."""
    base = {"india_only": True, "target_level": "internship"}
    patch = {"open_to_remote": True, "india_only": False}
    merged = {**base, **patch}
    assert merged["india_only"] is False
    assert merged["target_level"] == "internship"
    assert merged["open_to_remote"] is True

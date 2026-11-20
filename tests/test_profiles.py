from presscheck.profiles import PROFILES, get_profile
import pytest

def test_profiles_have_positive_dimensions():
    assert len(PROFILES) >= 4
    assert all(p.width_mm > 0 and p.height_mm > 0 and p.bleed_mm >= 0 for p in PROFILES.values())

def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="Unknown profile"):
        get_profile("made-up")

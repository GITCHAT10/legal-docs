import pytest
from mnos.modules.global_island_safety.country_profile import COUNTRY_PROFILES
from mnos.modules.global_island_safety.market_fit_score import score_country_profile

def test_country_profiles_load():
    assert len(COUNTRY_PROFILES) == 15
    assert "MV" in COUNTRY_PROFILES
    assert "AU" in COUNTRY_PROFILES

def test_maldives_score_highest():
    mv_score = COUNTRY_PROFILES["MV"].market_fit_score
    for code, profile in COUNTRY_PROFILES.items():
        assert mv_score >= profile.market_fit_score

def test_market_scores_above_threshold():
    targets = ["LK", "TH", "ID", "PH", "MY"]
    for t in targets:
        assert COUNTRY_PROFILES[t].market_fit_score >= 8.0

def test_dynamic_scoring_logic():
    mv = COUNTRY_PROFILES["MV"]
    calculated = score_country_profile(mv)
    # 7.0 (base) + 1.5 (island) + 1.0 (readiness) = 9.5
    assert calculated >= 9.0

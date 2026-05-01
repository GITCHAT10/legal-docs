import pytest
from mnos.modules.global_island_safety.market_fit_score import score_country_profile
from mnos.modules.global_island_safety.country_profile import COUNTRY_PROFILES

def test_market_fit_score_calculation():
    for code, profile in COUNTRY_PROFILES.items():
        score = score_country_profile(profile)
        assert 0 <= score <= 10.0

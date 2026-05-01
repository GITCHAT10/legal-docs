from typing import List, Dict

ROLLOUT_STRATEGY = {
    "PHASE_1": ["MV"], # Proof country
    "PHASE_2": ["LK", "TH", "PH"], # High market fit, high tourism
    "PHASE_3": ["ID", "MY", "SC", "FJ", "MU", "VN"], # Strategic island/coastal
    "PHASE_4": ["AU", "JP", "KR", "NZ", "SG"] # High regulatory complexity
}

def get_rollout_phase(country_code: str) -> str:
    for phase, countries in ROLLOUT_STRATEGY.items():
        if country_code in countries:
            return phase
    return "TBD"

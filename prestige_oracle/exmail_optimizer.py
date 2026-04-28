import numpy as np
from typing import Dict, List
from scipy.special import softmax

BASE_CONVERSION_PRIORS = {
    "free_transfer": 0.18, "sunset_experience": 0.22, "floating_breakfast": 0.26,
    "villa_upgrade_priority": 0.15, "private_chef_dining": 0.12
}

SEASON_MULTIPLIERS = {
    "peak": {"free_transfer": 0.8, "sunset_experience": 1.3, "floating_breakfast": 1.4, "villa_upgrade_priority": 0.9, "private_chef_dining": 1.1},
    "shoulder": {"free_transfer": 1.1, "sunset_experience": 1.0, "floating_breakfast": 1.1, "villa_upgrade_priority": 1.2, "private_chef_dining": 1.0},
    "low": {"free_transfer": 1.3, "sunset_experience": 0.9, "floating_breakfast": 0.8, "villa_upgrade_priority": 1.4, "private_chef_dining": 0.7}
}

def optimize_exmail_offer(
    segment: str, season: str, inventory_level: float,
    offer_pool: List[str] = None
) -> Dict:
    """
    Optimizes EXMAIL offers based on segment, season, and real-time inventory.
    """
    if offer_pool is None:
        offer_pool = list(BASE_CONVERSION_PRIORS.keys())

    season = season.lower() if season.lower() in SEASON_MULTIPLIERS else "shoulder"
    expected_probs = {off: BASE_CONVERSION_PRIORS[off] for off in offer_pool if off in BASE_CONVERSION_PRIORS}

    # Segment adjustments
    if segment.upper() == "GCC":
        expected_probs["private_chef_dining"] = expected_probs.get("private_chef_dining", 0.1) * 1.2
    elif segment.upper() in ("EU", "EUROPE"):
        expected_probs["sunset_experience"] = expected_probs.get("sunset_experience", 0.1) * 1.2
    elif segment.upper() in ("CN", "CHINA", "SEA"):
        expected_probs["floating_breakfast"] = expected_probs.get("floating_breakfast", 0.1) * 1.3

    # Season + inventory
    for offer in expected_probs:
        expected_probs[offer] *= SEASON_MULTIPLIERS[season][offer] * max(0.3, inventory_level)

    offers = list(expected_probs.keys())
    # Logit scale for softmax
    logits = np.array([expected_probs[o] * 10.0 for o in offers])
    probs_norm = softmax(logits)
    best_idx = int(np.argmax(probs_norm))

    return {
        "recommended_offer": offers[best_idx],
        "expected_conversion_probability": round(float(probs_norm[best_idx]), 4),
        "offer_ranking": {off: round(float(p), 4) for off, p in zip(offers, probs_norm)},
        "inventory_constraint_applied": inventory_level < 0.7,
        "season_context": season
    }

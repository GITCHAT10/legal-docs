import numpy as np
from typing import Dict

def predict_success(
    candidate_pillars: Dict[str, float],
    role_weights: Dict[str, float],
    manager_tier: float = 0.7,
    resort_complexity: float = 0.5,
    location_readiness: float = 0.8
) -> Dict:
    """
    Logistic Prediction Engine: Calculates probability of candidate success.
    Uses a weighted linear combination of pillars adjusted by environmental factors.
    """
    # 1. Base Score calculation
    base_score = 0.0
    for pillar, score in candidate_pillars.items():
        weight = role_weights.get(pillar, 0.25)
        base_score += (score / 100.0) * weight

    # 2. Factor adjustments (Logit scale)
    # y = sum(weights * scores) + bias
    logit = (base_score * 4.0) - 2.0 # Scale to roughly [-2, 2]

    # Environmental shifts
    logit += (manager_tier - 0.7) * 2.0
    logit -= (resort_complexity - 0.5) * 1.5
    logit += (location_readiness - 0.8) * 1.0

    # 3. Sigmoid transformation
    probability = 1 / (1 + np.exp(-logit))

    # 4. Calibration adjustment
    calibrated_prob = round(float(probability), 4)

    return {
        "success_probability": calibrated_prob,
        "confidence_score": round(1.0 - abs(0.5 - calibrated_prob) * 0.5, 4),
        "factors": {
            "base_competency": round(base_score, 4),
            "environmental_delta": round(logit - ((base_score * 4.0) - 2.0), 4)
        },
        "recommendation": "PROMOTABLE" if calibrated_prob > 0.8 else "STABLE" if calibrated_prob > 0.6 else "REVIW_REQUIRED"
    }

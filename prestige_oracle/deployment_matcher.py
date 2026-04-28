import numpy as np
from typing import Dict, List

def evaluate_deployment(
    candidate_beliefs: Dict[str, Dict],
    role_requirements: Dict[str, float],
    uncertainty_tolerance: float = 0.85
) -> Dict:
    """
    Evaluates candidate-role match based on Bayesian competency beliefs.
    """
    match_scores = []
    risk_factors = []

    for pillar, req_threshold in role_requirements.items():
        belief = candidate_beliefs.get(pillar, {})
        comp_mean = belief.get("mean", 0.5)
        comp_var = belief.get("variance", 0.1)

        match_scores.append(max(0, min(1, (comp_mean - req_threshold + 0.2) / 0.4)))

        if comp_mean < req_threshold:
            risk_factors.append(f"below_threshold_{pillar}")
        if comp_var > uncertainty_tolerance * 0.05:
            risk_factors.append(f"high_uncertainty_{pillar}")

    overall_match = float(np.mean(match_scores))
    risk_count = len(risk_factors)

    if risk_count == 0 and overall_match >= 0.85:
        risk_level = "low"
    elif risk_count <= 1 or (0.65 <= overall_match < 0.85):
        risk_level = "medium"
    else:
        risk_level = "high"

    action = {
        "low": "Deploy immediately",
        "medium": "Deploy with assigned mentor + weekly SHADOW check-ins",
        "high": "Retain for targeted training. Do not deploy."
    }[risk_level]

    return {
        "overall_match_score": round(overall_match, 4),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommended_action": action,
        "success_probability": round(overall_match * 0.9 + 0.1, 4)
    }

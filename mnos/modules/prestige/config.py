import os
from typing import Dict

# Region Configuration
# REJECTS "male-azure" explicitly as per doctrine.
ALLOWED_REGIONS = [
    "UAE North",
    "Southeast Asia",
    "Central India",
    "Singapore"
]

DEFAULT_REGION = os.environ.get("PRESTIGE_PRIMARY_REGION", "Singapore")
if DEFAULT_REGION == "male-azure":
    # Doctrine: "male-azure" is not safe to claim.
    DEFAULT_REGION = "Singapore"

PRESTIGE_CONFIG = {
    "region": DEFAULT_REGION,
    "data_residency_policy": "maldives_pdpa_controlled",
    "edge_residency": "AIRCLOUD Maldives Node",
    "nearest_compliant_region": DEFAULT_REGION
}

# Capability-based Model Routing
# DO NOT hardcode future model names like gpt-5 or claude-mythos-5.
MODEL_ROUTING = {
    "planning": {
        "preferred": "computer_use_planning",
        "fallback": "long_context_reasoning"
    },
    "reasoning": {
        "preferred": "policy_contract_reasoning"
    },
    "multimodal": {
        "preferred": "document_image_voice_analysis"
    },
    "adversarial_review": {
        "preferred": "multi_agent_contradiction_check"
    },
    "edge_offline": {
        "preferred": "local_small_model_or_symbolic_rules"
    }
}

def get_model_for_capability(capability: str) -> str:
    route = MODEL_ROUTING.get(capability)
    if not route:
        return "default_reasoning_model"
    return route.get("preferred")

def get_region_config(region_name: str) -> Dict:
    if region_name == "male-azure":
         raise ValueError("REJECTED: region 'male-azure' is invalid. Use a compliant region.")
    return PRESTIGE_CONFIG

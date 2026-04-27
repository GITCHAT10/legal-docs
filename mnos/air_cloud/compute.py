from enum import Enum
from typing import Dict, Any

class ComputeTier(Enum):
    SOVEREIGN_LOCAL = "NVIDIA_DGX_STATION" # On-prem, sensitive PII
    REGIONAL_EDGE = "NVIDIA_T4_EDGE"      # Island-level processing
    GLOBAL_BURST = "AWS_TRAINIUM"         # Scaling for anonymized data

class SovereignComputeManager:
    """
    AIR CLOUD: Compute & AI Resource Abstraction.
    Routes processing based on data sensitivity and tenant locality.
    """
    def __init__(self):
        self.resources = {
            ComputeTier.SOVEREIGN_LOCAL: {"status": "ACTIVE", "location": "Male-HQ"},
            ComputeTier.REGIONAL_EDGE: {"status": "ACTIVE", "location": "ADh.Omadhoo"}
        }

    def allocate_ai_resource(self, data_sensitivity: str) -> Dict[str, Any]:
        """
        Gating Rule: Guest PII (high sensitivity) NEVER leaves sovereign local compute.
        """
        if data_sensitivity == "high":
            tier = ComputeTier.SOVEREIGN_LOCAL
        elif data_sensitivity == "medium":
            tier = ComputeTier.REGIONAL_EDGE
        else:
            tier = ComputeTier.GLOBAL_BURST

        return {
            "tier": tier.value,
            "provider": "AIG-INTERNAL" if tier != ComputeTier.GLOBAL_BURST else "AWS-BURST",
            "locality_enforced": True
        }

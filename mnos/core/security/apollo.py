from typing import Dict, Any
from mnos.config import config

class ApolloPolicyPlane:
    """
    APOLLO Control Plane (HARDENED):
    Manages policy evaluation before any autonomous action.
    """
    def __init__(self):
        self.min_confidence = {
            3: 0.90, # TL-3 requires 90%
            4: 0.95, # TL-4 requires 95%
            5: 0.99  # TL-5 requires 99%
        }

    def evaluate_action(self, threat_level: int, zone: str, data: Dict[str, Any]) -> bool:
        """
        Evaluate if an action is permitted based on policy plane rules.
        """
        print(f"[APOLLO] Evaluating Policy for TL-{threat_level} in {zone}")

        # Policy: High confidence required for automated restriction
        confidence = data.get("frigate_event", {}).get("after", {}).get("confidence", 0)
        required = self.min_confidence.get(threat_level, 0.70)

        if confidence < required:
            print(f"[APOLLO] POLICY DENIED: Confidence {confidence} below threshold {required}")
            return False

        # Policy: Safe Exit must always be preserved (logical check)
        if data.get("restriction") == "total_lockdown" and not data.get("safe_exit"):
            print(f"[APOLLO] POLICY DENIED: Safe Exit Violation")
            return False

        print(f"[APOLLO] POLICY GRANTED")
        return True

apollo = ApolloPolicyPlane()

from typing import Dict, Any, List

class GovernanceException(Exception):
    pass

class L5SafeFiringLogic:
    """
    Governance Security Layer (L5 Safe-Firing Logic):
    Ensures no critical action happens automatically.
    Requires evidence, approval, and confirmation.
    """
    def __init__(self):
        self.critical_actions = {"system_shutdown", "network_routing_change", "data_purge"}

    def validate_action(self, action: str, evidence: Dict[str, Any], approvals: List[str]):
        """
        Validates critical actions against L5 requirements.
        """
        if action not in self.critical_actions:
            return True # Not a critical action, proceed

        # 1. Evidence Check
        if not evidence or not evidence.get("reason") or not evidence.get("timestamp"):
            raise GovernanceException(f"L5: Critical action '{action}' requires formal evidence.")

        # 2. Approval Check (Human identity required)
        if len(approvals) < 1:
            raise GovernanceException(f"L5: Critical action '{action}' requires at least one authorized human approval.")

        # 3. Confirmation Check
        if not evidence.get("confirmed", False):
            raise GovernanceException(f"L5: Critical action '{action}' pending final human confirmation.")

        return True

l5 = L5SafeFiringLogic()

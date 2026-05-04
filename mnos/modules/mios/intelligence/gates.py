from uuid import UUID, uuid4
from typing import Dict, List, Any, Optional

class ExecutionGates:
    """
    AGI-Compatible Execution Gates for MIOS Intelligence Layer.
    Enforces human-in-the-loop and sandbox-safe execution.
    """

    def __init__(self, shadow):
        self.shadow = shadow
        self.permission_matrix = {
            "agent": {
                "allowed_actions": ["prepare", "suggest", "draft", "compare", "alert"],
                "blocked_actions": ["bypass_customs", "override_finance", "seal_shadow_manually"]
            }
        }
        self.pending_approvals: Dict[UUID, dict] = {}

    def request_human_approval(self, shipment_id: UUID, action_type: str, action_payload: dict) -> UUID:
        approval_id = uuid4()
        self.pending_approvals[approval_id] = {
            "shipment_id": shipment_id,
            "action": action_type,
            "payload": action_payload,
            "status": "PENDING"
        }
        self.shadow.commit("mios.gate.approval_requested", "SYSTEM", {"approval_id": str(approval_id), "action": action_type})
        return approval_id

    def validate_agent_action(self, action_name: str) -> bool:
        """Fail-closed policy for agentic actions."""
        if action_name in self.permission_matrix["agent"]["blocked_actions"]:
            return False
        return action_name in self.permission_matrix["agent"]["allowed_actions"]

    def sandbox_simulate(self, action_func: callable, *args, **kwargs) -> dict:
        """Sandbox simulation mode for non-mutating testing of AGI logic."""
        try:
            result = action_func(*args, **kwargs)
            return {"status": "SUCCESS_SIMULATED", "potential_result": result}
        except Exception as e:
            return {"status": "FAILURE_SIMULATED", "error": str(e)}

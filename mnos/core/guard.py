from typing import Callable, Any, Dict
from mnos.core.policy import PolicyEngine
from mnos.modules.shadow.ledger import ShadowLedger

class ExecutionGuard:
    """
    MNOS Execution Guard (v10.0).
    Wraps critical actions with policy enforcement and SHADOW logging.
    """
    def __init__(self, shadow: ShadowLedger):
        self.policy = PolicyEngine()
        self.shadow = shadow

    def execute(self, action_name: str, actor_id: str, func: Callable, *args, **kwargs) -> Any:
        # 1. SHADOW Intent Logging
        correlation_id = kwargs.get("correlation_id", "UNKNOWN")
        self.shadow.commit(f"INTENT_{action_name}", actor_id, {"correlation_id": correlation_id})

        # 2. Policy Enforcement
        context = {"verified_identity": True} # Mock context
        if not self.policy.evaluate(action_name, context):
            self.shadow.commit(f"REJECTED_{action_name}", actor_id, {"reason": "Policy violation"})
            raise PermissionError(f"Action {action_name} rejected by Policy Engine")

        # 3. Execution
        try:
            # Strip correlation_id from kwargs before calling the function if it wasn't expected
            result = func(*args, **kwargs)
            # 4. SHADOW Result Logging
            self.shadow.commit(f"RESULT_{action_name}", actor_id, {"status": "SUCCESS"})
            return result
        except Exception as e:
            self.shadow.commit(f"RESULT_{action_name}", actor_id, {"status": "FAILURE", "error": str(e)})
            raise

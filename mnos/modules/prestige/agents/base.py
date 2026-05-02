from typing import Any, Dict, List
from mnos.modules.prestige.config import get_model_for_capability
from mnos.shared.execution_guard import ExecutionGuard

class BasePrestigeAgent:
    def __init__(self, agent_id: str, core_system: Any, permissions: List[str] = None):
        self.agent_id = agent_id
        self.core = core_system
        self.permissions = permissions or ["READ_ONLY"]

    async def execute_task(self, task_data: Dict, actor_ctx: Dict = None) -> Dict:
        """
        AI agents may reason, recommend, draft, classify, route, prepare.
        AI agents may NOT directly confirm bookings, execute payments, etc.
        """
        # Default SYSTEM actor if not provided (staging fallback)
        actor = actor_ctx or {"identity_id": "SYSTEM", "role": "admin", "device_id": "STAGING-CORE"}

        with ExecutionGuard.authorized_context(actor):
            # Doctrine Enforcement: Forbidden Actions
            forbidden_keys = [
                "confirm_booking", "execute_payment", "settle_supplier",
                "dispatch_transfer", "seal_final_readiness"
            ]
            if any(k in task_data for k in forbidden_keys):
                self.core.shadow.commit(
                    "prestige.agentic.execution_blocked_by_guardrail",
                    self.agent_id,
                    {"reason": "Agent attempted forbidden direct execution action."}
                )
                raise PermissionError(f"FORBIDDEN: Agent {self.agent_id} cannot execute direct actions.")

            # Ensure trace_id propagation
            trace_id = task_data.get("trace_id", "UNTRACTED")

            result = await self._run_agent_logic(task_data)

            if "trace_id" not in result:
                result["trace_id"] = trace_id

            return result

    async def _run_agent_logic(self, task_data: Dict) -> Dict:
        raise NotImplementedError("Subclasses must implement _run_agent_logic")

    def get_capability_model(self, capability: str) -> str:
        return get_model_for_capability(capability)

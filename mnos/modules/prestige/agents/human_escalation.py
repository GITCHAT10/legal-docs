from mnos.modules.prestige.agents.base import BasePrestigeAgent
from typing import Dict

class HumanEscalationAgent(BasePrestigeAgent):
    async def _run_agent_logic(self, task_data: Dict) -> Dict:
        # Request human approval for high-value sends or bookings
        reason = task_data.get("reason", "high_value_booking")

        return {
            "agent": self.agent_id,
            "status": "pending_approval",
            "escalation_type": "human_in_the_loop",
            "reason": reason
        }

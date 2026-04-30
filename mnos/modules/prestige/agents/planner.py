from mnos.modules.prestige.agents.base import BasePrestigeAgent
from typing import Dict

class PlannerAgent(BasePrestigeAgent):
    async def execute_task(self, task_data: Dict) -> Dict:
        # Planner decomposes inquiry into sourcing tasks
        inquiry = task_data.get("inquiry", "")
        model = self.get_capability_model("planning")

        return {
            "agent": self.agent_id,
            "status": "planned",
            "model_used": model,
            "sub_tasks": ["source_hotel", "source_flights", "source_transfers"]
        }

from mnos.modules.prestige.agents.base import BasePrestigeAgent
from typing import Dict

class TransferAgent(BasePrestigeAgent):
    async def _run_agent_logic(self, task_data: Dict) -> Dict:
        # Transfer Agent checks transfer possibilities and UT feasibility
        preferred_mode = task_data.get("preferred_transfer_mode", "speedboat")

        return {
            "agent": self.agent_id,
            "status": "transfer_recommendation_ready",
            "recommended_transfer": preferred_mode,
            "ut_feasibility_request": True,
            "notes": "Recommend checking night landing capability for seaplanes if after 16:00."
        }

from mnos.modules.prestige.agents.base import BasePrestigeAgent
from typing import Dict

class GuestAppAgent(BasePrestigeAgent):
    async def execute_task(self, task_data: Dict) -> Dict:
        # Build itinerary for guest app
        trip_data = task_data.get("trip_data", {})
        model = self.get_capability_model("multimodal")

        return {
            "agent": self.agent_id,
            "status": "itinerary_ready",
            "itinerary_url": f"https://guest.prestige.mv/trip/{trip_data.get('trip_id')}",
            "model_used": model
        }

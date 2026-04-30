from mnos.modules.prestige.agents.base import BasePrestigeAgent
from typing import Dict, List, Any

class HotelAgent(BasePrestigeAgent):
    def __init__(self, agent_id: str, core_system: Any, sourcing_engine: Any):
        super().__init__(agent_id, core_system)
        self.sourcing_engine = sourcing_engine

    async def execute_task(self, task_data: Dict) -> Dict:
        # Hotel Agent sources inventory using the multi-lane sourcing engine
        query = {
            "location": task_data.get("location", "Maldives"),
            "dates": task_data.get("dates"),
            "guests": task_data.get("guests")
        }

        results = await self.sourcing_engine.search_hotels(query)

        return {
            "agent": self.agent_id,
            "status": "hotel_sourced",
            "options": results
        }

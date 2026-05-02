from mnos.modules.prestige.agents.base import BasePrestigeAgent
from mnos.modules.prestige.pricing import PrestigePricingEngine
from decimal import Decimal
from typing import Dict, Any

class PricingAgent(BasePrestigeAgent):
    def __init__(self, agent_id: str, core_system: Any):
        super().__init__(agent_id, core_system)
        self.pricing_engine = PrestigePricingEngine()

    async def _run_agent_logic(self, task_data: Dict) -> Dict:
        base_price = Decimal(str(task_data.get("base_price_usd", 0)))
        nights = task_data.get("nights", 1)
        adults = task_data.get("adults", 1)

        breakdown = self.pricing_engine.calculate_luxury_package(base_price, nights, adults)

        return {
            "agent": self.agent_id,
            "status": "priced",
            "pricing_breakdown": breakdown
        }

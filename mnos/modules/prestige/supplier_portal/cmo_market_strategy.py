from typing import Dict
from mnos.modules.prestige.supplier_portal.models import CMOMarketStrategyProfile

class CMOMarketStrategyManager:
    """
    CMO protects market strategy, campaign fit, brand positioning, and final go-to-market approval.
    """
    def __init__(self):
        self.strategies: Dict[str, CMOMarketStrategyProfile] = {}

    def set_strategy(self, resort_id: str, strategy: CMOMarketStrategyProfile):
        self.strategies[resort_id] = strategy
        return {"status": "success", "resort_id": resort_id}

    def get_strategy(self, resort_id: str) -> CMOMarketStrategyProfile:
        return self.strategies.get(resort_id, CMOMarketStrategyProfile())

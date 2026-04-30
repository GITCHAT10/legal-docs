from mnos.modules.prestige.adapters.base_adapter import BaseHotelAdapter
from typing import Dict, List

class TBOHolidaysAdapter(BaseHotelAdapter):
    async def get_rates(self, query: Dict) -> List[Dict]:
        # Priority 2: Main B2B backup inventory
        return [
            {
                "hotel_id": "TBO-8829",
                "name": "Global Maldives Heights",
                "rate_usd": 680.00,
                "source": self.name
            }
        ]

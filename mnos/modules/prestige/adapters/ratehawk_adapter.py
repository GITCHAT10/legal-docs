from mnos.modules.prestige.adapters.base_adapter import BaseHotelAdapter
from typing import Dict, List

class RateHawkAdapter(BaseHotelAdapter):
    async def get_rates(self, query: Dict) -> List[Dict]:
        # Priority 3: Global fallback + rate comparison
        return [
            {
                "hotel_id": "RH-19283",
                "name": "Emerald Bay Resort",
                "rate_usd": 720.00,
                "source": self.name
            }
        ]

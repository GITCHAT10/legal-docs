from mnos.modules.prestige.adapters.base_adapter import BaseHotelAdapter
from typing import Dict, List

class HotelbedsAdapter(BaseHotelAdapter):
    async def get_rates(self, query: Dict) -> List[Dict]:
        # Priority 4: Wholesale hotel supply / global expansion
        return [
            {
                "hotel_id": "HB-5521",
                "name": "Sapphire Sands",
                "rate_usd": 590.00,
                "source": self.name
            }
        ]

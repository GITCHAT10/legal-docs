from mnos.modules.prestige.adapters.base_adapter import BaseHotelAdapter
from typing import Dict, List

class DirectMaldivesAdapter(BaseHotelAdapter):
    async def get_rates(self, query: Dict) -> List[Dict]:
        # Priority 1: SALA / own hotels, Direct Maldives resorts, Direct guesthouses
        # Mocking local supply
        return [
            {
                "hotel_id": "SALA-01",
                "name": "SALA Beach Resort",
                "rate_usd": 450.00,
                "source": self.name,
                "type": "SALA_OWNED"
            },
            {
                "hotel_id": "RESORT-DIRECT-01",
                "name": "Luxury Atoll Island",
                "rate_usd": 1200.00,
                "source": self.name,
                "type": "DIRECT_RESORT"
            }
        ]

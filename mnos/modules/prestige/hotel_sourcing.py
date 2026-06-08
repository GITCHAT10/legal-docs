from typing import Dict, List
from mnos.modules.prestige.adapters.direct_adapter import DirectMaldivesAdapter
from mnos.modules.prestige.adapters.tbo_adapter import TBOHolidaysAdapter
from mnos.modules.prestige.adapters.ratehawk_adapter import RateHawkAdapter
from mnos.modules.prestige.adapters.hotelbeds_adapter import HotelbedsAdapter

class HotelSourcingEngine:
    def __init__(self):
        # 4 hotel supply lanes with priority
        self.adapters = [
            DirectMaldivesAdapter("Direct Supply"),
            TBOHolidaysAdapter("TBO Holidays"),
            RateHawkAdapter("RateHawk"),
            HotelbedsAdapter("Hotelbeds")
        ]

    async def search_hotels(self, query: Dict) -> List[Dict]:
        """
        Multi-lane priority logic:
        Direct contract first
        ↓
        TBO Holidays
        ↓
        RateHawk
        ↓
        Hotelbeds
        """
        all_results = []
        for adapter in self.adapters:
            try:
                rates = await adapter.get_rates(query)
                all_results.extend(rates)
            except Exception as e:
                # Log error and continue to next lane
                print(f"Adapter {adapter.name} failed: {e}")

        return all_results

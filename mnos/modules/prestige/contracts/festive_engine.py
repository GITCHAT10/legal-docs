from decimal import Decimal
from datetime import date
from typing import List
from mnos.modules.prestige.contracts.accommodation_schema import AccommodationContractV2

class FestiveEngine:
    def calculate_festive_surcharge(self, contract: AccommodationContractV2, stay_dates: List[date]) -> Decimal:
        """
        Calculates Festive Gala Dinner Surcharge for Dec 24 and Dec 31.
        """
        total_surcharge = Decimal("0.00")

        for d in stay_dates:
            if d.month == 12 and d.day == 24:
                if contract.festive_gala_christmas:
                    total_surcharge += contract.festive_gala_christmas
            elif d.month == 12 and d.day == 31:
                if contract.festive_gala_new_year:
                    total_surcharge += contract.festive_gala_new_year

        return total_surcharge

    def get_brief_wording(self, surcharge: Decimal, privacy_level: str) -> str:
        # P3/P4 Prestige Brief wording as “Inclusive Signature Experience”
        if privacy_level in ["P3", "P4"] and surcharge > 0:
            return "Inclusive Signature Experience"
        return f"Compulsory Festive Gala Dinner: ${surcharge}"

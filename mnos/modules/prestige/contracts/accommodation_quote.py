from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from mnos.modules.prestige.contracts.accommodation_schema import AccommodationContractV2, EstablishmentType, MealPlan

class AccommodationQuoteEngine:
    def calculate_green_tax(self, contract: AccommodationContractV2, adults: int, children: int, nights: int, total_hours: float = 24.0) -> Decimal:
        """
        MANDATORY GREEN TAX 2026 LOGIC:
        - children under 2 exempt
        - less than 12-hour stay not taxed
        - USD 12: resort, integrated resort, resort hotel, tourist vessel, uninhabited-island, or > 50 rooms
        - USD 6: inhabited-island hotel/guesthouse <= 50 rooms
        """
        if total_hours < 12.0:
            return Decimal("0.00")

        rate = Decimal("12.00")

        # USD 6 rule for small inhabited island properties
        is_small_inhabited = (
            contract.island_type == "INHABITED_LOCAL_ISLAND" and
            contract.room_count <= 50
        )
        if is_small_inhabited:
            rate = Decimal("6.00")

        return rate * adults * nights # Children under 2 handled by intake filter

    def resolve_meal_plan(self, contract: AccommodationContractV2, requested_plan: MealPlan) -> MealPlan:
        # Guesthouse AI converted to NON_ALCOHOLIC_AI
        if contract.establishment_type == EstablishmentType.GUESTHOUSE and requested_plan == MealPlan.AI:
            return MealPlan.NON_ALCOHOLIC_AI
        return requested_plan

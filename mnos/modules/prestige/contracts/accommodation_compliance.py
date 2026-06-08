from typing import List, Dict, Any
from mnos.modules.prestige.contracts.accommodation_schema import AccommodationContractV2, IslandType

class AccommodationCompliance:
    def get_island_notices(self, contract: AccommodationContractV2) -> List[str]:
        notices = []
        if contract.island_type == IslandType.INHABITED_LOCAL_ISLAND:
            notices.append("LOCAL_ISLAND_NOTICE: Respect local culture (modest dress in public).")
            notices.append("DRY_ISLAND_NOTICE: Alcohol consumption is restricted on local inhabited islands.")
        return notices

    def verify_split_stay(self, stay_list: List[AccommodationContractV2]) -> Dict[str, Any]:
        # split-stay guesthouse-to-resort verification
        has_guesthouse = any(s.establishment_type == "GUESTHOUSE" for s in stay_list)
        has_resort = any(s.establishment_type == "RESORT" for s in stay_list)

        return {
            "is_valid": True,
            "requires_verification": has_guesthouse and has_resort,
            "notice": "Split-stay between local island and resort requires MIRA health/travel verification." if has_guesthouse and has_resort else None
        }

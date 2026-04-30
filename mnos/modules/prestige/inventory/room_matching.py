from typing import List, Dict, Any, Optional
from uuid import UUID
from mnos.modules.prestige.inventory.room_category_schema import RoomCategory, PrivacyLevel, EstablishmentType
from mnos.modules.prestige.contracts.transfer_quote import UHNWIntake

class RoomMatchingEngine:
    def __init__(self, shadow):
        self.shadow = shadow

    def match_room_categories(self, intake: UHNWIntake, room_categories: List[RoomCategory]) -> List[Dict[str, Any]]:
        """
        PRESTIGE Room Matching Logic:
        UHNW Intake -> Suitable Categories.
        AI Recommends, MAC EOS Enforces.
        """
        self.shadow.commit("prestige.room.matching_started", intake.resort_id, {"intake": intake.model_dump()})

        ranked_options = []
        total_guests = intake.guest_count_adult + intake.guest_count_child + intake.guest_count_infant

        for room in room_categories:
            # 1. Reject stop-sale
            if room.stop_sale_flag or room.status == "stop_sale":
                self.shadow.commit("prestige.room.stop_sale_rejected", str(room.room_category_id), {"room_name": room.room_category_name})
                continue

            # 2. Occupancy Check
            if total_guests > room.max_total_occupancy:
                self.shadow.commit("prestige.room.occupancy_rejected", str(room.room_category_id), {"room_name": room.room_category_name, "guests": total_guests, "max": room.max_total_occupancy})
                continue

            if intake.guest_count_adult > room.max_adults:
                 continue

            # 3. Privacy Filter (P3/P4 guests)
            guest_privacy = PrivacyLevel(intake.privacy_level) # assuming matching strings
            if guest_privacy in [PrivacyLevel.P3, PrivacyLevel.P4]:
                if guest_privacy not in room.privacy_levels_supported:
                    self.shadow.commit("prestige.room.privacy_filter_applied", str(room.room_category_id), {"guest_privacy": guest_privacy})
                    continue

            # 4. Alcohol / Guesthouse filter
            # Simplified: if alcohol mentioned in notes or assumed by AI
            if room.establishment_type == EstablishmentType.GUESTHOUSE:
                # Guesthouses in Maldives are dry islands.
                # If guest wants luxury AI with alcohol, filter out.
                if "alcohol" in (intake.must_avoid_notes or "").lower() or intake.preferred_transfer_mode == "seaplane":
                     # Heuristic: Seaplane guests rarely want guesthouses.
                     continue

            # 5. Score/Rank
            score = 0
            if guest_privacy == PrivacyLevel.P4 and room.private_pool: score += 100
            if guest_privacy == PrivacyLevel.P4 and room.room_category_type == "RESIDENCE": score += 200

            option = {
                "room": room,
                "score": score,
                "status": "MATCHED"
            }
            ranked_options.append(option)
            self.shadow.commit("prestige.room.option_ranked", str(room.room_category_id), {"score": score})

        # Sort by score desc
        ranked_options.sort(key=lambda x: x["score"], reverse=True)

        self.shadow.commit("prestige.room.matching_completed", intake.resort_id, {"matches_found": len(ranked_options)})

        return ranked_options

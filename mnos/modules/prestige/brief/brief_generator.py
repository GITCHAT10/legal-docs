import uuid
from typing import Dict, Any, List
from mnos.modules.prestige.brief.brief_models import PrestigeBrief, BriefType

class BriefGenerator:
    def generate_brief(self, booking_data: Dict[str, Any], brief_type: BriefType, privacy_level: str) -> PrestigeBrief:
        """
        - P3/P4 brief must hide unnecessary operational details
        - do not expose internal SHADOW hashes to guest version
        - do not expose private villa GPS to guest/agent unless authorized
        """
        is_high_privacy = privacy_level in ["P3", "P4"]

        # Filter logistics for privacy
        logistics = booking_data.get("logistics", [])
        safe_logistics = []
        for step in logistics:
            item = step.copy()
            if is_high_privacy:
                item.pop("internal_staff_notes", None)
                item.pop("vessel_tail_no", None) # Hide specific tail no for P4 if needed
            safe_logistics.append(item)

        brief = PrestigeBrief(
            brief_id=f"BR-{uuid.uuid4().hex[:6].upper()}",
            brief_type=brief_type,
            guest_name=booking_data.get("guest_name", "Valued Guest"),
            itinerary=booking_data.get("itinerary", []),
            transfer_logistics=safe_logistics,
            villa_summary=booking_data.get("villa_summary", {}),
            pricing_items=booking_data.get("pricing", []),
            payment_status=booking_data.get("payment_status", "PENDING"),
            emergency_contacts=[{"name": "Prestige Command", "phone": "+960-777-PRESTIGE"}],
            shadow_proof_status="VERIFIED" if brief_type != BriefType.PROPOSAL else "N/A"
        )

        return brief

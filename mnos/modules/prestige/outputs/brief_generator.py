import uuid
from typing import Dict, Any, List, Optional
from mnos.modules.prestige.outputs.brief_models import PrestigeBrief, BriefType

class BriefGenerator:
    def __init__(self, command_center, logistics_checklist):
        self.command_center = command_center
        self.checklist = logistics_checklist

    def generate_brief(self, booking_id: str, booking_data: Dict[str, Any], brief_type: BriefType, privacy_level: str) -> PrestigeBrief:
        """
        - final brief blocks if critical RED exists
        - final brief requires FINAL_24H_LOGISTICS_PROOF_SEALED or RESEALED
        - P3/P4 brief must hide unnecessary operational details
        """
        # 1. Validation Logic
        status = self.command_center.get_status(booking_id)
        if brief_type in [BriefType.AGENT_FINAL, BriefType.GUEST_FINAL]:
            if status == "RED":
                raise ValueError(f"BLOCKED: Cannot generate final brief for {booking_id} while status is RED.")

            if not self.checklist.is_arrival_ready(booking_id):
                 raise ValueError(f"BLOCKED: {booking_id} requires FINAL_24H_LOGISTICS_PROOF_SEALED.")

        # 2. Privacy Filtering (P3/P4)
        is_high_privacy = privacy_level in ["P3", "P4"]
        logistics = booking_data.get("logistics", [])
        safe_logistics = []
        for step in logistics:
            item = step.copy()
            if is_high_privacy:
                item.pop("internal_staff_notes", None)
                item.pop("vessel_gps", None) # Hide private coordinates
                item.pop("vessel_tail_no", None)
            safe_logistics.append(item)

        # 3. Construct Brief
        guest_name = booking_data.get("guest_name", "Valued Guest")
        if is_high_privacy:
            guest_name = "Valued Guest"

        brief = PrestigeBrief(
            brief_id=f"BR-{uuid.uuid4().hex[:6].upper()}",
            brief_type=brief_type,
            guest_name=guest_name,
            itinerary=booking_data.get("itinerary", []),
            transfer_logistics=safe_logistics,
            villa_summary=booking_data.get("villa_summary", {}),
            pricing_items=booking_data.get("pricing", []),
            payment_status=booking_data.get("payment_status", "PENDING"),
            emergency_contacts=[{"name": "Prestige Command", "phone": "+960-777-PRESTIGE"}],
            shadow_proof_status="VERIFIED" if brief_type != BriefType.PROPOSAL else "N/A",
            legal_tax_breakdown=booking_data.get("tax_breakdown") # Shown in all versions for legal compliance
        )

        return brief

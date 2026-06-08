from enum import Enum

class ChecklistItem(str, Enum):
    GUEST_IDENTITY_VERIFIED = "GUEST_IDENTITY_VERIFIED"
    ARRIVAL_FLIGHT_VERIFIED = "ARRIVAL_FLIGHT_VERIFIED"
    AIRPORT_HANDLING_CONFIRMED = "AIRPORT_HANDLING_CONFIRMED"
    TRANSFER_FEASIBILITY_CONFIRMED = "TRANSFER_FEASIBILITY_CONFIRMED"
    TRANSFER_ASSET_ASSIGNED = "TRANSFER_ASSET_ASSIGNED"
    VILLA_READINESS_CONFIRMED = "VILLA_READINESS_CONFIRMED"
    GUEST_PREFERENCE_CONFIRMED = "GUEST_PREFERENCE_CONFIRMED"
    EXPERIENCE_SCHEDULE_CONFIRMED = "EXPERIENCE_SCHEDULE_CONFIRMED"
    PAYMENT_STATUS_VERIFIED = "PAYMENT_STATUS_VERIFIED"
    SETTLEMENT_STATUS_VERIFIED = "SETTLEMENT_STATUS_VERIFIED"
    AGENT_FINAL_BRIEF_SENT = "AGENT_FINAL_BRIEF_SENT"
    GUEST_APP_BUNDLE_DELIVERED = "GUEST_APP_BUNDLE_DELIVERED"
    FINAL_24H_LOGISTICS_PROOF_SEALED = "FINAL_24H_LOGISTICS_PROOF_SEALED"

class ShadowLogisticsChecklist:
    def __init__(self, shadow):
        self.shadow = shadow
        self.checklists = {} # booking_id -> {item: status}

    def verify_item(self, booking_id: str, item: ChecklistItem, actor_ctx: dict):
        if booking_id not in self.checklists:
            self.checklists[booking_id] = {i: False for i in ChecklistItem}

        self.checklists[booking_id][item] = True
        self.shadow.commit("prestige.logistics.item_verified", booking_id, {"item": item, "status": "VERIFIED"})

    def is_arrival_ready(self, booking_id: str) -> bool:
        # no arrival-ready status without FINAL_24H_LOGISTICS_PROOF_SEALED
        checklist = self.checklists.get(booking_id, {})
        return checklist.get(ChecklistItem.FINAL_24H_LOGISTICS_PROOF_SEALED, False)

import time
import uuid
from typing import Dict, Any

class ReservationValidator:
    def __init__(self, core_system):
        self.core = core_system

    def validate_reservation(self, actor_ctx: dict, channel_id: str, payload: Dict[str, Any]):
        return self.core.guard.execute_sovereign_action(
            "prestige.channel.validate_reservation",
            actor_ctx,
            self._internal_validate,
            channel_id, payload
        )

    def _internal_validate(self, channel_id: str, payload: Dict[str, Any]):
        res_id = str(uuid.uuid4())

        # 1. Normalize
        ext_item_id = payload.get("item_id")
        item = self.core.inventory_mapper.get_by_external_id(channel_id, ext_item_id)
        if not item:
            return self._reject(res_id, channel_id, "UNKNOWN_INVENTORY")

        # 2. Privacy Redaction (AEGIS context)
        privacy_level = item.privacy_level
        if privacy_level >= 3:
             payload["guest_name"] = "[REDACTED]"
             payload["guest_email"] = "[REDACTED]"

        # 3. Validation Chain
        # MAC EOS / FCE / ORCA / AEGIS / UT

        # Availability Check
        count = self.core.availability_sync.canonical_availability.get(item.internal_id, 0)
        if count <= 0:
            return self._reject(res_id, channel_id, "NO_AVAILABILITY")

        # Pricing Validation (FCE)
        provided_price = payload.get("total_price")
        if provided_price != item.base_price:
            return self._reject(res_id, channel_id, "PRICE_MISMATCH")

        # Transfer Feasibility (UT)
        if item.transfer_requirements:
             # Mock transfer check
             if payload.get("arrival_time") == "02:00": # Night landing block doctrine
                 return self._reject(res_id, channel_id, "TRANSFER_IMPOSSIBLE_NIGHT_LANDING")

        # High-Value Approval
        if item.base_price >= 10000:
             status = "NEEDS_HUMAN_APPROVAL"
        else:
             status = "READY_TO_CONFIRM"

        # Seal Intake to SHADOW
        actor = self.core.guard.get_actor()
        actor_id = actor.get("identity_id") if actor else "SYSTEM"

        intake_record = {
            "reservation_id": res_id,
            "channel_id": channel_id,
            "status": status,
            "item_id": item.internal_id,
            "payload": payload,
            "timestamp": time.time()
        }
        self.core.shadow.commit("prestige.reservation.intake", actor_id, intake_record)

        return {"status": "success", "reservation_id": res_id, "booking_status": status}

    def _reject(self, res_id: str, channel_id: str, reason: str):
        reject_record = {
            "reservation_id": res_id,
            "channel_id": channel_id,
            "status": "REJECTED_VALIDATION_FAILED",
            "reason": reason,
            "timestamp": time.time()
        }
        self.core.shadow.commit("prestige.reservation.rejected", "SYSTEM", reject_record)
        return {"status": "rejected", "reservation_id": res_id, "reason": reason}

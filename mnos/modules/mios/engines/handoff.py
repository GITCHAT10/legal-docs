from uuid import UUID, uuid4
from typing import List, Dict, Optional
from mnos.modules.mios.schemas.models import AssetHandoff

class MIOSAssetHandoffEngine:
    def __init__(self, shadow):
        self.shadow = shadow
        self.handoffs: Dict[UUID, AssetHandoff] = {}

    def initiate_handoff(self, actor_ctx: dict, shipment_id: UUID, handoff_type: str, sender_id: UUID, receiver_id: UUID) -> AssetHandoff:
        handoff_id = uuid4()
        handoff = AssetHandoff(
            id=handoff_id,
            shipment_id=shipment_id,
            handoff_type=handoff_type,
            sender_id=sender_id,
            receiver_id=receiver_id
        )
        self.handoffs[handoff_id] = handoff
        self.shadow.commit("mios.handoff.initiated", actor_ctx["identity_id"], handoff.dict())
        return handoff

    def verify_handoff(self, actor_ctx: dict, handoff_id: UUID, signature_hash: str, condition: str = "GOOD", damage: bool = False):
        handoff = self.handoffs.get(handoff_id)
        if not handoff:
            raise ValueError("Handoff not found")

        handoff.status = "VERIFIED"
        handoff.condition_status = condition
        handoff.damage_flag = damage

        self.shadow.commit("mios.handoff.verified", actor_ctx["identity_id"], {
            "handoff_id": str(handoff_id),
            "signature_hash": signature_hash,
            "condition": condition,
            "damage": damage
        })
        return handoff

    def is_shipment_delivered(self, shipment_id: UUID) -> bool:
        return any(h.shipment_id == shipment_id and h.handoff_type == "FINAL_DELIVERY" and h.status == "VERIFIED" for h in self.handoffs.values())

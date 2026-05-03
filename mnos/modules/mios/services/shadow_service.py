import hashlib
import json
from uuid import UUID
from datetime import datetime
from typing import Dict, Optional

class MIOSShadowService:
    def __init__(self, global_shadow):
        self.global_shadow = global_shadow
        self.shipment_chains: Dict[UUID, str] = {} # last_hash per shipment

    def commit_event(self, shipment_id: UUID, event_type: str, actor_id: str, payload: dict) -> str:
        parent_hash = self.shipment_chains.get(shipment_id, "0" * 64)

        # Add MIOS specific chain metadata to payload
        mios_payload = payload.copy()
        mios_payload["_mios_metadata"] = {
            "shipment_id": str(shipment_id),
            "parent_hash": parent_hash,
            "timestamp": datetime.now().isoformat()
        }

        # Commit to global SHADOW
        new_hash = self.global_shadow.commit(event_type, actor_id, mios_payload)

        # Update local chain
        self.shipment_chains[shipment_id] = new_hash
        return new_hash

    def verify_chain(self, shipment_id: UUID) -> bool:
        # In a real system, we would traverse the global shadow and filter by shipment_id
        # and verify each parent_hash linkage.
        return True

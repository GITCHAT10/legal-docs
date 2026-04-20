import httpx
import uuid
from typing import Optional, List, Dict, Any
from decimal import Decimal

class AEGISAdapter:
    async def validate_token(self, auth_token: str) -> Dict[str, Any]:
        # Mocking MNOS AEGIS service call
        # In production: response = await httpx.post(f"{MNOS_AEGIS_URL}/validate", json={"token": auth_token})
        # For now, we return a success response for any token that isn't 'invalid'
        if auth_token == "invalid_token":
            return {"valid": False}
        # Deterministic UUIDs for testing consistency
        user_id = "b421e7db-a880-4955-ba06-e99da9607e16"
        tenant_id = "f09be61c-0163-49aa-bee3-17988016b570"

        return {
            "valid": True,
            "aegis_user_id": user_id,
            "tenant_id": tenant_id,
            "status": "ACTIVE",
            "allowed_payment_sources": ["wallet", "card-on-file", "room_folio"]
        }

class FCEAdapter:
    async def settle_autonomous(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Mocking MNOS FCE service call: POST /core/fce/settle/autonomous
        base_amount = Decimal(str(payload["base_amount"]))
        service_charge = base_amount * Decimal("0.10")
        subtotal_after_sc = base_amount + service_charge
        tgst = subtotal_after_sc * Decimal("0.17")
        platform_fee = base_amount * Decimal("0.04") # Assuming 4% for AUTONOMOUS_RETAIL_STANDARD
        grand_total = subtotal_after_sc + tgst

        return {
            "status": "SETTLED",
            "receipt_id": f"INV-{uuid.uuid4().hex[:6].upper()}",
            "settlement_id": str(uuid.uuid4()),
            "breakdown": {
                "base_amount": float(base_amount),
                "service_charge": float(service_charge),
                "tgst": float(tgst),
                "platform_fee": float(platform_fee),
                "operator_net": float(base_amount - platform_fee),
                "grand_total": float(grand_total)
            }
        }

    async def reverse_transaction(self, settlement_id: str) -> Dict[str, Any]:
        # Mocking MNOS FCE service call: POST /core/fce/reverse
        print(f"[FCE] Reversing transaction: {settlement_id}")
        return {
            "status": "REVERSED",
            "reversal_id": str(uuid.uuid4()),
            "original_settlement_id": settlement_id
        }

class SHADOWAdapter:
    async def commit(self, payload: Dict[str, Any]) -> str:
        # Mocking MNOS SHADOW service call: POST /core/shadow/commit
        # Returns a mock shadow hash
        import hashlib
        import json
        content = json.dumps(payload, sort_keys=True)
        shadow_hash = hashlib.sha256(content.encode()).hexdigest()
        return shadow_hash

class EVENTSAdapter:
    async def publish(self, event_type: str, payload: Dict[str, Any]):
        # Mocking MNOS event bus emission
        print(f"[EVENT BUS] Published {event_type}: {payload}")
        return True

class INNAdapter:
    async def resolve_active_folio(self, aegis_user_id: str, tenant_id: str) -> Optional[str]:
        # Mocking MNOS INN service call to check for active room folio
        # In production: response = await httpx.get(f"{MNOS_INN_URL}/folio/active", params={"user_id": aegis_user_id, "tenant_id": tenant_id})

        # Security validation: Ensure user has an active stay
        if aegis_user_id == "unlinked_user":
            return None

        return f"FOLIO-{uuid.uuid4().hex[:6].upper()}"

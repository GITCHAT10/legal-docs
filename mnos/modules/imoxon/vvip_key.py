import uuid
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional

class VVIPKeyEngine:
    """
    VVIP-KEY-SOVEREIGN-ACCESS: Digital Access Key Engine.
    Unlocks real-world luxury assets (Yachts, Villas) for top performers.
    Features: AEGIS Binding, Time-Lock, SHADOW logging, Instant Revoke.
    """
    def __init__(self, core):
        self.core = core
        self.minted_keys = {} # key_id -> key_data
        self.asset_registry = {
            "YACHT-01": {"name": "MIG Sovereign Yacht", "location": "Male Jetty"},
            "VILLA-05": {"name": "Premium Private Villa", "location": "Maafushi"},
            "RESORT-STAY": {"name": "LXR Resort Suite", "location": "Ari Atoll"}
        }

    def mint_vvip_key(self, actor_ctx: dict, recipient_id: str, asset_id: str, duration_hours: int = 72):
        """MIG Action: Reward top performer with a VVIP Key."""
        if actor_ctx.get("role") != "admin":
             raise PermissionError("Only MIG Admin can mint VVIP Keys")

        if asset_id not in self.asset_registry:
             raise ValueError(f"Invalid Asset: {asset_id}")

        key_id = f"VVIP-{datetime.now(UTC).year}-{uuid.uuid4().hex[:6].upper()}"
        valid_from = datetime.now(UTC)
        valid_to = valid_from + timedelta(hours=duration_hours)

        key_data = {
            "key_id": key_id,
            "owner_id": recipient_id,
            "asset_id": asset_id,
            "asset_name": self.asset_registry[asset_id]["name"],
            "valid_from": valid_from.isoformat(),
            "valid_to": valid_to.isoformat(),
            "access_type": "FULL_CONTROL",
            "status": "ACTIVE",
            "signature": "AEGIS_SECURE_SIGN_V1"
        }

        self.minted_keys[key_id] = key_data

        # Record in SHADOW
        self.core.shadow.commit("vvip.key.minted", recipient_id, key_data)
        return key_data

    def verify_access(self, actor_ctx: dict, key_id: str) -> bool:
        """QR/NFC Hardware Verification Simulation."""
        key = self.minted_keys.get(key_id)
        if not key: return False

        # 1. AEGIS Binding Check (Non-transferable)
        if key["owner_id"] != actor_ctx["identity_id"]:
             self.core.shadow.commit("vvip.access.denied", actor_ctx["identity_id"], {"reason": "Owner Mismatch", "key": key_id})
             return False

        # 2. Time-Lock Check
        now = datetime.now(UTC)
        if now < datetime.fromisoformat(key["valid_from"]) or now > datetime.fromisoformat(key["valid_to"]):
             key["status"] = "EXPIRED"
             return False

        # 3. Status Check
        if key["status"] != "ACTIVE":
             return False

        # 4. Success: Record Access in SHADOW
        self.core.shadow.commit("vvip.access.granted", actor_ctx["identity_id"], {"key_id": key_id, "asset": key["asset_id"]})
        return True

    def revoke_key(self, actor_ctx: dict, key_id: str):
        if actor_ctx.get("role") != "admin":
             raise PermissionError("Unauthorized to revoke key")

        if key_id in self.minted_keys:
             self.minted_keys[key_id]["status"] = "REVOKED"
             self.core.shadow.commit("vvip.key.revoked", key_id, {"by": actor_ctx["identity_id"]})
             return True
        return False

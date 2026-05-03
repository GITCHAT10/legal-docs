from mnos.shared.execution_guard import set_system_context

class AegisIdentityCore:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.profiles = {}
        self.devices = {}

    def create_profile(self, profile: dict) -> str:
        set_system_context()
        try:
            identity_id = f"AEGIS-{uuid.uuid4().hex[:8]}"
            profile["identity_id"] = identity_id
            profile["verification_status"] = "unverified"
            profile["persistent_identity_hash"] = hashlib.sha256(identity_id.encode()).hexdigest()
            profile["created_at"] = datetime.now(UTC).isoformat()
            profile["assigned_island"] = None
            profile["external_ref"] = None

            self.profiles[identity_id] = profile
            self.shadow.commit("IDENTITY_CREATED", identity_id, profile)
            self.events.publish("IDENTITY_CREATED", profile)
            return identity_id
        finally:
            from mnos.shared.execution_guard import _sovereign_context
            _sovereign_context.set(None)

    def bind_device(self, identity_id: str, device_info: dict) -> str:
        set_system_context()
        try:
            if identity_id not in self.profiles:
                raise ValueError("Identity not found")

            device_id = f"DEV-{uuid.uuid4().hex[:8]}"
            device = {
                "device_id": device_id,
                "identity_id": identity_id,
                "device_type": device_info.get("type", "UNKNOWN"),
                "trusted": True,
                "last_handshake": datetime.now(UTC).isoformat()
            }
            self.devices[device_id] = device
            self.shadow.commit("DEVICE_BOUND", identity_id, device)
            return device_id
        finally:
            from mnos.shared.execution_guard import _sovereign_context
            _sovereign_context.set(None)

import uuid
import hashlib
from datetime import datetime, UTC

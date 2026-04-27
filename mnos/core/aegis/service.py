from typing import Dict, Optional
from mnos.core.aegis_identity.identity import AegisIdentityCore

class AegisSovereignService:
    """
    AEGIS Identity & Device Binding Service for SALA Node.
    Wraps the core identity logic for sovereign execution.
    """
    def __init__(self, identity_core: AegisIdentityCore):
        self.core = identity_core

    def verify_actor(self, identity_id: str, device_id: str) -> bool:
        profile = self.core.profiles.get(identity_id)
        if not profile:
            return False

        device = self.core.devices.get(device_id)
        if not device or device.get("identity_id") != identity_id:
            return False

        return True

    def get_actor_role(self, identity_id: str) -> str:
        profile = self.core.profiles.get(identity_id)
        return profile.get("profile_type", "guest") if profile else "guest"

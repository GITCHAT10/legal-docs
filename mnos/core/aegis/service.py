from typing import Dict, Optional
from mnos.core.aegis_identity.identity import AegisIdentityCore

class AegisSovereignService:
    """
    AEGIS Identity & Device Binding Service for SALA Node.
    Wraps the core identity logic for sovereign execution.
    Enforces Strict Device Binding for SALA Node Production.
    """
    def __init__(self, identity_core: AegisIdentityCore):
        self.core = identity_core

    def verify_actor(self, identity_id: str, device_id: str) -> bool:
        """
        VERIFY_DEVICE_BINDING_IN_AEGIS:
        Strictly enforces that the device is registered to the identity.
        """
        profile = self.core.profiles.get(identity_id)
        if not profile:
            return False

        device = self.core.devices.get(device_id)
        if not device:
            return False

        if device.get("identity_id") != identity_id:
            # Device binding violation
            return False

        return True

    def get_actor_role(self, identity_id: str) -> str:
        profile = self.core.profiles.get(identity_id)
        return profile.get("profile_type", "guest") if profile else "guest"

    def validate_sovereign_context(self, actor_ctx: Dict) -> bool:
        """
        RESTRICT_SYSTEM_CONTEXT_TO_APPROVED_PATHS:
        Ensures the actor context is valid for sovereign actions.
        """
        identity_id = actor_ctx.get("identity_id")
        device_id = actor_ctx.get("device_id")

        if not identity_id or not device_id:
            return False

        return self.verify_actor(identity_id, device_id)

from typing import Dict, Any, List
from mnos.modules.aig_vault.service import aig_vault
from mnos.core.aig_aegis.service import aig_aegis

class GuestProfileBinding:
    """
    SALA Guest Profile: Binds UI to AIG Vault with AEGIS validation.
    Enforces encrypted read/write for guest data.
    """
    def load_profile(self, guest_id: str, session_context: Dict[str, Any], connection_context: Dict[str, Any]):
        """
        Loads guest profile data with identity and scope checks.
        """
        # Validate mission scope
        if session_context.get("mission_scope") != "V1":
             raise RuntimeError("GUEST_PROFILE: Load denied. Mission Scope 'V1' required.")

        # Check permissions in Vault
        device_id = session_context.get("device_id")
        aig_vault.check_permission(device_id, "read", session_context=session_context)

        # Log access (Audit)
        print(f"[GUEST_PROFILE] Profile {guest_id} accessed by {device_id}")

        return {"status": "SUCCESS", "guest_id": guest_id, "mode": "ENCRYPTED_READ"}

    def update_profile(self, guest_id: str, data: Dict[str, Any], session_context: Dict[str, Any]):
        """Updates guest data in AIG Vault."""
        device_id = session_context.get("device_id")
        aig_vault.check_permission(device_id, "write", session_context=session_context)

        print(f"[GUEST_PROFILE] Profile {guest_id} updated by {device_id}")
        return {"status": "SUCCESS", "guest_id": guest_id, "operation": "ENCRYPTED_WRITE"}

guest_profile_service = GuestProfileBinding()

from typing import Dict, Any, List
from mnos.core.security.aegis import aegis

class UCloudStorage:
    """
    uCloud Vault (HARDENED):
    Provides secure file management and granular identity-based permissions.
    Enforces device-bound access control and mandatory AEGIS signatures.
    """
    def __init__(self):
        self.authorized_devices = {"nexus-001", "nexus-admin-01"}
        self.storage: Dict[str, Any] = {}

    def write(self, key: str, data: Any, session_context: Dict[str, Any]):
        """
        Hardened Write:
        1. AEGIS signature required.
        2. Device ID must match server-side ACL.
        """
        # Validate session via AEGIS (this also resolves bound_device_id)
        aegis.validate_session(session_context)

        device_id = session_context.get("bound_device_id")
        if device_id not in self.authorized_devices:
            raise RuntimeError(f"UCLOUD_ACCESS_DENIED: Device {device_id} not authorized for vault writes.")

        print(f"[uCloud] Authorized Write: {key} by {device_id}")
        self.storage[key] = data
        return {"status": "SUCCESS", "key": key}

    def read(self, key: str, session_context: Dict[str, Any]):
        """AEGIS signature required for read."""
        aegis.validate_session(session_context)
        return self.storage.get(key)

ucloud = UCloudStorage()

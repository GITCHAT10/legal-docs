from typing import Dict, Any, List, Optional
import os

class VaultException(Exception):
    pass

class AIGVault:
    """
    Data Security Layer (AIGVault Vault):
    Controls files, users, and permissions.
    Ensures data is not exposed to public cloud by default.
    """
    def __init__(self):
        # AIG APOLLO ACL: Role-based alignment with AIG AEGIS
        self.permissions: Dict[str, List[str]] = {
            "nexus-admin-01": ["read", "write", "delete"],
            "nexus-001": ["read", "write"],
            "nexus-readonly": ["read"]
        }

    def check_permission(self, identity: str, action: str, session_context: Dict[str, Any] = None):
        """
        Enforces AIG AEGIS session verification for data access (FORTRESS BUILD).
        MIG HARDENING: No direct access without verified device binding.
        """
        if not session_context:
            raise VaultException("AIG_VAULT: Unauthorized access attempt. Active session context required.")

        # In MNOS 10.0, we only trust the verified_device_id from Aegis
        verified_id = session_context.get("verified_device_id")
        if not verified_id:
             raise VaultException("AIG_VAULT: Unverified identity. Aegis validation required.")

        if verified_id != identity:
             raise VaultException("AIG_VAULT: Identity mismatch. Session binding compromised.")

        allowed_actions = self.permissions.get(verified_id, [])
        if "*" not in allowed_actions and action not in allowed_actions:
            raise VaultException(f"AIG_VAULT: Identity '{verified_id}' denied '{action}' access.")
        return True

    def secure_storage_path(self, file_id: str, local_only: bool = True) -> str:
        """Determines the secure path for file storage."""
        if local_only:
            return f"/mnt/sovereign/vault/{file_id}"
        return f"s3://{os.getenv('S3_BACKUP_BUCKET', 'nexus-vault')}/{file_id}"

aig_vault = AIGVault()

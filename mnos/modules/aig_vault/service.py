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
        # AIG APOLLO ACL: Role and Device-based alignment with AIG AEGIS
        self.permissions: Dict[str, List[str]] = {
            "nexus-admin": ["read", "write", "delete"],
            "nexus-operator": ["read", "write"],
            "nexus-guest": ["read"],
            "system-gateway": ["read", "write"],
            # Explicit Device ID alignment for RC2 Production Blockers
            "nexus-001": ["read", "write"],
            "nexus-admin-01": ["read", "write", "delete"]
        }

    def check_permission(self, identity: str, action: str, session_context: Dict[str, Any] = None):
        """
        Enforces AIG AEGIS session verification for data access (FORTRESS BUILD).
        MIG HARDENING: Authorize based on role, log based on device.
        """
        if not session_context:
            raise VaultException("AIG_VAULT: Unauthorized access attempt. Active session context required.")

        # Resolve Actor Role
        verified_id = session_context.get("verified_device_id")
        resolved_role = session_context.get("resolved_role", "unknown")

        if not verified_id:
             raise VaultException("AIG_VAULT: Unverified device. Aegis validation required.")

        # PRODUCTION RULE: Check permission based on RESOLVED ROLE
        allowed_actions = self.permissions.get(resolved_role, [])
        if "*" not in allowed_actions and action not in allowed_actions:
            # Fallback to direct identity check for legacy support
            allowed_actions = self.permissions.get(verified_id, [])
            if "*" not in allowed_actions and action not in allowed_actions:
                raise VaultException(f"AIG_VAULT: Identity '{verified_id}' [Role: {resolved_role}] denied '{action}' access.")

        print(f"[AIG_VAULT] PERMISSION_GRANTED: Device={verified_id} Role={resolved_role} Action={action}")
        return True

    def secure_storage_path(self, file_id: str, local_only: bool = True) -> str:
        """Determines the secure path for file storage."""
        if local_only:
            return f"/mnt/sovereign/vault/{file_id}"
        return f"s3://{os.getenv('S3_BACKUP_BUCKET', 'nexus-vault')}/{file_id}"

aig_vault = AIGVault()

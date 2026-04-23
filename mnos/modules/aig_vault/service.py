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
            "nexus-admin-01": ["*"], # Full Sovereign Control
            "ut-dispatch-01": ["read", "write"],
            "nexus-001": ["read", "write"]
        }

    def check_permission(self, identity: str, action: str):
        allowed_actions = self.permissions.get(identity, [])
        if action not in allowed_actions:
            raise VaultException(f"AIG_VAULT: Identity '{identity}' denied '{action}' access.")
        return True

    def secure_storage_path(self, file_id: str, local_only: bool = True) -> str:
        """Determines the secure path for file storage."""
        if local_only:
            return f"/mnt/sovereign/vault/{file_id}"
        return f"s3://{os.getenv('S3_BACKUP_BUCKET', 'nexus-vault')}/{file_id}"

aig_vault = AIGVault()

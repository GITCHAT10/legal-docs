from typing import Dict, Any, List, Optional
import os

class VaultException(Exception):
    pass

class UCloudVault:
    """
    Data Security Layer (uCloud Vault):
    Controls files, users, and permissions.
    Ensures data is not exposed to public cloud by default.
    """
    def __init__(self):
        # In-memory mock for demonstration: Aligning with AEGIS device IDs
        self.permissions: Dict[str, List[str]] = {
            "nexus-admin-01": ["read", "write", "delete"],
            "ut-dispatch-01": ["read", "write"],
            "nexus-001": ["read"]
        }

    def check_permission(self, identity: str, action: str):
        allowed_actions = self.permissions.get(identity, [])
        if action not in allowed_actions:
            raise VaultException(f"UCLOUD: Identity '{identity}' denied '{action}' access.")
        return True

    def secure_storage_path(self, file_id: str, local_only: bool = True) -> str:
        """Determines the secure path for file storage."""
        if local_only:
            return f"/mnt/sovereign/vault/{file_id}"
        return f"s3://{os.getenv('S3_BACKUP_BUCKET', 'nexus-vault')}/{file_id}"

ucloud = UCloudVault()

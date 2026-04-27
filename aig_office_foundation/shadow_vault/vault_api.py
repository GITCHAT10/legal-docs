import uuid
from typing import List, Dict, Any
from .encryption import VaultEncryption
from .object_store import ObjectStore
from .file_metadata import create_file_metadata
from .sharing_policy import SharingPolicy

class ShadowVault:
    """
    SHADOW VAULT: Secure Sovereign Storage.
    Integrated with AEGIS and SHADOW AUDIT.
    """
    def __init__(self, shadow_ledger):
        self.encryption = VaultEncryption()
        self.object_store = ObjectStore()
        self.sharing_policy = SharingPolicy()
        self.shadow_ledger = shadow_ledger
        self.files = {} # file_id -> metadata
        self.keys = {}  # file_id -> encryption_key

    def upload_file(self, actor_payload: dict, filename: str, data: bytes, trace_id: str) -> str:
        file_id = str(uuid.uuid4())
        key = self.encryption.generate_key()
        encrypted_data = self.encryption.encrypt(data, key)

        self.object_store.put_object(file_id, encrypted_data)

        metadata = create_file_metadata(file_id, actor_payload["identity_id"], filename, len(data))
        self.files[file_id] = metadata
        self.keys[file_id] = key

        # Audit
        self.shadow_ledger.commit("vault.file.uploaded",
                                   actor_payload["identity_id"],
                                   actor_payload["device_id"],
                                   trace_id,
                                   {"file_id": file_id, "filename": filename})

        return file_id

    def download_file(self, actor_payload: dict, file_id: str, trace_id: str) -> bytes:
        metadata = self.files.get(file_id)
        if not metadata:
            raise FileNotFoundError("File not found")

        if not self.sharing_policy.has_access(file_id, actor_payload["identity_id"], metadata["owner_id"]):
            raise PermissionError("Access denied to file")

        encrypted_data = self.object_store.get_object(file_id)
        decrypted_data = self.encryption.decrypt(encrypted_data, self.keys[file_id])

        # Audit
        self.shadow_ledger.commit("vault.file.downloaded",
                                   actor_payload["identity_id"],
                                   actor_payload["device_id"],
                                   trace_id,
                                   {"file_id": file_id})

        return decrypted_data

    def share_file(self, actor_payload: dict, file_id: str, target_identity_id: str, trace_id: str):
        metadata = self.files.get(file_id)
        if not metadata or metadata["owner_id"] != actor_payload["identity_id"]:
            raise PermissionError("Only owner can share file")

        self.sharing_policy.share_file(file_id, target_identity_id)

        # Audit
        self.shadow_ledger.commit("vault.file.shared",
                                   actor_payload["identity_id"],
                                   actor_payload["device_id"],
                                   trace_id,
                                   {"file_id": file_id, "target": target_identity_id})

    def delete_file(self, actor_payload: dict, file_id: str, trace_id: str):
        metadata = self.files.get(file_id)
        if not metadata or metadata["owner_id"] != actor_payload["identity_id"]:
             raise PermissionError("Only owner can delete file")

        self.object_store.delete_object(file_id)
        del self.files[file_id]
        del self.keys[file_id]

        # Audit
        self.shadow_ledger.commit("vault.file.deleted",
                                   actor_payload["identity_id"],
                                   actor_payload["device_id"],
                                   trace_id,
                                   {"file_id": file_id})

    def list_files(self, actor_payload: dict) -> List[dict]:
        visible_files = []
        for file_id, metadata in self.files.items():
            if self.sharing_policy.has_access(file_id, actor_payload["identity_id"], metadata["owner_id"]):
                visible_files.append(metadata)
        return visible_files

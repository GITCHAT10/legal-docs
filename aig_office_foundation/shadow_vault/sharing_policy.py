from typing import Dict, List

class SharingPolicy:
    def __init__(self):
        self.shares = {} # file_id -> [identity_id]

    def share_file(self, file_id: str, target_identity_id: str):
        if file_id not in self.shares:
            self.shares[file_id] = []
        if target_identity_id not in self.shares[file_id]:
            self.shares[file_id].append(target_identity_id)

    def has_access(self, file_id: str, identity_id: str, owner_id: str) -> bool:
        if identity_id == owner_id:
            return True
        allowed_users = self.shares.get(file_id, [])
        return identity_id in allowed_users

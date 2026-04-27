from typing import Dict, List, Optional

class RolePolicy:
    def __init__(self):
        # Deny by default
        self.roles = {
            "admin": ["vault_write", "vault_read", "vault_share", "vault_delete", "audit_read"],
            "staff": ["vault_write", "vault_read", "vault_share"],
            "viewer": ["vault_read"]
        }

    def can_perform(self, role: str, action: str) -> bool:
        allowed_actions = self.roles.get(role, [])
        return action in allowed_actions

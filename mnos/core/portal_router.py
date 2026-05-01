import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

class UPortalRouter:
    """
    UPOS Multi-Portal Login & Access Routing.
    Handles B2C, B2B, B2G, B2E, B2O, B2A, and Super Admin routing.
    RESORT-FIRST logic prioritized.
    """
    def __init__(self, identity_core, orca):
        self.identity = identity_core
        self.orca = orca
        self.sessions = {}

    def get_portal_for_role(self, role: str) -> str:
        # Resort-First Priority Mapping
        role_to_portal = {
            "admin": "/app/enterprise",
            "procurement_manager": "/app/procurement",
            "finance_manager": "/app/finance",
            "resort_gm": "/app/enterprise",
            "storekeeper": "/app/stores",
            "executive_chef": "/app/fnb",
            "fnb_manager": "/app/fnb",
            "marine_manager": "/app/marine",
            "it_manager": "/app/wifi",
            "logistics_operator": "/app/logistics",
            "captain": "/app/logistics",
            "vendor": "/app/business",
            "customer": "/app/customer",
            "guest": "/app/customer"
        }
        return role_to_portal.get(role, "/login")

    def login(self, actor_ctx: dict):
        identity_id = actor_ctx.get("identity_id")
        role = actor_ctx.get("role")

        if not identity_id or not role:
             raise PermissionError("AUTH_FAILED: Missing identity or role")

        # ORCA validation
        valid, msg = self.orca.validate_action("auth.login", actor_ctx)
        if not valid:
             raise PermissionError(f"LOGIN_BLOCKED: {msg}")

        session_id = f"SES-{uuid.uuid4().hex[:12].upper()}"
        self.sessions[session_id] = {
            "identity_id": identity_id,
            "role": role,
            "portal": self.get_portal_for_role(role),
            "created_at": datetime.now(UTC).isoformat()
        }

        return {
            "session_id": session_id,
            "portal": self.sessions[session_id]["portal"],
            "status": "AUTHORIZED"
        }

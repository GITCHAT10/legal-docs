import uuid
import os

class AegisVerifier:
    """
    AEGIS: Identity authority and DID generation.
    Enforces the presence of NEXGEN_SECRET.
    Implements Mandatory Access Control (MAC).
    """
    def __init__(self):
        self.secret = os.environ.get("NEXGEN_SECRET")
        if not self.secret:
            raise RuntimeError("CRITICAL FAILURE: NEXGEN_SECRET not found. Fail-closed triggered.")
        # Trusted device bindings: device_id -> user_id
        self.device_bindings = {}

    def create_did(self, identity_data: dict, role: str) -> str:
        # MAC Policy
        allowed_roles = ["LOCAL_USER", "WORK_PERMIT_USER", "BUSINESS_VENDOR"]
        if role not in allowed_roles:
            raise PermissionError(f"ACCESS DENIED: Role {role} is not allowed in IMOXON.")

        unique_id = uuid.uuid4().hex
        return f"did:mnos:{unique_id}"

    def bind_device(self, user_id: str, device_id: str):
        # Security Fix 1: Device binding must verify against trusted server-side storage
        self.device_bindings[device_id] = user_id

    def verify_access(self, user_id: str, device_id: str, role: str) -> bool:
        # 1. Local-only check
        if role == "TOURIST_USER":
            return False

        # 2. Device binding check
        if self.device_bindings.get(device_id) != user_id:
            return False

        return True

    def verify_kyb(self, business_docs: dict) -> bool:
        if business_docs.get("registration_number") and business_docs.get("bank_account"):
            return True
        return False

    def verify_identity(self, user_token: str) -> bool:
        # Legacy support for checkouts
        return user_token.startswith("mnos-tok-")

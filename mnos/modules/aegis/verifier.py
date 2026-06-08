import uuid
import os

class AegisVerifier:
    def __init__(self):
        self.secret = os.environ.get("NEXGEN_SECRET")
        if not self.secret:
            raise RuntimeError("CRITICAL FAILURE: NEXGEN_SECRET not found.")
        self.device_bindings = {}

    def create_did(self, identity_data: dict, role: str) -> str:
        # Supply Roles Supported
        allowed_roles = [
            "LOCAL_USER", "WORK_PERMIT_USER", "BUSINESS_VENDOR",
            "RESORT_REQUESTER", "SUPPLIER_OPERATOR", "DELIVERY_CAPTAIN", "WAREHOUSE_OPERATOR"
        ]
        if role not in allowed_roles:
            raise PermissionError(f"ACCESS DENIED: Role {role} is not allowed.")

        unique_id = uuid.uuid4().hex
        return f"did:mnos:{unique_id}"

    def bind_device(self, user_id: str, device_id: str):
        self.device_bindings[device_id] = user_id

    def verify_access(self, user_id: str, device_id: str, role: str) -> bool:
        if role == "TOURIST_USER":
            return False
        if self.device_bindings.get(device_id) != user_id:
            return False
        return True

    def verify_kyb(self, business_docs: dict) -> bool:
        return True

    def verify_identity(self, user_token: str) -> bool:
        return user_token.startswith("mnos-tok-")

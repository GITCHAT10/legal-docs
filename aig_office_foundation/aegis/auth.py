import uuid
from .device_registry import DeviceRegistry
from .jwt_tokens import JwtManager
from .role_policy import RolePolicy

class AegisAuth:
    """
    AEGIS Identity: The Root Gate for AIG Office.
    """
    def __init__(self, jwt_secret: str):
        self.device_registry = DeviceRegistry()
        self.jwt_manager = JwtManager(jwt_secret)
        self.role_policy = RolePolicy()
        self.identities = {} # username -> {identity_id, password, role}

    def register_identity(self, username: str, password: str, role: str) -> str:
        identity_id = str(uuid.uuid4())
        self.identities[username] = {
            "identity_id": identity_id,
            "password": password,
            "role": role
        }
        return identity_id

    def login(self, username: str, password: str, device_id: str) -> str:
        identity = self.identities.get(username)
        if not identity or identity["password"] != password:
            raise PermissionError("AEGIS: Invalid credentials")

        # SERVER_SIDE_DEVICE_BINDING_ONLY
        if not self.device_registry.verify_device_binding(device_id, identity["identity_id"]):
            raise PermissionError("AEGIS: Unauthorized device")

        return self.jwt_manager.issue_token(identity["identity_id"], device_id, identity["role"])

    def validate_request(self, token: str, required_action: str) -> dict:
        payload = self.jwt_manager.validate_token(token)
        if not payload:
            raise PermissionError("AEGIS: Invalid or expired token")

        if not self.role_policy.can_perform(payload["role"], required_action):
            raise PermissionError(f"AEGIS: Insufficient permissions for {required_action}")

        return payload

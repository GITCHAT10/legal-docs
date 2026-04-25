class AegisAdapter:
    def __init__(self, verifier):
        self.verifier = verifier

    def authorize(self, user_id: str, device_id: str, role: str):
        # Mandatory Local-Only Gate
        if not self.verifier.verify_access(user_id, device_id, role):
            raise PermissionError("ACCESS_DENIED: LOCAL_ONLY_SYSTEM_ENFORCED")
        return True

    def register_actor(self, data: dict, role: str):
        if role == "BUSINESS_VENDOR" and not self.verifier.verify_kyb(data):
            raise ValueError("AEGIS: KYB_FAILED")
        return self.verifier.create_did(data, role)

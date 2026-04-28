import uuid
from datetime import datetime, UTC

class AegisIdentityCore:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events
        self.profiles = {}
        self.devices = {}
        self.roles = {}
        self.consents = {}
        self.verifications = {}
        self.bindings = {} # asset bindings

    def create_profile(self, profile_data: dict, trace_id: str = None) -> str:
        identity_id = str(uuid.uuid4())
        profile = {
            "identity_id": identity_id,
            "profile_type": profile_data.get("profile_type"), # staff, supplier, etc
            "external_ref": profile_data.get("external_ref"),
            "full_name": profile_data.get("full_name"),
            "organization_id": profile_data.get("organization_id"),
            "assigned_island": profile_data.get("assigned_island"), # For Island GMs
            "persistent_identity_hash": uuid.uuid4().hex, # Hardened identity hash
            "verification_status": "pending",
            "identity_status": "active",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.profiles[identity_id] = profile

        tid = trace_id or f"TR-ID-{uuid.uuid4().hex[:6]}"
        self.shadow.commit("identity.created", identity_id, profile, trace_id=tid)
        self.events.publish("IDENTITY_CREATED", profile)
        return identity_id

    def bind_device(self, identity_id: str, device_data: dict, trace_id: str = None) -> str:
        device_id = str(uuid.uuid4())
        device = {
            "device_id": device_id,
            "identity_id": identity_id,
            "device_fingerprint_hash": device_data.get("fingerprint"),
            "trust_level": "medium",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.devices[device_id] = device

        tid = trace_id or f"TR-DEV-{uuid.uuid4().hex[:6]}"
        self.shadow.commit("identity.device.bound", identity_id, device, trace_id=tid)
        return device_id

    def assign_role(self, identity_id: str, role_name: str, scope: dict, trace_id: str = None) -> str:
        binding_id = str(uuid.uuid4())
        role_binding = {
            "binding_id": binding_id,
            "identity_id": identity_id,
            "role_name": role_name,
            "scope": scope,
            "is_active": True
        }
        self.roles[binding_id] = role_binding
        tid = trace_id or f"TR-ROLE-{uuid.uuid4().hex[:6]}"
        self.shadow.commit("identity.role.assigned", identity_id, role_binding, trace_id=tid)
        return binding_id

    def record_consent(self, identity_id: str, consent_type: str, trace_id: str = None) -> str:
        consent_id = str(uuid.uuid4())
        consent = {
            "consent_id": consent_id,
            "identity_id": identity_id,
            "consent_type": consent_type,
            "granted": True,
            "granted_at": datetime.now(UTC).isoformat()
        }
        self.consents[consent_id] = consent
        tid = trace_id or f"TR-CONSENT-{uuid.uuid4().hex[:6]}"
        self.shadow.commit("identity.consent.recorded", identity_id, consent, trace_id=tid)
        return consent_id

    def verify_identity(self, identity_id: str, verifier_id: str, method: str = "document", trace_id: str = None):
        if identity_id in self.profiles:
            self.profiles[identity_id]["verification_status"] = "verified"
            verification = {
                "verification_id": str(uuid.uuid4()),
                "identity_id": identity_id,
                "verifier_id": verifier_id,
                "method": method,
                "verified_at": datetime.now(UTC).isoformat()
            }
            self.verifications[identity_id] = verification
            tid = trace_id or f"TR-VERIFY-{uuid.uuid4().hex[:6]}"
            self.shadow.commit("identity.verified", identity_id, verification, trace_id=tid)
            return True
        return False

    def bind_asset(self, identity_id: str, asset_type: str, asset_ref: str, trace_id: str = None):
        binding_id = str(uuid.uuid4())
        binding = {
            "binding_id": binding_id,
            "identity_id": identity_id,
            "asset_type": asset_type,
            "asset_ref": asset_ref,
            "bound_at": datetime.now(UTC).isoformat()
        }
        self.bindings[binding_id] = binding
        tid = trace_id or f"TR-ASSET-{uuid.uuid4().hex[:6]}"
        self.shadow.commit("identity.asset.bound", identity_id, binding, trace_id=tid)
        return binding_id

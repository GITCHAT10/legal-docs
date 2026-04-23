import uuid
from datetime import datetime, UTC
from typing import List, Optional, Dict

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

    def create_profile(self, profile_data: dict) -> str:
        identity_id = str(uuid.uuid4())
        profile = {
            "identity_id": identity_id,
            "profile_type": profile_data.get("profile_type"), # staff, supplier, etc
            "external_ref": profile_data.get("external_ref"),
            "full_name": profile_data.get("full_name"),
            "organization_id": profile_data.get("organization_id"),
            "verification_status": "pending",
            "identity_status": "active",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.profiles[identity_id] = profile
        self.shadow.commit("identity.created", profile)
        self.events.publish("IDENTITY_CREATED", profile)
        return identity_id

    def bind_device(self, identity_id: str, device_data: dict) -> str:
        device_id = str(uuid.uuid4())
        device = {
            "device_id": device_id,
            "identity_id": identity_id,
            "device_fingerprint_hash": device_data.get("fingerprint"),
            "trust_level": "medium",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.devices[device_id] = device
        self.shadow.commit("identity.device.bound", device)
        return device_id

    def assign_role(self, identity_id: str, role_name: str, scope: dict) -> str:
        binding_id = str(uuid.uuid4())
        role_binding = {
            "binding_id": binding_id,
            "identity_id": identity_id,
            "role_name": role_name,
            "scope": scope,
            "is_active": True
        }
        self.roles[binding_id] = role_binding
        self.shadow.commit("identity.role.assigned", role_binding)
        return binding_id

    def record_consent(self, identity_id: str, consent_type: str) -> str:
        consent_id = str(uuid.uuid4())
        consent = {
            "consent_id": consent_id,
            "identity_id": identity_id,
            "consent_type": consent_type,
            "granted": True,
            "granted_at": datetime.now(UTC).isoformat()
        }
        self.consents[consent_id] = consent
        self.shadow.commit("identity.consent.recorded", consent)
        return consent_id

    def verify_identity(self, identity_id: str, verifier_id: str, method: str = "document"):
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
            self.shadow.commit("identity.verified", verification)
            return True
        return False

    def bind_asset(self, identity_id: str, asset_type: str, asset_ref: str):
        binding_id = str(uuid.uuid4())
        binding = {
            "binding_id": binding_id,
            "identity_id": identity_id,
            "asset_type": asset_type,
            "asset_ref": asset_ref,
            "bound_at": datetime.now(UTC).isoformat()
        }
        self.bindings[binding_id] = binding
        self.shadow.commit("identity.asset.bound", binding)
        return binding_id

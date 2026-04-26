import uuid
from datetime import datetime, UTC
from mnos.db.session import SessionLocal
from mnos.db.schema import AegisIdentityProfile, AegisIdentityDevice, AegisIdentityRole, AegisIdentityConsent, AegisIdentityVerification, AegisAssetBinding

class AegisIdentityCore:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def create_profile(self, profile_data: dict) -> str:
        identity_id = uuid.uuid4()
        with SessionLocal() as db:
            profile = AegisIdentityProfile(
                identity_id=identity_id,
                profile_type=profile_data.get("profile_type"),
                external_ref=profile_data.get("external_ref"),
                full_name=profile_data.get("full_name"),
                organization_id=profile_data.get("organization_id") if profile_data.get("organization_id") else None,
                verification_status="pending",
                identity_status="active"
            )
            db.add(profile)
            db.commit()

        profile_dict = {
            "identity_id": str(identity_id),
            "profile_type": profile_data.get("profile_type"),
            "full_name": profile_data.get("full_name"),
            "verification_status": "pending",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.shadow.commit("identity.created", str(identity_id), profile_dict)
        self.events.publish("IDENTITY_CREATED", profile_dict)
        return str(identity_id)

    def bind_device(self, identity_id: str, device_data: dict) -> str:
        device_id = uuid.uuid4()
        with SessionLocal() as db:
            device = AegisIdentityDevice(
                device_id=device_id,
                identity_id=uuid.UUID(identity_id),
                device_fingerprint_hash=device_data.get("fingerprint"),
                trust_level="medium"
            )
            db.add(device)
            db.commit()

        device_dict = {
            "device_id": str(device_id),
            "identity_id": identity_id,
            "trust_level": "medium",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.shadow.commit("identity.device.bound", identity_id, device_dict)
        return str(device_id)

    def assign_role(self, identity_id: str, role_name: str, scope: dict) -> str:
        binding_id = uuid.uuid4()
        with SessionLocal() as db:
            role_binding = AegisIdentityRole(
                binding_id=binding_id,
                identity_id=uuid.UUID(identity_id),
                role_name=role_name,
                scope_type=scope.get("type"),
                scope_ref=uuid.UUID(scope.get("ref")) if scope.get("ref") else None,
                is_active=True
            )
            db.add(role_binding)
            db.commit()

        role_dict = {
            "binding_id": str(binding_id),
            "identity_id": identity_id,
            "role_name": role_name,
            "scope": scope,
            "is_active": True
        }
        self.shadow.commit("identity.role.assigned", identity_id, role_dict)
        return str(binding_id)

    def record_consent(self, identity_id: str, consent_type: str) -> str:
        consent_id = uuid.uuid4()
        with SessionLocal() as db:
            consent = AegisIdentityConsent(
                consent_id=consent_id,
                identity_id=uuid.UUID(identity_id),
                consent_type=consent_type,
                granted=True,
                granted_at=datetime.now(UTC)
            )
            db.add(consent)
            db.commit()

        consent_dict = {
            "consent_id": str(consent_id),
            "identity_id": identity_id,
            "consent_type": consent_type,
            "granted": True,
            "granted_at": datetime.now(UTC).isoformat()
        }
        self.shadow.commit("identity.consent.recorded", identity_id, consent_dict)
        return str(consent_id)

    def verify_identity(self, identity_id: str, verifier_id: str, method: str = "document"):
        with SessionLocal() as db:
            profile = db.query(AegisIdentityProfile).filter(AegisIdentityProfile.identity_id == uuid.UUID(identity_id)).first()
            if profile:
                profile.verification_status = "verified"
                verification = AegisIdentityVerification(
                    verification_id=uuid.uuid4(),
                    identity_id=uuid.UUID(identity_id),
                    verification_method=method,
                    verifier_identity_id=uuid.UUID(verifier_id) if verifier_id != "SYSTEM" else None,
                    verification_result="verified"
                )
                db.add(verification)
                db.commit()

                verification_dict = {
                    "verification_id": str(verification.verification_id),
                    "identity_id": identity_id,
                    "verifier_id": verifier_id,
                    "method": method,
                    "verified_at": datetime.now(UTC).isoformat()
                }
                self.shadow.commit("identity.verified", identity_id, verification_dict)
                return True
        return False

    def bind_asset(self, identity_id: str, asset_type: str, asset_ref: str):
        binding_id = uuid.uuid4()
        with SessionLocal() as db:
            binding = AegisAssetBinding(
                binding_id=binding_id,
                identity_id=uuid.UUID(identity_id),
                asset_type=asset_type,
                asset_ref=asset_ref,
                binding_status="active"
            )
            db.add(binding)
            db.commit()

        binding_dict = {
            "binding_id": str(binding_id),
            "identity_id": identity_id,
            "asset_type": asset_type,
            "asset_ref": asset_ref,
            "bound_at": datetime.now(UTC).isoformat()
        }
        self.shadow.commit("identity.asset.bound", identity_id, binding_dict)
        return str(binding_id)

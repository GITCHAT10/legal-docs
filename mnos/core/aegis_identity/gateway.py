import uuid
from typing import Optional

class AegisIdentityGateway:
    """
    AEGIS Identity Gateway: Unified Multi-Model Entry Point.
    One gateway with many controlled doors (Realms).
    Realms: D2C, B2B, B2B2C, B2E, B2G, G2C, G2G, VENDOR, ISLAND_GM
    Auth Methods: PHONE_OTP, EMAIL, OPENID_CONNECT, EFAAS, NATIONAL_ID, HARDWARE_BOUND_AEGIS
    """
    def __init__(self, identity_core, shadow):
        self.identity_core = identity_core
        self.shadow = shadow
        self.sessions = {} # session_id -> actor_ctx
        self.realms = ["D2C", "B2B", "B2B2C", "B2E", "B2G", "G2C", "G2G", "VENDOR", "ISLAND_GM"]

    def login(self, realm: str, auth_method: str, credentials: dict) -> dict:
        """Unified login logic for all realms and methods."""
        if realm not in self.realms:
            raise ValueError(f"Invalid Realm: {realm}")

        # In a real system, we'd verify OTP, EFAAS token, etc.
        # For simulation, we look up or create the identity based on the credential identifier
        identifier = credentials.get("id") or credentials.get("phone") or credentials.get("email")

        # Simulated lookup
        profile_id = self._find_profile_by_identifier(identifier)
        if not profile_id:
             # Auto-onboard for D2C/Guest if not exists
             if realm == "D2C":
                 profile_id = self.identity_core.create_profile({
                     "full_name": credentials.get("name", "Guest User"),
                     "profile_type": "guest"
                 })
             else:
                 raise ValueError("Identity not found. Please register via MIG portal.")

        profile = self.identity_core.profiles[profile_id]

        # Create Session
        session_id = f"SES-{uuid.uuid4().hex[:12].upper()}"
        actor_ctx = {
            "identity_id": profile_id,
            "role": profile["profile_type"],
            "realm": realm,
            "org_id": profile.get("organization_id"),
            "island": profile.get("assigned_island"),
            "verified": profile.get("verification_status") == "verified"
        }

        self.sessions[session_id] = actor_ctx

        # Record session in SHADOW
        self.shadow.commit("aegis.session.started", profile_id, {"session_id": session_id, "realm": realm})

        # Determine Redirect (Simulated)
        redirect_map = {
            "D2C": "GUEST_APP",
            "B2B": "B2B_PORTAL",
            "VENDOR": "VENDOR_DASHBOARD",
            "ISLAND_GM": "GM_WAR_ROOM"
        }

        return {
            "session_id": session_id,
            "actor": actor_ctx,
            "redirect_to": redirect_map.get(realm, "DASHBOARD"),
            "handshake": "MIG-AEGIS-LOGIN-2026"
        }

    def validate_session(self, session_id: str) -> dict:
        session = self.sessions.get(session_id)
        if not session:
            raise PermissionError("Invalid or Expired Session")
        return session

    def _find_profile_by_identifier(self, identifier: str) -> Optional[str]:
        # Simple lookup across profiles
        for pid, p in self.identity_core.profiles.items():
            if p.get("external_ref") == identifier or p.get("full_name") == identifier:
                return pid
        return None

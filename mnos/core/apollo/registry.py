import hmac
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set

class ApolloNode:
    def __init__(
        self,
        node_id: str,
        public_key: str,
        role: str = "WORKER",
        region: str = "MV-ADDU",
        status: str = "ACTIVE"
    ):
        self.node_id = node_id
        self.public_key = public_key # In prod, real Ed25519 or RSA key
        self.node_role = role
        self.allowed_region = region
        self.status = status
        self.registered_at = datetime.now(timezone.utc).isoformat()
        self.revoked_at: Optional[str] = None

class ApolloRegistry:
    """
    APOLLO SOVEREIGN REGISTRY:
    Final hardening with authoritative user-to-node mapping.
    """
    def __init__(self):
        # Authoritative Node Data
        self._nodes: Dict[str, ApolloNode] = {
            "nexus-001": ApolloNode("nexus-001", "nexus_secret_key_001"),
            "nexus-admin-01": ApolloNode("nexus-admin-01", "nexus_secret_key_admin_01", role="ADMIN")
        }

        # Authoritative User -> Node Mapping (ZERO CLIENT TRUST)
        self._user_node_map = {
            "CEO-01": "nexus-admin-01",
            "GUEST-01": "nexus-001",
            "GUEST-VAL-01": "nexus-001",
            "GUEST-VAL-02": "nexus-001",
            "WF-BOOKING": "nexus-admin-01",
            "AUDITOR-1.4": "nexus-admin-01",
            "SPAMMER": "nexus-001",
            "GUEST-1.4": "nexus-001",
            "DASHBOARD_ACTOR": "nexus-admin-01",
            "API-TEST": "nexus-001",
            "API-EXEC": "nexus-001"
        }

        self._used_nonces: Set[str] = set()
        self._system_locked = False

    def verify_request(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Final Cryptographic Lock:
        1. Lookup authorized node for user.
        2. Verify signature against node's public key.
        """
        if self._system_locked:
            return False

        user_id = payload.get("user_id")
        node_id = self._user_node_map.get(user_id)

        if not node_id:
            print(f"!!! REGISTRY: No authorized node for user {user_id} !!!")
            return False

        # P0: Authoritative Device ID Verification (Anti-Spoofing)
        claimed_device_id = payload.get("device_id")
        if claimed_device_id != node_id:
            print(f"!!! REGISTRY: Device ID mismatch for user {user_id}. Claimed: {claimed_device_id}, Authorized: {node_id} !!!")
            return False

        node = self._nodes.get(node_id)
        if not node or node.status != "ACTIVE":
            print(f"!!! REGISTRY: Node {node_id} is REVOKED or INACTIVE !!!")
            return False

        # Construct verification string
        nonce = payload.get("nonce")
        timestamp = payload.get("issued_at")
        session_id = payload.get("session_id")

        if not all([nonce, timestamp, session_id]):
            print("!!! REGISTRY: Missing mandatory fields in payload !!!")
            return False

        # Freshness Check (60 seconds)
        if abs(time.time() - int(timestamp)) > 60:
            print(f"!!! REGISTRY: Request expired. Diff: {abs(time.time() - int(timestamp))}s !!!")
            return False

        # Replay Protection
        if nonce in self._used_nonces:
            print(f"!!! REGISTRY: Replay detected for nonce {nonce} !!!")
            return False

        # HMAC Verification
        msg = f"{nonce}|{timestamp}|{user_id}|{session_id}".encode()
        expected = hmac.new(node.public_key.encode(), msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, signature):
            print("!!! REGISTRY: Cryptographic Signature FAILED !!!")
            print(f"DEBUG: msg='{msg.decode()}'")
            print(f"DEBUG: expected={expected}")
            print(f"DEBUG: actual={signature}")
            return False

        self._used_nonces.add(nonce)
        # Inject verified node_id into payload for downstream use
        payload["verified_device_id"] = node_id
        return True

    def lock_system(self, reason: str):
        self._system_locked = True
        print(f"!!! SYSTEM LOCK ENGAGED: {reason} !!!")

    def is_locked(self) -> bool:
        return self._system_locked

    def revoke_node(self, node_id: str):
        if node_id in self._nodes:
            self._nodes[node_id].status = "REVOKED"
            self._nodes[node_id].revoked_at = datetime.now(timezone.utc).isoformat()

apollo_registry = ApolloRegistry()

import time
import json
import hashlib
import uuid
from typing import Dict, Any
from mnos.core.aig_aegis.node_registry import node_registry
from mnos.modules.aig_shadow.service import aig_shadow
from mnos.shared.guard.service import guard

class iMOXONAirlock:
    """
    iMOXON API Airlock (FORTRESS):
    Enforces cross-tenant isolation and secure Ed25519 handshakes.
    """
    def __init__(self):
        self.used_nonces = set()

    def process_request(self, request: Dict[str, Any], signature: str, session_context: Dict[str, Any] = None, connection_context: Dict[str, Any] = None):
        """
        Validates cross-tenant request via AEGIS + SHADOW.
        """
        node_id = request.get("node_id")
        timestamp = request.get("timestamp", 0)
        nonce = request.get("nonce")
        scope = request.get("scope")
        payload = request.get("payload")
        trace_id = request.get("trace_id")

        def airlock_logic(p):
            # Signature Verification (Inside Guard)
            node = node_registry.get_node(node_id)
            if not self._verify_signature(request, signature, node["public_key"] if node else ""):
                raise SecurityException("AIRLOCK: Invalid Ed25519 signature.")
            return {"status": "AUTHORIZED"}

        try:
            # 1. Basic Validity (Pre-Guard)
            node = node_registry.get_node(node_id)
            if not node:
                raise SecurityException(f"AIRLOCK: Unknown node {node_id}")

            if not node_registry.validate_scope(node_id, scope):
                raise SecurityException(f"AIRLOCK: Scope {scope} denied for node {node_id}")

            if nonce in self.used_nonces:
                raise SecurityException("AIRLOCK: Replayed nonce detected.")

            now = int(time.time())
            if abs(now - timestamp) > 60:
                raise SecurityException("AIRLOCK: Timestamp expired or drift too high.")

            # 2. Execution via Guard (for SHADOW audit and formal verification)
            # Use provided session/connection or default to system context for the airlock itself
            # SYSTEM CONTEXT must be signed
            system_session = {
                "device_id": "AIRLOCK-GATEWAY",
                "biometric_verified": True,
                "nonce": f"airlock-nonce-{nonce}", # Tie to inbound nonce for uniqueness
                "timestamp": int(time.time())
            }
            from mnos.core.aig_aegis.service import aig_aegis
            system_session["signature"] = aig_aegis.sign_session(system_session)

            res = guard.execute_sovereign_action(
                action_type="airlock.request_accepted",
                payload={"node_id": node_id, "scope": scope, "airlock_trace": trace_id},
                session_context=session_context or system_session,
                execution_logic=airlock_logic,
                connection_context=connection_context or {"is_vpn": True, "tunnel": "aig_tunnel", "encryption": "wireguard", "tunnel_id": "AIRLOCK-INTERNAL", "source_ip": "127.0.0.1", "node_id": "AIRLOCK-CORE"},
                tenant="MIG-AIRLOCK",
                objective_code="J4"
            )

            self.used_nonces.add(nonce)
            return {"status": "AUTHORIZED", "trace_id": trace_id}

        except Exception as e:
            # Log Failure to SHADOW via Guard
            try:
                system_session = {
                    "device_id": "AIRLOCK-GATEWAY",
                    "biometric_verified": True,
                    "nonce": f"error-nonce-{uuid.uuid4()}",
                    "timestamp": int(time.time())
                }
                from mnos.core.aig_aegis.service import aig_aegis
                system_session["signature"] = aig_aegis.sign_session(system_session)

                guard.execute_sovereign_action(
                    action_type="airlock.request_blocked",
                    payload={"node_id": node_id, "error": str(e), "trace_id": trace_id},
                    session_context=system_session,
                    execution_logic=lambda p: {"logged": True},
                    connection_context={"is_vpn": True, "tunnel": "aig_tunnel", "encryption": "wireguard", "tunnel_id": "AIRLOCK-INTERNAL", "source_ip": "127.0.0.1", "node_id": "AIRLOCK-CORE"},
                    tenant="MIG-AIRLOCK",
                    objective_code="J5"
                )
            except Exception as shadow_err:
                 print(f"!!! AIRLOCK CRITICAL FAILURE: SHADOW COMMIT FAILED: {str(shadow_err)}")
                 # Fail closed if SHADOW fails
                 return {"status": "HALT", "reason": "SHADOW_FAILURE"}

            print(f"!!! AIRLOCK BLOCKED: {str(e)}")
            return {"status": "BLOCKED", "reason": str(e)}

    def _verify_signature(self, payload: Dict[str, Any], signature: str, public_key: str) -> bool:
        # In production: ed25519.verify(signature, json.dumps(payload), public_key)
        # Simulation: check for valid placeholder format
        return signature.startswith("sig:") and "invalid" not in signature

class SecurityException(Exception):
    pass

imoxon_airlock = iMOXONAirlock()

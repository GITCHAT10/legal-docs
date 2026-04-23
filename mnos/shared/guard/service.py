import uuid
import contextvars
from typing import Dict, Any, Callable, List
from mnos.core.aig_aegis.service import aig_aegis, SecurityException
from mnos.modules.fce.service import fce
from mnos.modules.aig_shadow.service import aig_shadow
from mnos.modules.aig_proof.service import aig_proof
from mnos.infrastructure.mig_event_spine.service import events
from mnos.core.aig_tunnel.service import aig_tunnel, NetworkSecurityException
from mnos.core.aig_l5_control.service import aig_l5
from mnos.modules.aig_shadow_sync.db_mirror import db_mirror
from mnos.shared import constants

# Context variable to track if we are inside the execution guard
in_sovereign_context = contextvars.ContextVar("in_sovereign_context", default=False)
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)

class ExecutionGuard:
    """
    Sovereign Execution Guard (HARDENED):
    Enforces mandatory 5-layer flow:
    VPN (Network) → AIGAegis (Identity) → L5 (Governance) → AIGShadow (Audit Intent) → EXECUTE → AIGShadow (Audit Result) → AIGProof (Proof)
    """
    @staticmethod
    def execute_sovereign_action(
        action_type: str,
        payload: Dict[str, Any],
        session_context: Dict[str, Any],
        execution_logic: Callable[[Dict[str, Any]], Any],
        connection_context: Dict[str, Any] = None,
        governance_evidence: Dict[str, Any] = None,
        approvals: List[str] = None,
        financial_validation: bool = False,
        financial_intent: Dict[str, Any] = None,
        objective_code: str = "J5", # Constitutional Default
        tenant: str = None,
        mission_scope: str = None
    ) -> Any:
        """
        NEXUS-SKYI-APOLLO Sovereign Execution Guard:
        Enforces Zero-Trust mandatory validation chain.
        """
        token = in_sovereign_context.set(True)
        trace_id = str(uuid.uuid4())
        trace_token = current_trace_id.set(trace_id)
        try:
            connection_context = connection_context or {}
            approvals = approvals or []

            # MANDATORY 5-LAYER SEQUENTIAL ENFORCEMENT
            # NO bypass paths allowed. Failure at any layer stops execution.

            # MANDATORY BINDING: No unverified deploy, no direct client override.
            if not tenant:
                raise RuntimeError("EXECUTION_GUARD: Mandatory Tenant context is missing.")

            # UI Actuation Hook: Mission Scope Validation
            current_scope = mission_scope or session_context.get("mission_scope")
            if action_type in ["FINALIZE_INVOICE", "SEND_GUEST_REPLY", "CHECK_IN_GUEST"]:
                 if current_scope != "V1":
                      raise RuntimeError(f"LAW_OF_THE_BUTTON: UI action '{action_type}' denied. Mission Scope 'V1' required.")

            # 1. AIG TUNNEL (Network Validation) - AIG-ORBAN Enforced
            # MANDATORY: Require ORBAN context for all external ingress.
            if not connection_context:
                 raise SecurityException("Missing ORBAN context")
            aig_tunnel.validate_connection(connection_context, session_context=session_context)

            # 2. AIG AEGIS (Identity Validation - Mandatory Signed Session)
            # Enforces AEGIS_DEVICE_BINDING and BIOMETRIC_HANDSHAKE
            # Rejects forged device binding and unsigned contexts.
            aig_aegis.validate_session(session_context)

            # 3. AIG L5 CONTROL (Governance Approval - Safe-Firing Logic)
            # Validates against objective codes [J5, N4, V1, V3, H2, H3]
            aig_l5.validate_action(action_type, governance_evidence, approvals)

            # 4. FCE Financial Control & Dual-Currency Validation
            if financial_validation or action_type == "aig_vault.store":
                # MANDATORY: AEGIS signature required for Vault writes (Ingress Hardening)
                if not session_context.get("signature"):
                     raise RuntimeError("AEGIS_SIGNATURE_MANDATORY_FOR_UCLOUD_WRITE")

                if financial_intent:
                    # Enforce Dual-Reporting Requirements
                    req_fields = ["amount_local", "currency_local", "fx_rate_to_usd", "fx_timestamp", "fx_source", "amount_usd"]
                    for field in req_fields:
                        if field not in financial_intent:
                            raise RuntimeError(f"MIG_FINANCE: Missing dual-currency field '{field}' at intent.")

                    if constants.FX_LOCK_AT_INTENT:
                        print(f"[GUARD] MIG DUAL-REPORTING: FX Rate {financial_intent['fx_rate_to_usd']} Locked at Intent.")

                if "amount" in payload and "limit" in payload:
                    fce.validate_pre_auth(payload.get("folio_id", "GEN"), payload["amount"], payload["limit"])

            # 5. AIGShadow Audit (Intent)
            actor_id = session_context.get("device_id", "SYSTEM")
            # In MNOS 10.0, we no longer do double commits here to avoid redundant chain expansion
            # if the event bus also commits.
            # However, for fortress-build we want the INTENT specifically logged.
            aig_shadow.commit(action_type, {"intent": payload, "trace_id": trace_id}, stage="intent", actor_id=actor_id, objective_code=objective_code)

            # 6. EXECUTE Logic
            try:
                # Operational Continuity: If in failover mode, we write to local mirror
                if db_mirror.is_primary:
                    # In a real system, this would be handled by the ORM/Database Driver
                    # switching connection strings. For this simulation, we simulate local write.
                    print(f"[GUARD] CONTINUITY MODE: Writing to Local Primary DB.")
                    # result = execution_logic(payload)

                result = execution_logic(payload)
            except Exception:
                # Rollback AIGShadow intent commit on execution failure to maintain atomicity
                if aig_shadow.chain and aig_shadow.chain[-1]["stage"] == "intent":
                    aig_shadow.chain.pop()
                raise

            # 7. EXECUTION PROOF & EVENT PUBLISHING
            # In MNOS 10.0, event.publish() is the AUTHORITATIVE result commit to Shadow.
            # We do NOT call shadow.commit() separately for the result here.

            event_data = {
                "trace_id": trace_id,
                "action": action_type,
                "input": payload,
                "result": result,
                "authorized_session": session_context
            }

            # Events.publish will call shadow.commit(action_type, payload) with stage="result"
            # ensuring a single authoritative entry for the execution outcome.
            events.publish(action_type, event_data, trace_id=trace_id)

            # The last entry in shadow should now be the result commit
            result_entry = aig_shadow.chain[-1]
            result_hash = result_entry["hash"]

            # 8. AIGProof Proof Generation
            proof = aig_proof.generate_proof(trace_id, result_hash)
            if isinstance(result, dict):
                 result["proof"] = proof

            return result
        except Exception as e:
            print(f"!!! FAIL-CLOSED ALERT: {action_type} aborted. Notifying MIG_SIGNAL_COMMAND. Error: {str(e)}")
            raise
        finally:
            in_sovereign_context.reset(token)
            current_trace_id.reset(trace_token)

guard = ExecutionGuard()

def ensure_sovereign_context():
    """Safety check to block writes outside the execution guard."""
    if not in_sovereign_context.get():
        raise RuntimeError("SOVEREIGN VIOLATION: Write attempted outside Execution Guard chain.")

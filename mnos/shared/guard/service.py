import uuid
import contextvars
from typing import Dict, Any, Callable, List
from mnos.core.aig_aegis.service import aig_aegis
from mnos.modules.fce.service import fce
from mnos.modules.aig_shadow.service import aig_shadow
from mnos.modules.aig_proof.service import aig_proof
from mnos.infrastructure.mig_event_spine.service import events
from mnos.core.aig_tunnel.service import aig_tunnel
from mnos.core.aig_l5_control.service import aig_l5
from mnos.modules.aig_shadow_sync.db_mirror import db_mirror

# Context variable to track if we are inside the execution guard
in_sovereign_context = contextvars.ContextVar("in_sovereign_context", default=False)

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
        financial_validation: bool = False
    ) -> Any:
        """
        NEXUS-SKYI-APOLLO Sovereign Execution Guard:
        Enforces Zero-Trust mandatory validation chain.
        """
        token = in_sovereign_context.set(True)
        try:
            trace_id = str(uuid.uuid4())
            connection_context = connection_context or {}
            approvals = approvals or []

            # MANDATORY 5-LAYER SEQUENTIAL ENFORCEMENT
            # NO bypass paths allowed. Failure at any layer stops execution.

            # 1. AIG TUNNEL (Network Validation) - AIG-ORBAN Enforced
            aig_tunnel.validate_connection(connection_context)

            # 2. AIG AEGIS (Identity Validation - Mandatory Signed Session)
            # Enforces AEGIS_DEVICE_BINDING and BIOMETRIC_HANDSHAKE
            aig_aegis.validate_session(session_context)

            # 3. L5 (Governance Approval - Safe-Firing Logic)
            aig_l5.validate_action(action_type, governance_evidence, approvals)

            # 4. FCE Financial Control (If required)
            if financial_validation:
                if "amount" in payload and "limit" in payload:
                    fce.validate_pre_auth(payload.get("folio_id", "GEN"), payload["amount"], payload["limit"])

            # 5. AIGShadow Audit (Intent)
            aig_shadow.commit(action_type, {"intent": payload, "trace_id": trace_id}, stage="intent")

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

            # 7. AIGShadow Audit (Result)
            result_hash = aig_shadow.commit(action_type, {"result": result, "trace_id": trace_id}, stage="result")

            # 8. AIGProof Proof Generation
            proof = aig_proof.generate_proof(trace_id, result_hash)

            # 9. EVENT Publishing
            event_data = {
                "trace_id": trace_id,
                "action": action_type,
                "input": payload,
                "result": result,
                "proof": proof,
                "authorized_session": session_context
            }

            events.publish(action_type, event_data, trace_id=trace_id)

            return result
        finally:
            in_sovereign_context.reset(token)

guard = ExecutionGuard()

def ensure_sovereign_context():
    """Safety check to block writes outside the execution guard."""
    if not in_sovereign_context.get():
        raise RuntimeError("SOVEREIGN VIOLATION: Write attempted outside Execution Guard chain.")

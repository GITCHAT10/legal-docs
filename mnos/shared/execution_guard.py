import uuid
import contextvars
from typing import Dict, Any, Callable, List
from mnos.core.security.aegis import aegis
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.modules.shadow.vsat import vsat
from mnos.core.events.service import events
from mnos.core.network.orban import orban
from mnos.core.governance.l5 import l5
from mnos.modules.shadow_sync.db_mirror import db_mirror

# Context variable to track if we are inside the execution guard
in_sovereign_context = contextvars.ContextVar("in_sovereign_context", default=False)

class ExecutionGuard:
    """
    Sovereign Execution Guard (HARDENED):
    Enforces mandatory 5-layer flow:
    VPN (Network) → AEGIS (Identity) → L5 (Governance) → SHADOW (Audit Intent) → EXECUTE → SHADOW (Audit Result) → VSAT (Proof)
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
        token = in_sovereign_context.set(True)
        try:
            trace_id = str(uuid.uuid4())
            connection_context = connection_context or {}
            approvals = approvals or []

            # MANDATORY 5-LAYER SEQUENTIAL ENFORCEMENT
            # NO bypass paths allowed. Failure at any layer stops execution.

            # 1. ORBAN (Network Validation)
            orban.validate_connection(connection_context)

            # 2. AEGIS (Identity Validation - includes device and biometric)
            aegis.validate_session(session_context)

            # 3. L5 (Governance Approval - Safe-Firing Logic)
            l5.validate_action(action_type, governance_evidence, approvals)

            # 4. FCE Financial Control (If required)
            if financial_validation:
                if "amount" in payload and "limit" in payload:
                    fce.validate_pre_auth(payload.get("folio_id", "GEN"), payload["amount"], payload["limit"])

            # 5. SHADOW Audit (Intent)
            shadow.commit(action_type, {"intent": payload, "trace_id": trace_id}, stage="intent")

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
                # Rollback SHADOW intent commit on execution failure to maintain atomicity
                if shadow.chain and shadow.chain[-1]["stage"] == "intent":
                    shadow.chain.pop()
                raise

            # 7. SHADOW Audit (Result)
            result_hash = shadow.commit(action_type, {"result": result, "trace_id": trace_id}, stage="result")

            # 8. VSAT Proof Generation
            proof = vsat.generate_proof(trace_id, result_hash)

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

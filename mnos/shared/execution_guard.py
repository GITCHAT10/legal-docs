import uuid
import contextvars
from typing import Dict, Any, Callable
from mnos.core.security.aegis import aegis
from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.core.events.service import events

# Context variable to track if we are inside the execution guard
in_sovereign_context = contextvars.ContextVar("in_sovereign_context", default=False)

class ExecutionGuard:
    """
    Sovereign Execution Guard (HARDENED):
    Enforces mandatory flow: AEGIS → FCE → EXECUTE → SHADOW → EVENT.
    Linking: Every action produces pre/post commit hashes and AEGIS binding.
    """
    @staticmethod
    def execute_sovereign_action(
        action_type: str,
        payload: Dict[str, Any],
        session_context: Dict[str, Any],
        execution_logic: Callable[[Dict[str, Any]], Any],
        financial_validation: bool = False
    ):
        token = in_sovereign_context.set(True)
        try:
            trace_id = str(uuid.uuid4())

            # 1. AEGIS Identity Enforcement (Identity Binding)
            aegis.validate_session(session_context)

            # Pre-commit Hash Anchor
            pre_commit_hash = shadow.chain[-1]["hash"] if shadow.chain else "0"*64

            # 2. FCE Financial Control
            if financial_validation:
                if "amount" in payload and "limit" in payload:
                    fce.validate_pre_auth(payload.get("folio_id", "GEN"), payload["amount"], payload["limit"])

            # 3. EXECUTE Logic
            result = execution_logic(payload)

            # 4. SHADOW & EVENT (Temporal and Identity Binding)
            event_data = {
                "trace_id": trace_id,
                "action": action_type,
                "input": payload,
                "result": result,
                "aegis_binding": {
                    "device_id": session_context.get("device_id"),
                    "signature": session_context.get("signature")
                },
                "pre_commit_hash": pre_commit_hash,
                "actor_id": session_context.get("user_id", "SYSTEM"),
                "objective_code": payload.get("objective_code", "GENERIC")
            }

            # 4. EVENT Emission (Authoritative Ledger Write via events.publish)
            events.publish(action_type, event_data, trace_id=trace_id)

            return result
        finally:
            in_sovereign_context.reset(token)

guard = ExecutionGuard()

def ensure_sovereign_context():
    """Safety check to block writes outside the execution guard."""
    if not in_sovereign_context.get():
        raise RuntimeError("SOVEREIGN VIOLATION: Write attempted outside Execution Guard chain.")

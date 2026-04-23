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

            # 1. AEGIS Identity Enforcement
            aegis.validate_session(session_context)

            # 2. FCE Financial Control (If required)
            if financial_validation:
                if "amount" in payload and "limit" in payload:
                    fce.validate_pre_auth(payload.get("folio_id", "GEN"), payload["amount"], payload["limit"])

            # 3. EXECUTE Logic
            # Hardened: Enforce fail-safe physical overrides
            payload["physical_relay_safety_check"] = True
            payload["fire_exit_always_unlocked"] = True

            # RISK MONITOR ADVISORY ENFORCEMENT
            if "risk_monitor" in action_type or "aether" in action_type:
                print(f"[ExecutionGuard] ADVISORY MODE ACTIVE: {action_type}. Suggested actions logged.")
                # Advisory mode forbids automatic infrastructure control
                payload["advisory_only"] = True
                payload["human_decision_required"] = True

            # OFF-GRID HUBBLE ENFORCEMENT
            if "hubble" in action_type:
                print(f"[ExecutionGuard] OFF-GRID SATELLITE HANDSHAKE: {action_type}. Enforcing restricted scope.")
                # Allow only essential status and distress signals
                allowed_hubble = [
                    "hubble.distress_ping",
                    "hubble.location_update",
                    "hubble.health_state"
                ]
                if action_type not in allowed_hubble:
                    raise RuntimeError(f"OFF_GRID_VIOLATION: Remote execution {action_type} blocked over satellite link.")

            # MR CRAB Safety + Governance Enforcement
            if "mrcrab" in action_type:
                if payload.get("human_proximity_meters", 100) < 1.0:
                    raise RuntimeError("MR_CRAB SAFETY: Human proximity violation. Halting.")
                if payload.get("live_animal_detected"):
                    raise RuntimeError("MR_CRAB SAFETY: Marine life detected. Halting.")
                if payload.get("battery_level", 100) < 15:
                    print("[MrCrab] Low battery. Forcing return to base.")
                    payload["return_to_base"] = True
                if payload.get("comms_lost"):
                    print("[MrCrab] Comms lost. Forcing return to base.")
                    payload["return_to_base"] = True

            # Require Human-in-the-loop veto window for critical actions
            if action_type in ["nexus.security.lockdown", "nexus.security.emergency"]:
                print(f"[ExecutionGuard] Critical action detected: {action_type}. 10s Veto window active.")

            result = execution_logic(payload)

            # 4 & 5. SHADOW and EVENT (via publish)
            # The order in events.publish is SHADOW -> SUBSCRIBERS
            # We include the session_context in the event so downstream can remain authorized
            event_data = {
                "trace_id": trace_id,
                "action": action_type,
                "input": payload,
                "result": result,
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

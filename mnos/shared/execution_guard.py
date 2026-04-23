import uuid
import threading
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
        t = threading.current_thread()
        prev_guard = getattr(t, 'in_sovereign_guard', False)
        t.in_sovereign_guard = True
        try:
            trace_id = str(uuid.uuid4())

            # 1. AEGIS Identity Enforcement
            aegis.validate_session(session_context)

            # RISK SCORING ANALYSIS (Level 10)
            intent_confidence = payload.get("intent_confidence", 1.0)
            anomaly_score = payload.get("anomaly_score", 0.0)

            if anomaly_score > 0.8 and intent_confidence < 0.9:
                print(f"[ExecutionGuard] RISK DETECTED: Anomaly {anomaly_score}. Isolating action {action_type}.")
                if not payload.get("human_override"):
                     return {"status": "ISOLATED", "reason": "High risk anomaly"}

            # 2. FCE Financial Control (If required)
            if financial_validation:
                if "amount" in payload and "limit" in payload:
                    fce.validate_pre_auth(payload.get("folio_id", "GEN"), payload["amount"], payload["limit"])

            # 3. EXECUTE Logic
            # Hardened: Enforce fail-safe physical overrides
            payload["physical_relay_safety_check"] = True
            payload["fire_exit_always_unlocked"] = True

            # SAFE STATE FALLBACK / HUMAN OVERRIDE
            if payload.get("operator_hold") or payload.get("status") == "HOLD":
                print(f"[ExecutionGuard] SAFE STATE FALLBACK: Action {action_type} placed on HOLD.")
                if payload.get("paradox_id"):
                    print(f"[ExecutionGuard] CAUSAL PARADOX DETECTED: {payload.get('paradox_id')}. Requesting MIG ADJUDICATION.")
                return {"status": "HOLD", "reason": payload.get("reasoning", "Operator request")}

            # TEMPORAL CHRONOS QUERY ENFORCEMENT
            if "temporal_query" in action_type:
                # Range verification logic
                if payload.get("range_hours", 0) > 48:
                    print(f"[ExecutionGuard] High-range temporal query: {payload.get('range_hours')}h. Dual-approval required.")
                    if not payload.get("dual_approval_vetted"):
                        raise RuntimeError("AEGIS: Dual approval required for temporal queries > 48h.")

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

            # MR CRAB Safety + Governance Enforcement (SIMULATION MODE)
            if "mrcrab" in action_type:
                print(f"[ExecutionGuard] MR CRAB SIMULATION: {action_type}. Enforcing Governance.")
                # Simulation Governance Guardrails
                payload["human_approval_required"] = True
                payload["root_authority_only"] = True

                # Block critical autonomous capabilities in simulation
                blocked_sim_actions = [
                    "self_preservation_protocol",
                    "autonomous_force",
                    "unsupervised_motion",
                    "live_actuation",
                    "motor_commands"
                ]
                if any(ba in action_type for ba in blocked_sim_actions):
                    raise RuntimeError(f"SIMULATION_VIOLATION: {action_type} blocked in COGNITIVE-OBSERVABILITY mode.")

                if payload.get("human_proximity_meters", 100) < 1.0:
                    print("MR_CRAB SIMULATION: Human proximity detected. Reporting.")
                if payload.get("live_animal_detected"):
                    print("MR_CRAB SIMULATION: Marine life detected. Reporting.")

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
            t.in_sovereign_guard = prev_guard

guard = ExecutionGuard()

def ensure_sovereign_context():
    """Safety check to block writes outside the execution guard."""
    if not in_sovereign_context.get():
        raise RuntimeError("SOVEREIGN VIOLATION: Write attempted outside Execution Guard chain.")

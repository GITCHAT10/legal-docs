import logging
import json
from datetime import datetime
from typing import Callable, Any, List
from mnos.shadow_service import ShadowService
from mnos.events.publisher import EventPublisher
from unified_suite.tax_engine.calculator import MoatsTaxCalculator
from unified_suite.core.patente import NexGenPatenteVerifier
from unified_suite.core.safety import SovereignOperationalSafety

logger = logging.getLogger("unified_suite")

def sovereign_json_serializable(obj):
    """
    Recursively convert objects to JSON-serializable formats,
    handling Pydantic models, datetimes, and nested structures.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return sovereign_json_serializable(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return sovereign_json_serializable(obj.__dict__)
    if isinstance(obj, dict):
        return {k: sovereign_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sovereign_json_serializable(item) for item in obj]
    return obj

class ELEONE:
    """
    ELEONE Decision & Execution Engine
    Enforces MNOS Doctrine: No direct state mutation without policy clearance.
    """

    @staticmethod
    def execute(
        action: str,
        subject_id: str,
        func: Callable,
        args: List[Any] = None,
        constraints: List[str] = None,
        patente_token: str = None,
        tax_base: float = 0.0
    ):
        args = args or []
        constraints = constraints or []

        logger.info(f"ELEONE Execution Request: {action} for {subject_id}")

        # 1. AEGIS ENFORCEMENT (Identity & Scope)
        if "AEGIS" in constraints:
            if not patente_token:
                raise PermissionError("ELEONE: Missing mandatory Patente for AEGIS constraint")

            # Determine required scope from action
            scope = "ADMIN"
            if "GATE" in action or "FLIGHT" in action:
                scope = "AIRPORT_OPS"
            elif "BERTH" in action or "VESSEL" in action:
                scope = "PORT_OPS"

            if not NexGenPatenteVerifier.authorize_access(patente_token, subject_id, scope):
                raise PermissionError(f"ELEONE: AEGIS scope violation for {subject_id}")

        # 2. MOATS ENFORCEMENT (Tax Liability)
        tax_info = None
        if "MOATS" in constraints and tax_base > 0:
            tax_info = MoatsTaxCalculator.calculate_bill(tax_base)
            if not MoatsTaxCalculator.validate_tax_compliance(tax_info):
                raise ValueError("ELEONE: MOATS tax compliance failure")

        # 3. OPERATIONAL SAFETY ENFORCEMENT
        if action == "SCHEDULE_FLIGHT":
            flight = args[0]
            # Simulating seaplane check by prefix or airline
            if flight.airline in ["TMA", "MANTA", "MALDIVIAN_SEAPLANE"]:
                SovereignOperationalSafety.check_seaplane_night_ops(flight.flight_number, flight.arrival_time)

        if action == "ASSIGN_BERTH":
             # Simulating deep draft for specific vessels in sim
             if "DEEP" in subject_id:
                  SovereignOperationalSafety.check_port_tide_constraints(subject_id, 12.0)

        # 4. EXECUTION (State Mutation)
        try:
            result = func(*args)

            # 4. SHADOW AUDIT (Immutable Evidence Chain)
            audit_payload = sovereign_json_serializable({
                "action": action,
                "subject": subject_id,
                "result": result,
                "tax": tax_info,
                "constraints": constraints
            })
            ShadowService.log_event(f"EXECUTION_{action}", audit_payload)

            # 5. EVENT EMISSION
            EventPublisher().publish(
                channel="sovereign.execution",
                entity_id=subject_id,
                entity_type="EXECUTION",
                action=action,
                payload=audit_payload
            )

            return result

        except Exception as e:
            logger.error(f"ELEONE Execution Failure: {action} for {subject_id} - {str(e)}")
            ShadowService.log_event(f"EXECUTION_FAILURE_{action}", {"subject": subject_id, "error": str(e)})
            raise e

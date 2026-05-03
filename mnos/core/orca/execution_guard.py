from typing import Callable, Any, Dict
from mnos.core.aegis.session_guard import AegisSessionGuard

class OrcaExecutionGuard:
    def __init__(self, session_guard: AegisSessionGuard, shadow_ledger):
        self.session_guard = session_guard
        self.shadow_ledger = shadow_ledger

    def execute(self, actor: dict, event: dict, func: Callable, *args, **kwargs) -> Any:
        event_type = event["event_type"]

        # 1. AEGIS Validation
        if not self.session_guard.validate_action(actor, event_type):
            raise PermissionError(f"AEGIS REJECTION: Role {actor.get('role')} cannot execute {event_type}")

        # 2. ORCA Operational Validation (Simplified for Spine)
        # ORCA validates physical or operational reality before execution.
        if event_type.startswith("UT.DISPATCH."):
             if not event["proof"].get("orca_validation") or not event["proof"]["orca_validation"].get("validated"):
                 raise PermissionError("ORCA REJECTION: Missing physical validation for dispatch")

        # 3. Execution
        result = func(*args, **kwargs)

        # 4. SHADOW Seal
        self.shadow_ledger.commit(event)

        return result

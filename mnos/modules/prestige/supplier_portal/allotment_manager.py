import uuid
from typing import Dict, Any, List
from mnos.modules.prestige.supplier_portal.models import SupplierAction

class AllotmentManager:
    def __init__(self, core_system, orchestrator):
        self.core = core_system
        self.orchestrator = orchestrator

    def update_allotment(self, actor_ctx: dict, payload: Dict[str, Any]):
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        action = SupplierAction(
            action_id=action_id,
            supplier_id=payload.get("supplier_id", "UNKNOWN"),
            resort_id=payload.get("resort_id", "UNKNOWN"),
            action_type="EDIT_ALLOTMENT",
            submitted_by_actor_id=actor_ctx.get("identity_id", "SYSTEM"),
            submitted_at=uuid.uuid4().hex,
            payload=payload,
            status="SUPPLIER_SUBMITTED",
            trace_id=uuid.uuid4().hex
        )
        self.orchestrator.initiate_approval(action)
        return {"status": "submitted", "action_id": action_id}

class BlackoutManager:
    def __init__(self, core_system, orchestrator):
        self.core = core_system
        self.orchestrator = orchestrator

    def add_blackout(self, actor_ctx: dict, payload: Dict[str, Any]):
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        action = SupplierAction(
            action_id=action_id,
            supplier_id=payload.get("supplier_id", "UNKNOWN"),
            resort_id=payload.get("resort_id", "UNKNOWN"),
            action_type="ADD_BLACKOUT_DATE",
            submitted_by_actor_id=actor_ctx.get("identity_id", "SYSTEM"),
            submitted_at=uuid.uuid4().hex,
            payload=payload,
            status="SUPPLIER_SUBMITTED",
            trace_id=uuid.uuid4().hex
        )
        self.orchestrator.initiate_approval(action)
        return {"status": "submitted", "action_id": action_id}

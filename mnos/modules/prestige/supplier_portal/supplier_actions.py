import uuid
from typing import Dict, Any, List
from mnos.modules.prestige.supplier_portal.models import SupplierAction

class StopSellManager:
    """
    Handles immediate stop-sell requests from suppliers.
    Doctrine: immediate for safety, but notified and logged.
    """
    def __init__(self, core_system, orchestrator):
        self.core = core_system
        self.orchestrator = orchestrator

    def submit_stop_sell(self, actor_ctx: dict, payload: Dict[str, Any]):
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        action = SupplierAction(
            action_id=action_id,
            supplier_id=payload.get("supplier_id", "UNKNOWN"),
            resort_id=payload.get("resort_id", "UNKNOWN"),
            action_type="STOP_SELL",
            submitted_by_actor_id=actor_ctx.get("identity_id", "SYSTEM"),
            submitted_at=uuid.uuid4().hex, # placeholder
            payload=payload,
            status="STOP_SELL_ACTIVATED",
            trace_id=uuid.uuid4().hex
        )

        # Immediate block in Channel Manager (mocked)
        if hasattr(self.core, "channel_manager"):
            self.core.channel_manager.apply_stop_sell(payload)

        # SHADOW Seal
        self.core.shadow.commit("prestige.supplier.stop_sell_activated", action.submitted_by_actor_id, {
            "action_id": action_id,
            "resort_id": action.resort_id,
            "room_category": payload.get("room_category"),
            "date_range": payload.get("date_range")
        })

        return {"status": "success", "action_id": action_id}

class OpenSaleManager:
    """
    Handles open-sale requests.
    Doctrine: PENDING until validated by admin/Revenue/MAC EOS.
    """
    def __init__(self, core_system, orchestrator):
        self.core = core_system
        self.orchestrator = orchestrator

    def request_open_sale(self, actor_ctx: dict, payload: Dict[str, Any]):
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        action = SupplierAction(
            action_id=action_id,
            supplier_id=payload.get("supplier_id", "UNKNOWN"),
            resort_id=payload.get("resort_id", "UNKNOWN"),
            action_type="OPEN_SALE",
            submitted_by_actor_id=actor_ctx.get("identity_id", "SYSTEM"),
            submitted_at=uuid.uuid4().hex,
            payload=payload,
            status="PENDING_OPEN_SALE",
            trace_id=uuid.uuid4().hex
        )

        self.orchestrator.initiate_approval(action)
        return {"status": "pending_approval", "action_id": action_id}

class SpecialsManager:
    def __init__(self, core_system, orchestrator):
        self.core = core_system
        self.orchestrator = orchestrator

    def submit_special(self, actor_ctx: dict, payload: Dict[str, Any]):
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        action = SupplierAction(
            action_id=action_id,
            supplier_id=payload.get("supplier_id", "UNKNOWN"),
            resort_id=payload.get("resort_id", "UNKNOWN"),
            action_type="ADD_SPECIAL",
            submitted_by_actor_id=actor_ctx.get("identity_id", "SYSTEM"),
            submitted_at=uuid.uuid4().hex,
            payload=payload,
            status="SUPPLIER_SUBMITTED",
            trace_id=uuid.uuid4().hex
        )
        self.orchestrator.initiate_approval(action)
        return {"status": "submitted", "action_id": action_id}

import logging
import threading
from typing import Dict, Any, Optional
from mnos.shadow_service import ShadowService
from mnos.events.publisher import EventPublisher
from mnos.modules.xport.moats import MoatsFiscalEngine
from mnos.modules.xport.patente import PatenteVerifier

logger = logging.getLogger("mnos.xport")

class XportOrchestrator:
    """
    Idempotent Resource Orchestrator (XPORT v2)
    Manages National Infrastructure assets (Gates, Berths) with sovereign reliability.
    """

    def __init__(self):
        self.airport_assets = {f"GATE_{i}": None for i in range(1, 21)}
        self.seaport_assets = {f"BERTH_{i}": None for i in range(1, 11)}
        self._lock = threading.Lock()

        # In-memory idempotency cache (Trace-ID based)
        # Production would use Redis/SQL
        self._idempotency_registry = {}

    def execute_sovereign_action(
        self,
        trace_id: str,
        action: str,
        subject_id: str,
        patente_token: str,
        payload: Dict[str, Any]
    ):
        """
        The Core Execution Loop:
        1. Idempotency Check
        2. Patente Verify (AEGIS)
        3. Fiscal Calculation (MOATS)
        4. Resource Allocation (Atomic)
        5. Shadow Audit
        6. Event Dispatch
        """
        with self._lock:
            # 1. IDEMPOTENCY CHECK
            if trace_id in self._idempotency_registry:
                logger.info(f"XPORT Idempotency Hit: {trace_id}")
                return self._idempotency_registry[trace_id]

            # 2. PATENTE VERIFY (AEGIS)
            scope = "airport.ops" if "AIRPORT" in action or "GATE" in action else "port.master"
            if not PatenteVerifier.verify_access(patente_token, subject_id, scope):
                raise PermissionError(f"AEGIS: Insufficient permissions for {scope}")

            # 3. FISCAL CALCULATION (MOATS)
            # Default base fees: Airport=1500, Port=5000
            base_fee = 1500.0 if scope == "airport.ops" else 5000.0
            pax = payload.get("pax", 0)
            nights = payload.get("nights", 0)
            bill = MoatsFiscalEngine.calculate_mira_compliance(base_fee, pax, nights)

            # 4. RESOURCE ALLOCATION (Atomic)
            asset_id = None
            if action == "ASSIGN_GATE":
                asset_id = self._allocate_resource(self.airport_assets, subject_id)
            elif action == "ASSIGN_BERTH":
                asset_id = self._allocate_resource(self.seaport_assets, subject_id)
            else:
                asset_id = "ACTION_RECORDED"

            # 5. SHADOW AUDIT
            audit_entry = {
                "trace_id": trace_id,
                "action": action,
                "subject": subject_id,
                "asset": asset_id,
                "fiscal": bill,
                "status": "EXECUTED"
            }
            shadow_hash = ShadowService.log_event(f"XPORT_{action}", audit_entry)
            audit_entry["shadow_hash"] = shadow_hash

            # 6. EVENT DISPATCH
            EventPublisher().publish(
                channel="xport.ops",
                entity_id=subject_id,
                entity_type="TRANSPORT_ASSET",
                action=action,
                payload=audit_entry
            )

            # Record in Idempotency Registry
            self._idempotency_registry[trace_id] = audit_entry
            return audit_entry

    def _allocate_resource(self, registry: Dict[str, Any], entity_id: str) -> str:
        # Check if already allocated (idempotency within resource map)
        for rid, eid in registry.items():
            if eid == entity_id:
                return rid

        # New Allocation
        for rid, eid in registry.items():
            if eid is None:
                registry[rid] = entity_id
                return rid

        raise RuntimeError("Capacity Exhausted: No resources available in national grid")

    def release_resource(self, action: str, entity_id: str):
        with self._lock:
            registry = self.airport_assets if "GATE" in action else self.seaport_assets
            for rid, eid in registry.items():
                if eid == entity_id:
                    registry[rid] = None
                    logger.info(f"XPORT Release: {rid} freed from {entity_id}")
                    return True
            return False

# Global Singleton Orchestrator
orchestrator = XportOrchestrator()

from enum import Enum
from datetime import datetime, timezone
from typing import List, Dict, Any
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow

class DBMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"

class ShadowSyncEngine:
    """
    Sovereign Continuity Engine: Manages local data persistence and reconciliation.
    Ensures operation during total disconnection.
    """
    def __init__(self):
        self.mode = DBMode.READ_ONLY
        self.local_queue: List[Dict[str, Any]] = []
        self.local_db: Dict[str, Any] = {"bookings": [], "finance": [], "identity": []}

        # Subscribe to CABLE_CUT event
        events.subscribe("nexus.emergency.triggered", self._handle_disconnection)

    def _handle_disconnection(self, payload: Dict[str, Any]):
        """Triggered by emergency/cable-cut signal."""
        data = payload.get("data", {})
        # Check input or payload content for disconnection triggers
        input_data = data.get("input", {})
        if input_data.get("type") == "CABLE_CUT" or "SOS" in str(data):
            self.promote_to_read_write()

    def promote_to_read_write(self):
        """Activates local execution mode."""
        print("[SHADOW-SYNC] PROMOTING TO READ_WRITE MODE (Failover active)")
        self.mode = DBMode.READ_WRITE

    def ingest_cloud_event(self, event: Dict[str, Any]):
        """CDC Listener: Applies cloud changes to local mirror."""
        if self.mode == DBMode.READ_ONLY:
            self._apply_to_local(event)

    def process_local_execution(self, action: str, data: Dict[str, Any]):
        """Handles execution during disconnection."""
        if self.mode != DBMode.READ_WRITE:
             raise RuntimeError("Local DB is READ_ONLY. Disconnection mode not active.")

        # Record locally
        self._apply_to_local({"type": action, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})
        # Queue for reconciliation
        self.local_queue.append({"action": action, "data": data, "ts": datetime.now(timezone.utc).timestamp()})
        print(f"[SHADOW-SYNC] Local execution recorded: {action}")

    def reconcile_with_cloud(self):
        """Pushes local changes back to cloud using timestamp-based reconciliation."""
        # MUST wrap in sovereign context to allow shadow.commit via events.publish
        from mnos.shared.execution_guard import in_sovereign_context, guard
        import time
        token = in_sovereign_context.set(True)

        try:
            print(f"[SHADOW-SYNC] Reconciling {len(self.local_queue)} items...")
            # Sort by timestamp
            self.local_queue.sort(key=lambda x: x["ts"])

            reconciled_count = 0
            for item in self.local_queue:
                # Pushing to SHADOW via Guard
                guard.execute_sovereign_action(
                    item["action"],
                    item["data"],
                    {"user_id": "SYNC-PROC", "session_id": "SYNC", "device_id": "nexus-admin-01", "issued_at": int(time.time()), "nonce": f"N-SYNC-{reconciled_count}", "signature": "TRUSTED"},
                    lambda x: None
                )
                reconciled_count += 1

            self.local_queue = []
            self.mode = DBMode.READ_ONLY
            print(f"[SHADOW-SYNC] Reconciliation complete. Mode: {self.mode}")
            return reconciled_count
        finally:
            in_sovereign_context.reset(token)

    def _apply_to_local(self, event: Dict[str, Any]):
        """Internal local mirror update."""
        # Simplification: append to internal dict
        etype = event.get("type") or "generic"
        if etype not in self.local_db:
            self.local_db[etype] = []
        self.local_db[etype].append(event.get("data"))

shadow_sync = ShadowSyncEngine()

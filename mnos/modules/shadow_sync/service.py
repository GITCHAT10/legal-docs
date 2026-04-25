import uuid
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
        self.provisional_seals: List[Dict[str, Any]] = []

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

    def process_local_execution(self, action: str, data: Dict[str, Any], trace_id: str = None, session_context: Dict[str, Any] = None):
        """Handles execution during disconnection. Enforces WAL append integrity."""
        if self.mode != DBMode.READ_WRITE:
             raise RuntimeError("Local DB is READ_ONLY. Disconnection mode not active.")

        # WAL Append with previous_hash continuity simulation
        prev_hash = self.local_queue[-1].get("hash") if self.local_queue else "0"*64

        entry = {
            "action": action,
            "data": data,
            "trace_id": trace_id or str(uuid.uuid4()),
            "ts": datetime.now(timezone.utc).timestamp(),
            "previous_hash": prev_hash,
            "session_context": session_context
        }
        # Simplified hash for WAL continuity
        import hashlib
        entry["hash"] = hashlib.sha256(str(entry).encode()).hexdigest()

        # Record locally
        self._apply_to_local({"type": action, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})
        # Queue for reconciliation
        self.local_queue.append(entry)
        print(f"[SHADOW-SYNC] Local execution (WAL) recorded: {action} | Trace: {entry['trace_id']}")

    def create_local_provisional_seal(self):
        """Generates a local seal for a closed business day while offline."""
        if not self.local_queue:
            return None

        seal = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "head_hash": self.local_queue[-1]["hash"],
            "event_count": len(self.local_queue),
            "status": "PROVISIONAL"
        }
        self.provisional_seals.append(seal)
        print(f"[SHADOW-SYNC] PROVISIONAL SEAL CREATED: {seal['head_hash'][:16]}")
        return seal

    def reconcile_with_cloud(self, batch_size: int = None):
        """
        Pushes local changes back to cloud using timestamp-based reconciliation.
        Supports partial replay and idempotency.
        """
        from mnos.shared.execution_guard import in_sovereign_context, guard
        from mnos.core.security.aegis import aegis
        import time
        token = in_sovereign_context.set(True)

        try:
            items_to_process = self.local_queue
            if batch_size:
                items_to_process = self.local_queue[:batch_size]

            print(f"[SHADOW-SYNC] Replaying {len(items_to_process)} items (Mode: {self.mode})...")
            # Sort by timestamp to ensure deterministic replay order
            items_to_process.sort(key=lambda x: x["ts"])

            reconciled_count = 0
            for item in items_to_process:
                # Use original session context if available, else system sync
                ctx = item.get("session_context")
                if not ctx or "signature" not in ctx:
                    ctx = {
                        "user_id": "SYNC-PROC",
                        "session_id": "SYNC",
                        "device_id": "nexus-admin-01",
                        "issued_at": int(time.time()),
                        "nonce": f"N-SYNC-{reconciled_count}-{item['trace_id'][:8]}"
                    }
                    ctx["signature"] = aegis.sign_session(ctx)

                # Pushing to SHADOW via Guard
                # Note: guard will handle the trace_id/idempotency check at the event level
                guard.execute_sovereign_action(
                    item["action"],
                    item["data"],
                    ctx,
                    lambda x: None
                )
                reconciled_count += 1

            # Remove processed items from queue
            self.local_queue = self.local_queue[reconciled_count:]

            if not self.local_queue:
                self.mode = DBMode.READ_ONLY
                # Promote provisional seals to FINAL
                for seal in self.provisional_seals:
                    seal["status"] = "FINAL"
                print(f"[SHADOW-SYNC] Reconciliation complete. Mode: {self.mode}")
            else:
                print(f"[SHADOW-SYNC] Partial replay finished. {len(self.local_queue)} items remain.")

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

import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional

class UTMVPBridge:
    """
    UT MVP Bridge: Connects Flight delays to UT Transfer rescheduling.
    Rule: Delay > 30m -> New Pickup = Arrival + 45m.
    """
    def __init__(self, core):
        self.core = core
        self.pending_adjustments = {} # adj_id -> data
        self.capacity_cache = {} # bucket -> available_slots

    def attempt_auto_adjust(self, actor_ctx: dict, flight_id: str, delay_min: int, pax_count: int, ut_ticket_ref: str):
        """
        Logic: Calculate new time, check capacity, update UT or queue for manual.
        """
        if delay_min <= 30:
            return {"status": "NO_ACTION_REQUIRED"}

        # 1. Calculate New Time (Arrival + 45m buffer)
        # For simplicity in MVP, we use relative adjustment
        new_offset = delay_min + 45

        # 2. Capacity Check (Simulated)
        # Rounded to 15m bucket
        bucket = (datetime.now(UTC) + timedelta(minutes=new_offset)).replace(second=0, microsecond=0)
        available = self.capacity_cache.get(bucket, 10) # Default 10 for demo

        if available >= pax_count:
            # 3a. AUTO ADJUST
            self.capacity_cache[bucket] = available - pax_count
            adjustment = {
                "id": f"ADJ-{uuid.uuid4().hex[:6].upper()}",
                "ut_ticket_ref": ut_ticket_ref,
                "flight_id": flight_id,
                "new_pickup_offset": new_offset,
                "status": "AUTO_CONFIRMED"
            }
            self.core.events.publish("ut_mvp.auto_adjusted", adjustment)
            return adjustment
        else:
            # 3b. QUEUE FOR MANUAL
            adj_id = f"MADJ-{uuid.uuid4().hex[:6].upper()}"
            adjustment = {
                "id": adj_id,
                "ut_ticket_ref": ut_ticket_ref,
                "flight_id": flight_id,
                "delay_minutes": delay_min,
                "pax_count": pax_count,
                "status": "PENDING_MANUAL"
            }
            self.pending_adjustments[adj_id] = adjustment
            self.core.events.publish("ut_mvp.manual_queued", adjustment)
            return adjustment

    def process_manual_override(self, actor_ctx: dict, adj_id: str, action: str):
        """Ops Lead manually approves or rejects adjustment."""
        return self.core.execute_commerce_action(
            f"ut_mvp.manual.{action}",
            actor_ctx,
            self._internal_process_manual,
            adj_id, action
        )

    def _internal_process_manual(self, adj_id: str, action: str):
        adj = self.pending_adjustments.get(adj_id)
        if not adj: raise ValueError("Adjustment not found")

        adj["status"] = "MANUAL_APPROVED" if action == "approve" else "MANUAL_REJECTED"
        adj["processed_at"] = datetime.now(UTC).isoformat()

        # Cleanup
        del self.pending_adjustments[adj_id]

        self.core.events.publish("ut_mvp.manual_processed", adj)
        return adj

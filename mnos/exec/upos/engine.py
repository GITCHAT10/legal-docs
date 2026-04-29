import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

class UPOSEngine:
    """
    UPOS Engine (Unified POS) for SALA Node.
    Handles F&B mode, inventory, and order processing.
    Enforces Trace ID and Idempotency.
    """
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.inventory = {} # item_id -> qty
        self.processed_orders = set() # idempotency_keys

    def create_order(self, merchant_id: str, actor_id: str, items: List[Dict], amount: float,
                     idempotency_key: str, trace_id: str) -> Dict:
        """
        Creates an order with strict idempotency and tracing.
        Internal logic only. Execution via ExecutionGuard.
        """
        if not trace_id:
            raise ValueError("TRACE_ID_REQUIRED: Cannot process order without trace context.")

        if not idempotency_key:
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED: Prevention of double spend/invoice.")

        if idempotency_key in self.processed_orders:
            raise ValueError(f"IDEMPOTENCY_VIOLATION: Order {idempotency_key} already processed.")

        # 1. Price calculation via FCE (Hardened with idempotency)
        pricing = self.fce.calculate_order(amount, category="RETAIL", idempotency_key=idempotency_key)

        order = {
            "order_id": f"UPOS-{uuid.uuid4().hex[:8].upper()}",
            "merchant_id": merchant_id,
            "items": items,
            "pricing": pricing,
            "status": "COMPLETED",
            "timestamp": datetime.now(UTC).isoformat(),
            "idempotency_key": idempotency_key,
            "trace_id": trace_id
        }

        # 2. Audit in SHADOW (Enforces Trace ID & Idempotency)
        self.shadow.commit("upos.order.completed", actor_id, order, trace_id=trace_id)

        # 3. Publish Event
        self.events.publish("upos.order.completed", order)

        # 4. Mark as processed
        self.processed_orders.add(idempotency_key)

        return order

    def update_inventory(self, item_id: str, qty: float):
        self.inventory[item_id] = self.inventory.get(item_id, 0.0) + qty

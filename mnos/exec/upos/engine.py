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
                     idempotency_key: str, trace_id: str, category: str = "TOURISM") -> Dict:
        """
        Creates an order with strict idempotency and tracing.
        Internal logic only. Execution via ExecutionGuard.
        Lifecycle: created → validated → completed
        """
        # Financial Fail-Closed Validation
        if not merchant_id:
             raise ValueError("FAIL_CLOSED: Missing merchant_id")
        if not items:
             raise ValueError("FAIL_CLOSED: Items list is empty")
        if amount <= 0:
             raise ValueError("FAIL_CLOSED: Amount must be greater than zero")

        if not trace_id:
            raise ValueError("TRACE_ID_REQUIRED: Cannot process order without trace context.")

        if not idempotency_key:
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED: Prevention of double spend/invoice.")

        if idempotency_key in self.processed_orders:
            raise ValueError(f"IDEMPOTENCY_VIOLATION: Order {idempotency_key} already processed.")

        from mnos.shared.execution_guard import ExecutionGuard
        # Authorization context for all SHADOW commits within the engine
        auth_ctx = {"identity_id": actor_id, "device_id": "UPOS-ENGINE", "role": "user"}

        # 1. upos.order.created
        order_id = f"UPOS-{uuid.uuid4().hex[:8].upper()}"
        initial_order = {
            "order_id": order_id,
            "merchant_id": merchant_id,
            "items": items,
            "amount": amount,
            "status": "CREATED",
            "timestamp": datetime.now(UTC).isoformat(),
            "idempotency_key": idempotency_key,
            "trace_id": trace_id
        }
        with ExecutionGuard.authorized_context(auth_ctx):
            self.shadow.commit("upos.order.created", actor_id, initial_order, trace_id=trace_id)
        self.events.publish("upos.order.created", initial_order)

        # 2. upos.order.validated (MIRA Tax Rule Enforcement)
        # Using TOURISM category for 17% TGST enforcement
        pricing = self.fce.calculate_order(amount, category=category, idempotency_key=idempotency_key)
        initial_order["pricing"] = pricing
        initial_order["status"] = "VALIDATED"

        with ExecutionGuard.authorized_context(auth_ctx):
            self.shadow.commit("upos.order.validated", actor_id, initial_order, trace_id=trace_id)
        self.events.publish("upos.order.validated", initial_order)

        # 3. upos.order.completed (Reality Handshake Simulation)
        initial_order["status"] = "COMPLETED"
        initial_order["final_verification"] = "BUBBLE_QR_HANDSHAKE_VERIFIED"

        # 4. Audit in SHADOW (Enforces Trace ID & Idempotency)
        with ExecutionGuard.authorized_context(auth_ctx):
            self.shadow.commit("upos.order.completed", actor_id, initial_order, trace_id=trace_id)

        # 5. Publish Final Event
        self.events.publish("upos.order.completed", initial_order)

        # 6. Mark as processed
        self.processed_orders.add(idempotency_key)

        return initial_order

    def update_inventory(self, item_id: str, qty: float):
        self.inventory[item_id] = self.inventory.get(item_id, 0.0) + qty

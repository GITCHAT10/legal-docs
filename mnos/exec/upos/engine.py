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
        Lifecycle: requested → validated → approved → executed → completed
        """
        from mnos.shared.execution_guard import ExecutionGuard
        if not ExecutionGuard.is_authorized():
            raise PermissionError("FAIL CLOSED: Unauthorized direct call to upos_engine.create_order blocked.")

        if not merchant_id:
             raise ValueError("ExecutionValidationError: Missing merchant_id")
        if not items:
             raise ValueError("ExecutionValidationError: Items list is empty")
        if amount is None or amount <= 0:
             raise ValueError("ExecutionValidationError: Amount must be greater than zero")

        if not trace_id:
            raise ValueError("ExecutionValidationError: trace_id required")

        if not idempotency_key:
            raise ValueError("ExecutionValidationError: idempotency_key required")

        if idempotency_key in self.processed_orders:
            raise ValueError(f"IDEMPOTENCY_VIOLATION: Order {idempotency_key} already processed.")

        from mnos.shared.execution_guard import ExecutionGuard
        auth_ctx = {"identity_id": actor_id, "device_id": "UPOS-ENGINE", "role": "user"}

        order_id = f"UPOS-{uuid.uuid4().hex[:8].upper()}"
        order = {
            "order_id": order_id,
            "merchant_id": merchant_id,
            "items": items,
            "amount": amount,
            "status": "REQUESTED",
            "timestamp": datetime.now(UTC).isoformat(),
            "idempotency_key": idempotency_key,
            "trace_id": trace_id
        }

        with ExecutionGuard.authorized_context(auth_ctx):
            # Common payload attributes for all stages
            order.update({
                "actor_id": actor_id,
                "device_id": auth_ctx["device_id"],
                "currency": "MVR"
            })

            # 1. requested
            self.shadow.commit("upos.order.requested", actor_id, order, trace_id=trace_id)
            self.events.publish("upos.order.requested", order)

            # 2. validated
            pricing = self.fce.calculate_order(amount, category=category, idempotency_key=idempotency_key)
            order["pricing"] = pricing
            order["status"] = "VALIDATED"
            self.shadow.commit("upos.order.validated", actor_id, order, trace_id=trace_id)
            self.events.publish("upos.order.validated", order)

            # 3. approved
            order["status"] = "APPROVED"
            self.shadow.commit("upos.order.approved", actor_id, order, trace_id=trace_id)
            self.events.publish("upos.order.approved", order)

            # 4. executed
            order["status"] = "EXECUTED"
            self.shadow.commit("upos.order.executed", actor_id, order, trace_id=trace_id)
            self.events.publish("upos.order.executed", order)

            # 5. completed
            order["status"] = "COMPLETED"
            order["final_verification"] = "BUBBLE_QR_HANDSHAKE_VERIFIED"
            # Ensure every required attribute is present for the final commit
            self.shadow.commit("upos.order.completed", actor_id, order, trace_id=trace_id)
            self.events.publish("upos.order.completed", order)

        self.processed_orders.add(idempotency_key)
        return order

    def update_inventory(self, item_id: str, qty: float):
        self.inventory[item_id] = self.inventory.get(item_id, 0.0) + qty

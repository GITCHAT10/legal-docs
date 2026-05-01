import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from decimal import Decimal

class UPOSCommerceCore:
    """
    UPOS Commerce Core: Standardized transaction engine for all U-Series verticals.
    Workflow: AEGIS -> ORCA -> ExecutionGuard -> UPOS -> FCE -> SHADOW
    """
    def __init__(self, guard, orca, fce, shadow, events, escrow):
        self.guard = guard
        self.orca = orca
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.escrow = escrow
        self.orders = {}

    def execute_transaction(self, action_type: str, actor_ctx: Dict, logic_func: Any, *args, **kwargs):
        """
        Universal Transaction Workflow entrypoint.
        """
        # 1. AEGIS/ORCA Rule Validation
        valid, msg = self.orca.validate_action(action_type, actor_ctx)
        if not valid:
            raise PermissionError(f"ORCA REJECTION: {msg}")

        # 2. Execution through Guard (AEGIS + SHADOW + Atomicity)
        return self.guard.execute_sovereign_action(
            action_type,
            actor_ctx,
            logic_func,
            *args, **kwargs
        )

    # --- Standardized Order Lifecycle ---

    def create_order(self, actor_ctx: dict, data: dict, category: str = "RETAIL"):
        return self.execute_transaction(
            "upos.order.create",
            actor_ctx,
            self._internal_create_order,
            data, category
        )

    def _internal_create_order(self, data, category):
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        amount = data.get("amount", 0)

        # FCE Calculation
        pricing = self.fce.finalize_invoice(amount, category)

        # Global Commerce Reserves
        if category == "GLOBAL_COMMERCE":
            reserves = data.get("reserves", {})
            pricing["reserves"] = {
                "supplier_payable": reserves.get("supplier", amount * 0.7),
                "freight_reserve": reserves.get("freight", 50.0),
                "customs_reserve": reserves.get("customs", 150.0),
                "port_reserve": reserves.get("port", 100.0),
                "clearance_reserve": 50.0,
                "domestic_reserve": 30.0,
                "platform_fee": amount * 0.05
            }

        order = {
            "id": order_id,
            "tenant_id": data.get("tenant_id"),
            "customer_id": self.guard.get_actor().get("identity_id"),
            "items": data.get("items"),
            "pricing": pricing,
            "status": "PLACED",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.orders[order_id] = order
        self.events.publish("upos.order_created", order)
        return order

    def process_payment(self, actor_ctx: dict, order_id: str, payment_method: str):
        return self.execute_transaction(
            "upos.payment.process",
            actor_ctx,
            self._internal_payment,
            order_id, payment_method
        )

    def _internal_payment(self, order_id, method):
        order = self.orders.get(order_id)
        if not order: raise ValueError("Order not found")

        # Record payment
        payment_record = {
            "order_id": order_id,
            "method": method,
            "amount": order["pricing"]["total"],
            "status": "PAID",
            "timestamp": datetime.now(UTC).isoformat()
        }
        order["status"] = "PAID"
        order["payment"] = payment_record

        self.events.publish("upos.payment_completed", payment_record)
        return payment_record

    def finalize_settlement(self, actor_ctx: dict, order_id: str):
        return self.execute_transaction(
            "upos.settlement.finalize",
            actor_ctx,
            self._internal_settle,
            order_id
        )

    def _internal_settle(self, order_id):
        order = self.orders.get(order_id)
        if not order or order["status"] != "PAID":
            raise ValueError("Order not ready for settlement")

        # Payout logic via FCE
        settlement = self.fce.process_clearing_settlement(
            order["pricing"]["base"],
            {"platform": 0.05, "vendor": 0.95}
        )
        order["status"] = "SETTLED"
        order["settlement"] = settlement

        return settlement

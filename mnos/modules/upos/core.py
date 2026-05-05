import uuid
from datetime import datetime, UTC
from typing import Dict, Any

class UPOSCommerceCore:
    """
    iMOXON.UPOS Commerce Execution: Universal commerce engine for the MNOS ecosystem.
    Workflow: AEGIS -> ORCA -> ExecutionGuard -> UPOS -> FCE -> SHADOW

    UPOS owns checkout, POS, marketplace cart, and transaction execution.
    It does NOT own hotel/travel package/transport movement truth.
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
        if not order:
            raise ValueError("Order not found")

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

    # --- PRESTIGE GIANT BRAIN Integration APIs ---

    def create_payment_link(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.payment_link.create", actor_ctx, self._internal_create_paylink, data)

    def _internal_create_paylink(self, data):
        paylink_id = f"PL-{uuid.uuid4().hex[:8].upper()}"
        return {"id": paylink_id, "url": f"https://upos.pay/{paylink_id}", "status": "ACTIVE"}

    def create_invoice(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.invoice.create", actor_ctx, self._internal_create_invoice, data)

    def _internal_create_invoice(self, data):
        # Mandatory FCE tax calculation
        amount = data.get("amount", 0)
        pricing = self.fce.finalize_invoice(amount, data.get("category", "RETAIL"))
        return {"id": f"INV-{uuid.uuid4().hex[:8].upper()}", "pricing": pricing}

    def create_qr_pay(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.qr_pay.create", actor_ctx, self._internal_create_qr, data)

    def _internal_create_qr(self, data):
        return {"qr_code": f"UPOS-QR-{uuid.uuid4().hex[:8].upper()}", "amount": data.get("amount")}

    def charge_wallet(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.wallet.charge", actor_ctx, self._internal_wallet_charge, data)

    def _internal_wallet_charge(self, data):
        return {"status": "SUCCESS", "balance_after": 5000.0}

    def create_refund(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.refund.create", actor_ctx, self._internal_refund, data)

    def _internal_refund(self, data):
        return {"refund_id": f"REF-{uuid.uuid4().hex[:8].upper()}", "status": "PROCESSED"}

    def create_split_settlement(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.settlement.split.create", actor_ctx, self._internal_split_settle, data)

    def _internal_split_settle(self, data):
        return {"settlement_id": f"SET-{uuid.uuid4().hex[:8].upper()}", "splits": data.get("splits")}

    def get_transaction(self, actor_ctx: dict, tx_id: str):
        # Read-only query via Guard
        return self.guard.execute_sovereign_action("upos.transaction.query", actor_ctx, self._internal_get_tx, tx_id)

    def _internal_get_tx(self, tx_id):
        return {"id": tx_id, "status": "COMPLETED", "amount": 1250.0}

    def get_merchant_status(self, actor_ctx: dict, merchant_id: str):
        return self.guard.execute_sovereign_action("upos.merchant.query", actor_ctx, self._internal_merchant_status, merchant_id)

    def _internal_merchant_status(self, merchant_id):
        return {"merchant_id": merchant_id, "status": "ACTIVE", "kyc": "VERIFIED"}

    def calculate_revenue_share(self, actor_ctx: dict, data: dict):
        return self.execute_transaction("upos.revenue_share.calculate", actor_ctx, self._internal_rev_share, data)

    def _internal_rev_share(self, data):
        amount = data.get("amount", 0)
        return {"gross": amount, "platform_fee": amount * 0.05, "vendor_net": amount * 0.95}

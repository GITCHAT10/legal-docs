import uuid
from datetime import datetime, UTC

class ProcurementEngine:
    """
    Robust Procurement Lifecycle Engine (RC1-PRODUCTION-BRIDGE)
    Implements the full PR-PO-GRN-Invoice-Settlement state machine.
    States: CREATED -> APPROVED -> DISPATCHED -> DELIVERED -> INVOICED -> SETTLED
    """
    def __init__(self, guard, shadow, events, fce, escrow):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.fce = fce
        self.escrow = escrow
        self.orders = {} # state machine storage

    def create_purchase_request(self, actor_ctx: dict, items: list, estimated_amount: float):
        return self.guard.execute_sovereign_action(
            "procurement.pr.create",
            actor_ctx,
            self._internal_create_pr,
            items, estimated_amount
        )

    def _internal_create_pr(self, items, amount):
        pr_id = f"PR-{uuid.uuid4().hex[:8].upper()}"
        order = {
            "id": pr_id,
            "items": items,
            "amount": amount,
            "status": "CREATED",
            "approvals": [],
            "created_at": datetime.now(UTC).isoformat()
        }
        self.orders[pr_id] = order
        self.events.publish("procurement.pr_created", order)
        return order

    def approve_order(self, actor_ctx: dict, order_id: str):
        """
        Implements DUAL_APPROVAL_FOR_HIGH_VALUE_TRANSACTIONS logic.
        """
        return self.guard.execute_sovereign_action(
            "procurement.order.approve",
            actor_ctx,
            self._internal_approve,
            order_id
        )

    def _internal_approve(self, order_id):
        order = self.orders.get(order_id)
        if not order: raise ValueError("Order not found")

        actor = self.guard.get_actor()
        if actor["identity_id"] not in order["approvals"]:
            order["approvals"].append(actor["identity_id"])

        # Threshold for dual approval
        threshold = 50000 # 50k MVR
        required_approvals = 2 if order["amount"] > threshold else 1

        if len(order["approvals"]) >= required_approvals:
            order["status"] = "APPROVED"
            # Lock funds in Escrow upon approval
            self.escrow.lock_funds(actor["identity_id"], order_id, order["amount"])
            self.events.publish("procurement.order_approved", order)

        return order

    def mark_dispatched(self, actor_ctx: dict, order_id: str):
        return self.guard.execute_sovereign_action(
            "procurement.order.dispatch",
            actor_ctx,
            self._internal_update_status,
            order_id, "DISPATCHED"
        )

    def mark_delivered(self, actor_ctx: dict, order_id: str):
        return self.guard.execute_sovereign_action(
            "procurement.order.deliver",
            actor_ctx,
            self._internal_update_status,
            order_id, "DELIVERED"
        )

    def finalize_invoice(self, actor_ctx: dict, order_id: str):
        return self.guard.execute_sovereign_action(
            "procurement.order.invoice",
            actor_ctx,
            self._internal_invoice,
            order_id
        )

    def _internal_invoice(self, order_id):
        order = self.orders.get(order_id)
        if not order: raise ValueError("Order not found")

        # MIRA-compliant tax calculation via FCE
        pricing = self.fce.finalize_invoice(order["amount"], "RESORT_SUPPLY")
        order["pricing"] = pricing
        order["status"] = "INVOICED"

        self.events.publish("procurement.invoiced", order)
        return order

    def settle_payment(self, actor_ctx: dict, order_id: str):
        """
        Enforce NATIONAL_ID_BINDING_REQUIRED_FOR_SETTLEMENT check.
        """
        return self.guard.execute_sovereign_action(
            "procurement.order.settle",
            actor_ctx,
            self._internal_settle,
            order_id
        )

    def _internal_settle(self, order_id):
        order = self.orders.get(order_id)
        if not order: raise ValueError("Order not found")

        # Simulated check for national ID binding in actor context
        actor = self.guard.get_actor()
        if not actor.get("national_id_verified"):
            raise PermissionError("FAIL CLOSED: National ID binding required for settlement")

        # Release funds from Escrow upon settlement
        self.escrow.release_to_settlement(actor["identity_id"], order_id)

        order["status"] = "SETTLED"
        self.events.publish("procurement.settled", order)
        return order

    def _internal_update_status(self, order_id, status):
        if order_id in self.orders:
            self.orders[order_id]["status"] = status
            return self.orders[order_id]
        raise ValueError("Order not found")

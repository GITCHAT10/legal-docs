class CommerceEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.vendors = {} # vendor_id -> details
        self.orders = {}

    def approve_vendor(self, actor_ctx: dict, vendor_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.vendor.approve",
            actor_ctx,
            self._internal_approve_vendor,
            vendor_data
        )

    def _internal_approve_vendor(self, vendor_data: dict):
        vendor_id = vendor_data.get("did")
        self.vendors[vendor_id] = {
            "did": vendor_id,
            "business_name": vendor_data.get("business_name"),
            "kyc_status": "APPROVED",
            "risk_score": 0.05,
            "approved_by": self.guard.get_actor().get("identity_id"),
            "status": "ACTIVE"
        }
        self.events.publish("vendor.approved", self.vendors[vendor_id])
        return self.vendors[vendor_id]

    def create_order(self, actor_ctx: dict, order_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.order.create",
            actor_ctx,
            self._internal_create_order,
            order_data
        )

    def _internal_create_order(self, order_data: dict):
        vendor_id = order_data.get("vendor_id")
        if vendor_id not in self.vendors or self.vendors[vendor_id]["kyc_status"] != "APPROVED":
            raise ValueError("FAIL CLOSED: Vendor not approved or missing KYC")

        # Central FCE Pricing
        pricing = self.fce.price_order(order_data.get("amount"))

        order_id = f"ord_{uuid.uuid4().hex[:6]}"
        order = {
            "id": order_id,
            "user": self.guard.get_actor().get("identity_id"),
            "vendor": vendor_id,
            "pricing": pricing,
            "status": "CREATED"
        }
        self.orders[order_id] = order
        self.events.publish("order.created", order)
        return order
import uuid

import uuid
from datetime import datetime, UTC

class UStorageGlobalEngine:
    """
    U-Storage Global: Overseas hub receiving and verification.
    Doctrine: receive only paid/FCE-approved orders.
    """
    def __init__(self, upos, shadow):
        self.upos = upos
        self.shadow = shadow
        self.inventory = {}

    def receive_package(self, actor_ctx: dict, order_id: str, hub_id: str, data: dict):
        # 1. DOCTRINE CHECK: Is order paid?
        order = self.upos.orders.get(order_id)
        if not order or order.get("status") != "PAID":
            raise PermissionError(f"DOCTRINE REJECTION: Hub receiving blocked for unpaid order {order_id}")

        # 2. Process receiving
        pkg_id = f"PKG-{uuid.uuid4().hex[:6].upper()}"
        receiving_record = {
            "id": pkg_id,
            "order_id": order_id,
            "hub_id": hub_id,
            "received_at": datetime.now(UTC).isoformat(),
            "quantity_verified": data.get("quantity"),
            "photo_proof": data.get("photo_url"),
            "status": "RECEIVED_AT_HUB"
        }
        self.inventory[pkg_id] = receiving_record

        return receiving_record

    def assign_to_consolidation(self, actor_ctx: dict, pkg_ids: list, batch_id: str):
        # DOCTRINE GATE: No hub receiving/consolidation without paid order
        # (already checked in receive_package, but double check status here)
        for pid in pkg_ids:
            pkg = self.inventory.get(pid)
            if pkg:
                order = self.upos.orders.get(pkg["order_id"])
                if not order or order["status"] != "PAID":
                     raise PermissionError(f"GLOBAL GATE: Consolidation blocked for unpaid order in package {pid}")

                pkg["status"] = "CONSOLIDATED"
                pkg["batch_id"] = batch_id

        return True

import uuid
from datetime import datetime, UTC

class UMarineEngine:
    """
    U-Marine Vertical: Boats, charters, and transfers.
    """
    def __init__(self, upos):
        self.upos = upos
        self.vessels = {}

    def register_vessel(self, actor_ctx: dict, vessel_data: dict):
        return self.upos.execute_transaction(
            "u_marine.vessel.register",
            actor_ctx,
            self._internal_register_vessel,
            vessel_data
        )

    def _internal_register_vessel(self, data):
        v_id = f"VES-{uuid.uuid4().hex[:6].upper()}"
        vessel = {
            "id": v_id,
            "name": data.get("name"),
            "type": data.get("type"),
            "owner": self.upos.guard.get_actor().get("identity_id")
        }
        self.vessels[v_id] = vessel
        return vessel

    def book_transfer(self, actor_ctx: dict, route_data: dict):
        return self.upos.execute_transaction(
            "upos.order.create",
            actor_ctx,
            self._internal_book,
            route_data
        )

    def _internal_book(self, data):
        order = self.upos._internal_create_order(
            {"amount": data.get("fare", 0), "tenant_id": data.get("vessel_id")},
            "TOURISM"
        )
        return {"ticket_id": f"TR-{uuid.uuid4().hex[:6].upper()}", "order_id": order["id"]}

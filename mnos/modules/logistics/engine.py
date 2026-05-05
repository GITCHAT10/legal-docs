import uuid
from datetime import datetime, UTC

class ULogisticsEngine:
    """
    U-Logistics: International freight movement and proof layer.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.shipments = {}

    def create_shipment(self, actor_ctx: dict, batch_id: str, mode: str = "SEA"):
        shipment_id = f"SHIP-{uuid.uuid4().hex[:6].upper()}"
        shipment = {
            "id": shipment_id,
            "batch_id": batch_id,
            "mode": mode,
            "status": "BOOKED",
            "timeline": [{"status": "BOOKED", "ts": datetime.now(UTC).isoformat()}]
        }
        self.shipments[shipment_id] = shipment
        self.shadow.commit("logistics.shipment.booked", actor_ctx.get("identity_id"), {"shipment_id": shipment_id})
        return shipment

    def update_status(self, actor_ctx: dict, shipment_id: str, status: str):
        if shipment_id in self.shipments:
            self.shipments[shipment_id]["status"] = status
            self.shipments[shipment_id]["timeline"].append({
                "status": status,
                "ts": datetime.now(UTC).isoformat()
            })
            # Track official milestones in SHADOW
            official_milestones = ["CARGO_LOADED", "DEPARTED", "ARRIVED_MALDIVES", "RELEASED"]
            if status in official_milestones:
                 self.shadow.commit(f"logistics.{status.lower()}", actor_ctx.get("identity_id"), {"shipment_id": shipment_id})
            return True
        return False

    def get_shipment(self, shipment_id: str):
        return self.shipments.get(shipment_id)

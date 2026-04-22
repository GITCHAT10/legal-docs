class LogisticsEngine:
    def __init__(self, shadow, events, geo):
        self.shadow = shadow
        self.events = events
        self.geo = geo
        self.shipments = {}

    def create_shipment(self, sender_id: str, origin: str, destination: str, items: list):
        shipment_id = f"shp_{hash(sender_id + origin + destination) % 10000}"
        shipment = {
            "shipment_id": shipment_id,
            "sender_id": sender_id,
            "origin": origin,
            "destination": destination,
            "items": items,
            "status": "CREATED"
        }

        self.shadow.record_action("shipment.created", shipment)
        self.events.trigger("SHIPMENT_CREATED", shipment)
        self.shipments[shipment_id] = shipment
        return shipment

    def deliver_shipment(self, shipment_id: str):
        if shipment_id in self.shipments:
            self.shipments[shipment_id]["status"] = "DELIVERED"
            self.shadow.record_action("shipment.delivered", {"id": shipment_id})
            self.events.trigger("SHIPMENT_DELIVERED", {"id": shipment_id})
            return True
        return False

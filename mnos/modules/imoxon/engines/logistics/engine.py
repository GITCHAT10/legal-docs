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

        self.shadow.commit("shipment.created", shipment)
        self.events.publish("SHIPMENT_CREATED", shipment)
        self.shipments[shipment_id] = shipment
        return shipment

    def deliver_shipment(self, shipment_id: str):
        if shipment_id in self.shipments:
            self.shipments[shipment_id]["status"] = "DELIVERED"
            self.shadow.commit("shipment.delivered", {"id": shipment_id})
            self.events.publish("SHIPMENT_DELIVERED", {"id": shipment_id})
            return True
        return False

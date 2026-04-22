class TransportEngine:
    def __init__(self, aegis, fce, shadow, events):
        self.aegis = aegis
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.drivers = {} # driver_id -> status

    def request_ride(self, user_id: str, device_id: str, role: str, pickup: str, destination: str):
        # 1. AEGIS verify (local only)
        self.aegis.authorize(user_id, device_id, role)

        # 2. Fare calculation via FCE
        fare = self.fce.price_order(15.0)

        ride_event = {
            "user_id": user_id,
            "pickup": pickup,
            "destination": destination,
            "fare": fare,
            "status": "REQUESTED"
        }

        self.shadow.record_action("ride.requested", ride_event)
        self.events.trigger("RIDE_REQUESTED", ride_event)
        return ride_event

    def assign_driver(self, ride_id: str, driver_id: str):
        self.drivers[driver_id] = "BUSY"
        self.events.trigger("DRIVER_ASSIGNED", {"ride_id": ride_id, "driver_id": driver_id})
        return True

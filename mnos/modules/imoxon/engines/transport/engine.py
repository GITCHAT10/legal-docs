class TransportEngine:
    def __init__(self, aegis, fce, shadow, events):
        self.aegis = aegis
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def request_ride(self, user_id: str, device_id: str, role: str, pickup: str, destination: str):
        # 1. AEGIS: Mandatory Identity & Role check
        self.aegis.authorize(user_id, device_id, role)

        # 2. FCE: Mandatory Pricing
        pricing = self.fce.price_order(15.0) # Base taxi fare 15 MVR

        ride = {
            "user": user_id,
            "pickup": pickup,
            "destination": destination,
            "pricing": pricing,
            "status": "REQUESTED"
        }

        # 3. SHADOW: Mandatory Record
        self.shadow.commit("ride.requested", ride)

        # 4. EVENTS: Async trigger
        self.events.publish("RIDE_REQUESTED", ride)
        return ride

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

class AquaDispatchEngine:
    """
    AQUA Boat Operations Dispatch Engine.
    Handles vessel matching and weather-aware routing.
    """
    def __init__(self, wallet, shadow, events):
        self.wallet = wallet
        self.shadow = shadow
        self.events = events
        self.fleet = {} # vessel_id -> data

    def match_and_assign(self, route_data: Dict, pax: int, booking_id: str, trace_id: str) -> Dict:
        # 1. Weather Check (Mock)
        weather_mult = 1.0

        # 2. Match Vessel (Mock)
        vessel_id = f"VES-{uuid.uuid4().hex[:6].upper()}"
        eta = 45 # minutes

        trip = {
            "trip_id": str(uuid.uuid4()),
            "vessel_id": vessel_id,
            "route": route_data,
            "pax": pax,
            "booking_id": booking_id,
            "eta_min": eta,
            "status": "assigned",
            "timestamp": datetime.now(UTC).isoformat()
        }

        # 3. Shadow Audit
        self.shadow.commit("aqua.trip.assigned", "SYSTEM", trip, trace_id=trace_id)

        # 4. Notify Events
        self.events.publish("aqua.trip.confirmed", trip)

        return trip

class TelemetryIngestor:
    def __init__(self, events):
        self.events = events

    def process_ping(self, trip_id: str, gps_data: Dict):
        self.events.publish("aqua.telemetry.stream", {"trip_id": trip_id, **gps_data})

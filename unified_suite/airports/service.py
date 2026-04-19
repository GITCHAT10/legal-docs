from .models import Flight
from typing import List
import logging
import threading

logger = logging.getLogger("unified_suite")

class AirportService:
    def __init__(self):
        self.flights = []
        self.gates = [f"GATE_{i}" for i in range(1, 11)]
        self._lock = threading.Lock()

    def schedule_flight(self, flight: Flight):
        self.flights.append(flight)
        return flight

    def assign_gate(self, flight):
        with self._lock:
            # Compatibility: handle flight object or flight_number string
            flight_obj = flight
            if isinstance(flight, str):
                flight_obj = next((f for f in self.flights if f.flight_number == flight), None)
                if not flight_obj:
                    return None

            # ✅ Idempotency: preserve existing assignment
            if flight_obj.gate:
                logger.info(f"Idempotency: preserving existing gate {flight_obj.gate} for flight {flight_obj.flight_number}")
                return flight_obj.gate

            used_gates = [f.gate for f in self.flights if f.gate]

            for gate in self.gates:
                if gate not in used_gates:
                    flight_obj.gate = gate
                    logger.info(f"New assignment: flight {flight_obj.flight_number} assigned to {gate}")
                    return gate

            logger.error(f"Assignment failed: no gates available for flight {flight_obj.flight_number}")
            raise Exception("No gates available")

    def get_all_flights(self) -> List[Flight]:
        return self.flights

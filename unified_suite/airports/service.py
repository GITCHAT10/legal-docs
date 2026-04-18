from .models import Flight
from typing import List

class AirportService:
    def __init__(self):
        self.flights = []
        self.gates = [f"GATE_{i}" for i in range(1, 11)]

    def schedule_flight(self, flight: Flight):
        self.flights.append(flight)
        return flight

    def assign_gate(self, flight_number: str):
        for flight in self.flights:
            if flight.flight_number == flight_number:
                # Basic logic: assign the first available gate
                used_gates = [f.gate for f in self.flights if f.gate]
                for gate in self.gates:
                    if gate not in used_gates:
                        flight.gate = gate
                        return gate
        return None

    def get_all_flights(self) -> List[Flight]:
        return self.flights

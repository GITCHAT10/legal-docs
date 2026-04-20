from typing import List
from mnos.core.ai.models import PrestigeData, BookingData, AiDecision

class RoutingOptimizer:
    """
    Optimizes maritime and air routes based on demand and search patterns.
    """
    async def optimize(self, prestige_data: List[PrestigeData], booking_data: List[BookingData]) -> List[AiDecision]:
        decisions = []
        for p in prestige_data:
            if p.searches_last_24h > 100 and p.conversion_rate < 0.05:
                decisions.append(AiDecision(
                    module="routing_optimizer",
                    action="ADD_FREQUENCY",
                    reasoning=f"High search volume ({p.searches_last_24h}) but low conversion for {p.origin}->{p.destination}. Suggest adding more options.",
                    parameters={"route": f"{p.origin}-{p.destination}", "suggested_increase": 0.2},
                    confidence_score=0.85
                ))

        for b in booking_data:
            if b.total_capacity <= 0:
                print(f"Warning: Invalid total_capacity ({b.total_capacity}) for route {b.route_id}. Skipping.")
                continue
            occupancy = b.booked_seats / b.total_capacity
            if occupancy > 0.9:
                decisions.append(AiDecision(
                    module="routing_optimizer",
                    action="UPGRADE_VESSEL",
                    reasoning=f"High occupancy ({occupancy:.2%}) on route {b.route_id}. Current capacity fully utilized.",
                    parameters={"route_id": b.route_id, "required_capacity": int(b.total_capacity * 1.5)},
                    confidence_score=0.92
                ))

        return decisions

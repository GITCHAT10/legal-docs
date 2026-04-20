from typing import List
from mnos.core.ai.models import FinanceData, BookingData, AiDecision

class RevenueOptimizer:
    """
    Optimizes pricing and revenue strategies.
    """
    async def optimize(self, finance_data: List[FinanceData], booking_data: List[BookingData]) -> List[AiDecision]:
        decisions = []
        # Logic to adjust prices based on occupancy and financial performance
        for b in booking_data:
            occupancy = b.booked_seats / b.total_capacity
            if occupancy < 0.3 and b.avg_lead_time_days < 7:
                decisions.append(AiDecision(
                    module="revenue_optimizer",
                    action="APPLY_DISCOUNT",
                    reasoning=f"Low occupancy ({occupancy:.2%}) with short lead time for route {b.route_id}.",
                    parameters={"route_id": b.route_id, "discount_percentage": 0.15},
                    confidence_score=0.80
                ))
            elif occupancy > 0.8:
                decisions.append(AiDecision(
                    module="revenue_optimizer",
                    action="INCREASE_PRICE",
                    reasoning=f"High occupancy ({occupancy:.2%}) on route {b.route_id}. Optimizing for margin.",
                    parameters={"route_id": b.route_id, "increase_percentage": 0.10},
                    confidence_score=0.90
                ))
        return decisions

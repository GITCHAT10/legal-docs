from typing import List
from mnos.core.ai.models import PrestigeData, BookingData, AiDecision

class DemandPredictor:
    """
    Predicts future demand for routes and services.
    """
    async def predict(self, prestige_data: List[PrestigeData], booking_data: List[BookingData]) -> List[AiDecision]:
        decisions = []
        # Simple demand prediction logic based on search trends and booking velocity
        for p in prestige_data:
            if p.searches_last_24h > 500:
                decisions.append(AiDecision(
                    module="demand_predictor",
                    action="PREDICT_SURGE",
                    reasoning=f"Search surge detected for {p.origin}->{p.destination}.",
                    parameters={"route": f"{p.origin}-{p.destination}", "surge_factor": 1.5, "period": "NEXT_7_DAYS"},
                    confidence_score=0.88
                ))
        return decisions

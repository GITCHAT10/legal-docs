import numpy as np
from typing import Dict, Any

class HoneymoonRevenueForecaster:
    """High-AOV forecast model using Monte Carlo simulations."""

    def project_revenue(self, list_size: int, segment: str) -> Dict[str, Any]:
        params = {
            "eu_honeymoon": {
                "open_rate": 0.48,
                "click_rate": 0.24,
                "conversion_rate": 0.22,
                "aov_mvr": (125000, 35000) # Mean, std dev
            },
            "eu_honeymoon_luxury": {
                "open_rate": 0.54,
                "click_rate": 0.28,
                "conversion_rate": 0.18,
                "aov_mvr": (195000, 55000)
            }
        }

        p = params.get(segment, params["eu_honeymoon"])

        expected_bookings = list_size * p["open_rate"] * p["click_rate"] * p["conversion_rate"]

        # Monte Carlo simulation (100 iterations for sandbox speed)
        revenues = []
        mean, std = p["aov_mvr"]
        for _ in range(100):
            aov = max(0, np.random.normal(mean, std))
            revenues.append(expected_bookings * aov)

        return {
            "segment": segment,
            "expected_bookings": round(expected_bookings, 2),
            "projected_revenue_mean": round(float(np.mean(revenues)), 2),
            "projected_revenue_p90": round(float(np.percentile(revenues, 90)), 2)
        }

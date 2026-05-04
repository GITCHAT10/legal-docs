from typing import Dict, Any

def track_economic_metrics(total_value: float, margin: float):
    # Take rate = Margin / GMV
    take_rate = margin / total_value if total_value > 0 else 0

    return {
        "gmv": round(total_value, 2),
        "margin": round(margin, 2),
        "take_rate": round(take_rate, 4),
        "investor_ready": True
    }

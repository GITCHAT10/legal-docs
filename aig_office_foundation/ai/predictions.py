from typing import List, Dict, Any
import random

class PredictionEngine:
    """
    Machine Learning (ML): Learns from data patterns.
    Makes automated predictions based on historical office data.
    """
    def __init__(self, shadow_ledger):
        self.shadow_ledger = shadow_ledger
        self.trained_models = ["workload_forecast", "resource_allocation"]

    def predict_workload(self, actor_payload: dict, dataset: List[float], trace_id: str) -> Dict[str, Any]:
        """
        Simulates ML workload prediction based on input patterns.
        """
        if not dataset:
            raise ValueError("ML: Dataset required for prediction")

        avg = sum(dataset) / len(dataset)
        forecast = avg * 1.15 # Simulated upward trend

        prediction = {
            "model": "workload_forecast_v1",
            "prediction": forecast,
            "probability": 0.88,
            "status": "VALIDATED"
        }

        # Mandatory SHADOW audit for ML predictions
        self.shadow_ledger.commit("ml.prediction.generated",
                                   actor_payload["identity_id"],
                                   actor_payload["device_id"],
                                   trace_id,
                                   {"model": prediction["model"], "result": forecast})

        return prediction

    def detect_anomalies(self, actor_payload: dict, data_stream: List[float], trace_id: str) -> List[int]:
        """
        Unsupervised pattern recognition simulation.
        """
        anomalies = [i for i, val in enumerate(data_stream) if val > 100] # Simple threshold

        self.shadow_ledger.commit("ml.anomaly.detected",
                                   actor_payload["identity_id"],
                                   actor_payload["device_id"],
                                   trace_id,
                                   {"anomalies_found": len(anomalies)})
        return anomalies

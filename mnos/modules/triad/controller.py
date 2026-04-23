from typing import Dict, Any, List

class TriadController:
    """
    MIG Triad Readiness Controller.
    Enforces readiness scores for autonomous actions.
    """
    def __init__(self):
        self.threshold = 0.85

    def evaluate_readiness(self, system_id: str, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates readiness with explainability."""
        print(f"[Triad] Evaluating readiness for {system_id}...")

        # Simulated scoring
        score = telemetry.get("score", 0.90)
        confidence = 0.98

        ready = score >= self.threshold
        reason = "System healthy" if ready else "Sub-optimal metrics detected"

        return {
            "system_id": system_id,
            "readiness_score": score,
            "confidence": confidence,
            "is_ready": ready,
            "reason": reason,
            "reason_codes": ["HEALTH_OK"] if ready else ["ERR_LOW_SCORE"]
        }

triad_controller = TriadController()

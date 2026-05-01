import asyncio
import random
from typing import Dict
import uuid

class ORCAEngine:
    """
    ORCA (Operational Risk & Compliance Authority) Engine.
    Handles mission validation (Weather, NFZ) and operational metrics.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.metrics = []

    async def validate_mission(self, actor_ctx: dict, drone_data: dict, incident_data: dict) -> Dict:
        """
        Validates if a mission is allowed based on weather and geo-fencing.
        """
        await asyncio.sleep(random.uniform(0.1, 0.25))

        # Real-world: Connect to weather API and NFZ GeoJSON layers
        weather_ok = random.random() > 0.05
        nfz_clear = True # Mock NFZ check

        allowed = weather_ok and nfz_clear
        result = {
            "allowed": allowed,
            "reason": "CLEAR" if allowed else ("WEATHER_RESTRICTED" if not weather_ok else "NFZ_VIOLATION"),
            "risk_score": 0.1 if allowed else 0.9
        }

        self.metrics.append(result)

        # Record in shadow
        from mnos.shared.execution_guard import _sovereign_context
        token = str(uuid.uuid4())
        t = _sovereign_context.set({"token": token, "actor": {"identity_id": "ORCA"}})
        try:
            self.shadow.commit("orca.validation_performed", actor_ctx.get("identity_id", "UNKNOWN"), result)
        finally:
            _sovereign_context.reset(t)

        return result

    def get_metrics(self) -> Dict:
        """
        Returns aggregated mission metrics with null-safety for offline_sync payloads.
        """
        # NULL-SAFE .get() access as per MNOS memory instructions
        success_count = len([m for m in self.metrics if m.get("allowed")])
        total_count = len(self.metrics)

        return {
            "total_validations": total_count,
            "success_rate": (success_count / total_count) if total_count > 0 else 1.0,
            "status": "OPERATIONAL"
        }

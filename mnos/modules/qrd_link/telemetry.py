import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger("QRD_TELEMETRY")

import time

class TelemetryBridge:
    """
    Telemetry Bridge: Streams drone data to MNOS MIG SHIELD core.
    In production, this connects to Kafka/Redis.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.active_streams: List[asyncio.Queue] = []
        self.heartbeats: Dict[str, float] = {}

    def is_active(self, drone_id: str, timeout: float = 3.0) -> bool:
        """
        Check if drone telemetry is active within the timeout window.
        """
        last_seen = self.heartbeats.get(drone_id, 0)
        return (time.time() - last_seen) < timeout

    async def broadcast_telemetry(self, drone_id: str, data: Dict[str, Any]):
        """
        Broadcasting telemetry data and logging significant changes to SHADOW.
        """
        self.heartbeats[drone_id] = time.time()

        # Audit high-frequency telemetry if needed, or just thresholded
        if data.get("battery", 100) < 20:
            # Bypass guard for emergency telemetry alert
            from mnos.shared.execution_guard import _sovereign_context
            t = _sovereign_context.set({"token": "TELEMETRY_ALERT", "actor": {"identity_id": "SYSTEM"}})
            try:
                self.shadow.commit("telemetry.alert.low_battery", drone_id, data)
            finally:
                _sovereign_context.reset(t)

        # Stream to any listening UI clients
        for queue in self.active_streams:
            await queue.put({"drone_id": drone_id, "telemetry": data})

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_streams.append(queue)
        return queue

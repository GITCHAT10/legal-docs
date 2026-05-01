import time
import logging
from typing import Dict, Any

logger = logging.getLogger("UT_AEROMARINE_WATCHDOG")

class TelemetryWatchdog:
    """
    UT AEROMARINE Telemetry Watchdog.
    Monitors hybrid air-sea assets and fails closed on connection/safety breach.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.heartbeats: Dict[str, float] = {}

    def update_heartbeat(self, device_id: str):
        self.heartbeats[device_id] = time.time()

    def check_safety(self, device_id: str, telemetry: dict) -> bool:
        """
        Evaluate safety parameters. Fail closed on breach.
        """
        # 1. Heartbeat check (3s timeout)
        last_seen = self.heartbeats.get(device_id, 0)
        if (time.time() - last_seen) > 3.0:
            logger.error(f"WATCHDOG: Heartbeat lost for {device_id}")
            return False

        # 2. Battery threshold (25%)
        if telemetry.get("battery", 100) < 25:
            logger.error(f"WATCHDOG: Low battery for {device_id}: {telemetry.get('battery')}%")
            return False

        # 3. Geofence check
        if not telemetry.get("geofence_ok", True):
            logger.error(f"WATCHDOG: Geofence breach for {device_id}")
            return False

        # 4. GPS Lock
        if not telemetry.get("gps_lock", True):
            logger.error(f"WATCHDOG: GPS lock lost for {device_id}")
            return False

        return True

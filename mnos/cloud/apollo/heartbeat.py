import time
from typing import Dict, Any
from datetime import datetime, UTC

class HeartbeatMonitor:
    """
    AIR CLOUD: Node Heartbeat Monitor.
    Tracks health status and latency of cloud nodes for failover detection.
    """
    def __init__(self, threshold_seconds: int = 30):
        self.node_status = {} # node_id -> {last_seen, status, latency_ms}
        self.threshold = threshold_seconds

    def record_heartbeat(self, node_id: str, latency_ms: int):
        self.node_status[node_id] = {
            "last_seen": time.time(),
            "status": "ONLINE",
            "latency_ms": latency_ms
        }

    def get_node_health(self, node_id: str) -> str:
        status = self.node_status.get(node_id)
        if not status:
            return "UNKNOWN"

        if time.time() - status["last_seen"] > self.threshold:
            status["status"] = "OFFLINE"
            return "OFFLINE"

        return status["status"]

    def list_unhealthy_nodes(self) -> list:
        return [nid for nid, stat in self.node_status.items()
                if time.time() - stat["last_seen"] > self.threshold]

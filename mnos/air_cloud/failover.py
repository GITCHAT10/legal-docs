from enum import Enum
from typing import List

class FailoverPath(Enum):
    FIBER = "PRIMARY_DHIRAAGU_OOREDOO"
    SATELLITE_STARLINK = "SECONDARY_STARLINK"
    SATELLITE_KACIFIC = "TERTIARY_KACIFIC"
    OFFLINE_WAL = "FALLBACK_OFFLINE_QUEUE"

class CloudFailoverEngine:
    """
    AIR CLOUD: Network & Sync Failover Logic.
    Ensures zero data loss during connectivity drops in the Maldives.
    """
    def __init__(self):
        self.current_status = FailoverPath.FIBER

    def detect_and_route(self, link_latency_ms: int) -> FailoverPath:
        if link_latency_ms < 50:
            self.current_status = FailoverPath.FIBER
        elif link_latency_ms < 150:
            self.current_status = FailoverPath.SATELLITE_STARLINK
        elif link_latency_ms < 500:
            self.current_status = FailoverPath.SATELLITE_KACIFIC
        else:
            self.current_status = FailoverPath.OFFLINE_WAL

        return self.current_status

    def get_sync_strategy(self) -> str:
        if self.current_status == FailoverPath.OFFLINE_WAL:
            return "WRITE_AHEAD_LOG_LOCAL"
        return "REALTIME_CORE_COMMIT"

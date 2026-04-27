from typing import Dict, Any
import time

class FailoverOrchestrator:
    """
    APOLLO: Failover Promotion Logic.
    Handles node promotion after heartbeat loss with SHADOW verification.
    """
    def __init__(self, heartbeat_monitor, shadow_ledger, orca):
        self.heartbeat = heartbeat_monitor
        self.shadow = shadow_ledger
        self.orca = orca
        self.is_promoted = False
        self.last_failover_event = {}

    def trigger_failover(self, node_id: str, remote_shadow_hash: str):
        """
        Promotes the standby node to ACTIVE if SHADOW hashes match.
        """
        # Rule: no SHADOW match = block promotion
        local_hash = self.shadow.chain[-1]["hash"] if self.shadow.chain else self.shadow.genesis_hash

        if remote_shadow_hash != local_hash:
             raise PermissionError(f"FAIL CLOSED: Promotion blocked for {node_id} - SHADOW hash mismatch")

        # Execute promotion
        self.is_promoted = True
        self.last_failover_event = {
            "node_id": node_id,
            "promotion_time": time.time(),
            "status": "ACTIVE_FAILOVER"
        }

        # Update ORCA Visibility
        self.orca.record_failover(self.last_failover_event)

        return self.last_failover_event

    def get_failover_status(self) -> dict:
        return {
            "is_promoted": self.is_promoted,
            "last_event": self.last_failover_event
        }

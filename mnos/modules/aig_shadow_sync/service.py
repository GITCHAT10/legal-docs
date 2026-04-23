from typing import Dict, Any, List
import datetime
from mnos.modules.aig_shadow.service import aig_shadow

class SyncAgent:
    """
    Shadow-Sync Agent (Core Service):
    Listens to DB changes (CDC) and applies them to the local mirror.
    Ensures L1 data (identity, finance, transactions) is prioritized.
    """
    def __init__(self):
        self.local_queue: List[Dict[str, Any]] = []
        self.priority_layers = {
            "L1": ["identity", "finance", "bookings", "transactions"],
            "L2": ["documents", "operations"]
        }

    def process_cdc_event(self, table: str, operation: str, data: Dict[str, Any]):
        """
        Processes a Change Data Capture event from the cloud.
        NEXUS-SKYI-APOLLO: Enforces fail-closed sync integrity.
        """
        try:
            layer = self._get_data_layer(table)

            event = {
                "table": table,
                "operation": operation,
                "data": data,
                "layer": layer,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            # Apply to local mirror (Simulation)
            from mnos.modules.aig_shadow_sync.db_mirror import db_mirror
            db_mirror.apply_change(event)

            # APOLLO: Deferred Commit Logic (Simulation)
            # In a real edge node, this would queue the commit for the next heartbeat

            return event
        except Exception as e:
            # FAIL-CLOSED: If sync fails, the edge node must enter emergency mode
            print(f"[AIGShadowSync] FAIL-CLOSED: Sync disruption detected: {str(e)}")
            raise RuntimeError("Sovereign Sync Failure: System Halt mandated.") from e

    def _get_data_layer(self, table: str) -> str:
        for layer, tables in self.priority_layers.items():
            if table in tables:
                return layer
        return "L3"

    def queue_local_change(self, change: Dict[str, Any]):
        """Queues changes made locally during outage for later reconciliation."""
        self.local_queue.append(change)

sync_agent = SyncAgent()

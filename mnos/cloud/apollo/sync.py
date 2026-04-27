from typing import Dict, Any
import time

class ApolloSyncService:
    """
    APOLLO Sync Engine.
    Synchronizes Edge WAL queue to the Core SHADOW ledger.
    """
    def __init__(self, edge_node, core_shadow):
        self.edge = edge_node
        self.shadow = core_shadow

    def sync_node(self) -> Dict[str, Any]:
        pending = self.edge.get_pending_sync()
        if not pending:
            return {"status": "IDLE", "synced": 0}

        synced_count = 0
        for tx in pending:
            # Commit to core shadow with original metadata
            self.shadow.commit(
                event_type=tx.get("event_type", "edge.sync"),
                actor_id=tx.get("actor_id", "EDGE_NODE"),
                payload={**tx.get("payload", {}), "synced_at": time.time()}
            )
            synced_count += 1

        self.edge.clear_wal()
        return {"status": "SUCCESS", "synced": synced_count}

from typing import Dict, Any, List
import logging

class EdgeNode:
    """
    N-DEOS Edge Architecture.
    Supports offline-first operation and local execution fallback.
    """
    def __init__(self, node_id: str, type: str):
        self.node_id = node_id
        self.type = type
        self.queue: List[Dict[str, Any]] = []
        self.is_online = True

    def execute(self, action: str, payload: Dict[str, Any]):
        if not self.is_online:
            logging.warning(f"NODE {self.node_id} OFFLINE: Queueing {action}")
            self.queue.append({"action": action, "payload": payload})
            return {"status": "queued"}

        logging.info(f"NODE {self.node_id} EXECUTING: {action}")
        return {"status": "executed", "node": self.node_id}

    def sync(self):
        if not self.is_online:
            return False
        sync_count = len(self.queue)
        self.queue = []
        return {"synced": sync_count}

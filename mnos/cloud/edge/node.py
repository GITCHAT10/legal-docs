from typing import Dict, List, Any
import json
import os

class EdgeNode:
    """
    SALA Edge Node.
    Handles local state and offline WAL (Write-Ahead Log) queue.
    """
    def __init__(self, node_id: str, storage_path: str = "mnos/cloud/edge/storage"):
        self.node_id = node_id
        self.storage_path = storage_path
        self.wal_file = os.path.join(storage_path, "wal.jsonl")
        os.makedirs(storage_path, exist_ok=True)
        self.online = True

    def toggle_online(self, status: bool):
        self.online = status

    def record_transaction(self, tx: Dict[str, Any]):
        if not self.online:
            with open(self.wal_file, "a") as f:
                f.write(json.dumps(tx) + "\n")
            return {"status": "QUEUED_OFFLINE"}
        return {"status": "PROCESSED_ONLINE"}

    def get_pending_sync(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.wal_file):
            return []
        pending = []
        with open(self.wal_file, "r") as f:
            for line in f:
                pending.append(json.loads(line.strip()))
        return pending

    def clear_wal(self):
        if os.path.exists(self.wal_file):
            os.remove(self.wal_file)

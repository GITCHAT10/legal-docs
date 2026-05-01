from typing import Dict, List, Any
import json
import os

class EdgeNode:
    """
    SALA Edge Node.
    Handles local state and offline WAL (Write-Ahead Log) queue.
    Ensures WAL is not cleared before confirmed core commit.
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
        """
        Records transaction to WAL if offline.
        Enforces Trace ID and Idempotency key existence.
        """
        payload = tx.get("payload", {})
        if not tx.get("trace_id"):
            raise ValueError("TRACE_ID_REQUIRED for WAL entry.")
        if not payload.get("idempotency_key"):
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED for WAL entry.")

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

    def remove_synced_entries(self, entries: List[Dict[str, Any]]):
        """
        BLOCK_WAL_CLEAR_BEFORE_DB_COMMIT:
        Only removes entries from WAL that have been successfully synced.
        """
        if not os.path.exists(self.wal_file):
            return

        synced_ikeys = {e.get("payload", {}).get("idempotency_key") for e in entries}
        remaining = []
        with open(self.wal_file, "r") as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get("payload", {}).get("idempotency_key") not in synced_ikeys:
                    remaining.append(entry)

        with open(self.wal_file, "w") as f:
            for entry in remaining:
                f.write(json.dumps(entry) + "\n")

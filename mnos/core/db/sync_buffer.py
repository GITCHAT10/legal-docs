from typing import Dict, Any, List
from sqlalchemy.orm import Session
from mnos.modules.shadow import service as shadow_service
import json

class SyncBuffer:
    """
    Sovereign Execution: Offline Transaction -> Sync -> SHADOW Commit.
    Mocks a buffer that holds transactions before they are cryptographically sealed.
    """
    def __init__(self):
        self._buffer: List[Dict[str, Any]] = []

    def queue_transaction(self, trace_id: str, payload: Dict[str, Any]):
        self._buffer.append({
            "trace_id": trace_id,
            "payload": payload,
            "offline_timestamp": shadow_service.models.datetime.utcnow().isoformat()
        })

    def process_sync(self, db: Session) -> List[str]:
        """Seal all buffered transactions in SHADOW."""
        sealed_traces = []
        for tx in self._buffer:
            shadow_service.commit_evidence(db, tx["trace_id"], {
                "action": "OFFLINE_SYNC",
                "original_payload": tx["payload"],
                "offline_at": tx["offline_timestamp"]
            })
            sealed_traces.append(tx["trace_id"])

        self._buffer.clear()
        return sealed_traces

sync_buffer = SyncBuffer()

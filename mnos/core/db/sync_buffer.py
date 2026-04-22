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
        try:
            for tx in self._buffer:
                # Use hardened SHADOW service
                from mnos.modules.shadow.service import shadow
                shadow.commit("OFFLINE_SYNC", {
                    "original_payload": tx["payload"],
                    "offline_at": tx["offline_timestamp"],
                    "trace_id": tx["trace_id"]
                })
                sealed_traces.append(tx["trace_id"])

            # Directive: Ensure db.commit() is called BEFORE self._buffer.clear()
            # Our 'Sovereign' promise means we never lose a transaction.
            db.commit()
            self._buffer.clear()
            return sealed_traces
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Sync Buffer: Fail-Closed on commit failure. {str(e)}")

sync_buffer = SyncBuffer()

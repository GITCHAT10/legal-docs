from typing import Dict, Any, List
from sqlalchemy.orm import Session
from mnos.modules.shadow import service as shadow_service
import json
import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class SyncBuffer:
    """
    Sovereign Execution: Offline Transaction -> Sync -> SHADOW Commit.
    Durable Sync: flush -> commit -> THEN clear.
    """
    def __init__(self, buffer_size: int = 100):
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_size = buffer_size

    def queue_transaction(self, trace_id: str, payload: Dict[str, Any]):
        self._buffer.append({
            "trace_id": trace_id,
            "payload": payload,
            "offline_timestamp": datetime.now(UTC).isoformat()
        })

        # In a real system, we might trigger process_sync if buffer is full

    def process_sync(self, db: Session) -> List[str]:
        """
        Safely persist buffered transactions:
        1. Write to DB (flush)
        2. Commit transaction (durability guarantee)
        3. THEN clear buffer (no data loss)
        """
        if not self._buffer:
            return []

        sealed_traces = []
        try:
            for tx in self._buffer:
                # 1. Commit Evidence to SHADOW (This adds to DB session)
                shadow_service.commit_evidence(db, tx["trace_id"], {
                    "action": "OFFLINE_SYNC",
                    "original_payload": tx["payload"],
                    "offline_at": tx["offline_timestamp"],
                    "compliance_tags": ["BUBBLE-SYNC"]
                })
                sealed_traces.append(tx["trace_id"])

            # 2. Flush to DB (but don't clear memory yet)
            db.flush()

            # 3. COMMIT DB (AUTHORITATIVE DURABILITY)
            db.commit()

            # 4. Clear Buffer only AFTER commit succeeds
            self._buffer.clear()
            logger.info(f"SyncBuffer: {len(sealed_traces)} entries sealed and cleared.")
            return sealed_traces
        except Exception as e:
            db.rollback()
            logger.error(f"SyncBuffer failure: {e}. Buffer preserved for retry.")
            raise e

sync_buffer = SyncBuffer()

import json
import hashlib
import uuid
from typing import Dict, Any, List
from datetime import datetime

class ChronosEventStore:
    """
    MIG CHRONOS: Temporal Event Store.
    Hardened for provable replay and immutability.
    """
    def __init__(self):
        self.streams: Dict[str, List[Dict[str, Any]]] = {}

    def append(self, stream_id: str, event_type: str, payload: Dict[str, Any]):
        """Appends and hashes event to the temporal stream."""
        if stream_id not in self.streams:
            self.streams[stream_id] = []

        prev_hash = self.streams[stream_id][-1]["hash"] if self.streams[stream_id] else "0"*64

        event = {
            "event_id": str(uuid.uuid4()),
            "stream_id": stream_id,
            "event_type": event_type,
            "payload": payload,
            "event_time_ns": datetime.now().timestamp() * 1e9,
            "previous_hash": prev_hash
        }

        event["hash"] = self._calculate_hash(event)
        self.streams[stream_id].append(event)
        return event

    def _calculate_hash(self, event: Dict[str, Any]) -> str:
        """Deterministic canonical hashing."""
        data = {
            "event_id": event["event_id"],
            "stream_id": event["stream_id"],
            "event_type": event["event_type"],
            "payload": event["payload"],
            "event_time_ns": event["event_time_ns"],
            "previous_hash": event["previous_hash"]
        }
        block_string = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        return hashlib.sha256(block_string).hexdigest()

chronos_store = ChronosEventStore()

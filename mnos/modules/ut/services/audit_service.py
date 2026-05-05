import hashlib
from typing import Dict, List

class UTAuditService:
    def __init__(self, shadow):
        self.shadow = shadow
        self.event_chain = []

    def log_event(self, trace_id: str, event_type: str, actor_id: str, payload: Dict):
        """
        Logs a forensic event to SHADOW with a local hash chain.
        """
        previous_hash = self.event_chain[-1]["hash"] if self.event_chain else "0" * 64

        raw_data = f"{trace_id}-{event_type}-{actor_id}-{payload}-{previous_hash}"
        event_hash = hashlib.sha256(raw_data.encode()).hexdigest()

        event = {
            "trace_id": trace_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "payload": payload,
            "hash": event_hash,
            "previous_hash": previous_hash
        }

        self.event_chain.append(event)
        self.shadow.commit(f"ut.audit.{event_type}", actor_id, event)
        return event

    def verify_chain(self) -> bool:
        """
        Verifies the integrity of the UT event chain.
        """
        for i in range(1, len(self.event_chain)):
            if self.event_chain[i]["previous_hash"] != self.event_chain[i-1]["hash"]:
                return False
        return True

    def export_forensics(self, trace_id: str) -> List[Dict]:
        """
        Exports all events for a specific trace_id.
        """
        return [e for e in self.event_chain if e["trace_id"] == trace_id]

import hashlib
import json
from datetime import datetime, UTC

class ShadowLedger:
    """
    SHADOW Immutable Ledger
    Implements SHA-256 hash chaining for audit traceability.
    """
    def __init__(self):
        self.ledger = []
        self.last_hash = "0" * 64

    def commit(self, entry_id: str, event_type: str, payload: dict):
        timestamp = datetime.now(UTC).isoformat()

        # SHA-256 hash chaining: prev_hash + event_type + payload + entry_id
        content = f"{self.last_hash}{event_type}{json.dumps(payload, sort_keys=True)}{entry_id}{timestamp}"
        current_hash = hashlib.sha256(content.encode()).hexdigest()

        entry = {
            "entry_id": entry_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": timestamp,
            "previous_hash": self.last_hash,
            "hash": current_hash
        }

        self.ledger.append(entry)
        self.last_hash = current_hash
        return current_hash

    def verify_integrity(self):
        prev_hash = "0" * 64
        for entry in self.ledger:
            if entry["previous_hash"] != prev_hash:
                return False

            content = f"{entry['previous_hash']}{entry['event_type']}{json.dumps(entry['payload'], sort_keys=True)}{entry['entry_id']}{entry['timestamp']}"
            expected_hash = hashlib.sha256(content.encode()).hexdigest()

            if entry["hash"] != expected_hash:
                return False

            prev_hash = entry["hash"]
        return True

shadow = ShadowLedger()

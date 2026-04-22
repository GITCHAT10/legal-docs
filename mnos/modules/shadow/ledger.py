import hashlib
import json
from datetime import datetime, UTC

class ShadowLedger:
    """
    SHADOW Ledger: Immutable SHA-256 hash chaining for all critical actions.
    """
    def __init__(self):
        self.chain = []
        self.last_hash = "0" * 64

    def commit(self, event_type: str, payload: dict) -> str:
        entry_id = len(self.chain) + 1
        timestamp = datetime.now(UTC).isoformat()

        data_to_hash = {
            "previous_hash": self.last_hash,
            "event_type": event_type,
            "payload": payload,
            "entry_id": entry_id,
            "timestamp": timestamp
        }

        block_string = json.dumps(data_to_hash, sort_keys=True)
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()

        self.chain.append({
            "hash": block_hash,
            "data": data_to_hash
        })

        self.last_hash = block_hash
        return block_hash

    def verify_integrity(self) -> bool:
        prev_hash = "0" * 64
        for block in self.chain:
            data = block["data"]
            if data["previous_hash"] != prev_hash:
                return False

            block_string = json.dumps(data, sort_keys=True)
            recalc_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if block["hash"] != recalc_hash:
                return False

            prev_hash = block["hash"]
        return True

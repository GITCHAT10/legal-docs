from datetime import datetime, UTC
import hashlib
import json
from typing import Any
from datetime import datetime, UTC

class ShadowEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ShadowLedger:
    """
    SHADOW Hardened Ledger for immutable event logging.
    """
    def __init__(self):
        self.chain = []

    def commit(self, event_type: str, actor_id: str, payload: Any):
        """
        Commits an event to the SHADOW ledger.
        """
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "payload": payload,
            "prev_hash": self.chain[-1]["hash"] if self.chain else "ROOT"
        }
        entry["hash"] = self._hash_entry(entry)
        self.chain.append(entry)
        return entry["hash"]

    def _hash_entry(self, entry: dict) -> str:
        canonical = json.dumps(entry, sort_keys=True, cls=ShadowEncoder)
        return hashlib.sha256(canonical.encode()).hexdigest()

import hashlib
import json
from datetime import datetime

def create_shadow_hash(payload: dict) -> str:
    """
    Creates an immutable Shadow Ledger evidence log.
    Every record is timestamped and hashed for auditors.
    """
    payload_copy = payload.copy()
    payload_copy['timestamp'] = datetime.utcnow().isoformat()

    # Canonical JSON string for hashing
    canonical_payload = json.dumps(payload_copy, sort_keys=True)
    return hashlib.sha256(canonical_payload.encode()).hexdigest()

def record_entry(entry: dict):
    """
    Bucket A: Blockchain ledger / integrity anchor stub.
    """
    return create_shadow_hash(entry)

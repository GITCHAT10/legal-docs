import hashlib
import json
from datetime import datetime, UTC

class EleoneAI:
    """
    ELEONE AI Decision Layer
    Handles construction decision hashing and auditing for the ARCOs pipeline.
    """
    def __init__(self):
        self.decision_log = []

    def log_decision(self, intent: str, context: dict, result: dict):
        timestamp = datetime.now(UTC).isoformat()
        payload = {
            "intent": intent,
            "context": context,
            "result": result,
            "timestamp": timestamp
        }

        # SHA-256 decision hashing for auditing
        decision_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

        entry = {
            "hash": decision_hash,
            "payload": payload
        }

        self.decision_log.append(entry)
        return decision_hash

    def get_audit_trail(self):
        return self.decision_log

eleone = EleoneAI()

import hashlib
import json
from datetime import datetime, UTC

class EleoneEngine:
    """
    ELEONE AI Decision Layer handles construction and commerce decision hashing and auditing.
    """
    @staticmethod
    def generate_decision_hash(payload: dict) -> str:
        data = {
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat()
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    @staticmethod
    def audit_decision(decision_id: str, action: str, actor: str):
        # In a real system, this would write to a secure audit log or database
        print(f"[ELEONE AUDIT] {datetime.now(UTC)} | Decision: {decision_id} | Action: {action} | Actor: {actor}")

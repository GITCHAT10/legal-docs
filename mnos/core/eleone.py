import hashlib
import json
from datetime import datetime, UTC
import uuid

class EleoneEngine:
    """
    ELEONE AI Decision Layer handles construction and commerce decision hashing and auditing.
    """
    def __init__(self, shadow=None):
        self.shadow = shadow

    @staticmethod
    def generate_decision_hash(payload: dict) -> str:
        data = {
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat()
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def audit_decision(self, decision_id: str, action: str, actor: str):
        # In a real system, this would write to a secure audit log or database
        print(f"[ELEONE AUDIT] {datetime.now(UTC)} | Decision: {decision_id} | Action: {action} | Actor: {actor}")
        if self.shadow:
            from mnos.shared.execution_guard import _sovereign_context
            token = str(uuid.uuid4())
            t = _sovereign_context.set({"token": token, "actor": {"identity_id": "ELEONE"}})
            try:
                self.shadow.commit("eleone.decision_audited", actor, {
                    "decision_id": decision_id,
                    "action": action,
                    "actor_id": actor
                })
            finally:
                _sovereign_context.reset(t)

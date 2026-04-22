from typing import Dict, Any
import hashlib
import json

class EleoneEngine:
    """
    ELEONE: MNOS AI Decision & Context Layer.
    Proposes and hashes construction decisions before ledger commit.
    """
    def __init__(self, shadow_logger):
        self.shadow = shadow_logger

    def propose_decision(self, trace_id: str, decision_type: str, payload: Dict[str, Any]) -> str:
        """
        Creates a hashed AI decision proposal.
        """
        decision_hash = hashlib.sha256(json.dumps(payload).encode()).hexdigest()

        proposal = {
            "trace_id": trace_id,
            "type": decision_type,
            "hash": decision_hash,
            "status": "PROPOSED",
            "advisory_only": False
        }

        self.shadow.log("AI_DECISION_PROPOSED", proposal)
        return decision_hash

    def approve_decision(self, decision_hash: str):
        self.shadow.log("AI_DECISION_APPROVED", {"hash": decision_hash})

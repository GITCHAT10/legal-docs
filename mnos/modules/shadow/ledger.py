import hashlib
import json
import uuid
import copy
from datetime import datetime, UTC
from mnos.shared.auth_context import is_sovereign_authorized

class ShadowLedger:
    def __init__(self):
        self.chain = []
        self.genesis_hash = "0" * 64

    def commit(self, event_type: str, actor_id: str, payload: dict) -> str:
        if not is_sovereign_authorized() and actor_id != "SYSTEM":
             raise PermissionError("FAIL CLOSED: Unauthorized direct write to SHADOW Ledger blocked.")

        if "trace_id" not in payload:
             payload["trace_id"] = str(uuid.uuid4().hex[:8])

        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash
        safe_payload = copy.deepcopy(payload)

        block = {
            "index": len(self.chain),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "payload": safe_payload,
            "prev_hash": prev_hash,
            "signature": f"SIG-{uuid.uuid4().hex[:8]}"
        }

        block["hash"] = self._calculate_hash(block)
        self.chain.append(block)
        return block["hash"]

    def _calculate_hash(self, block: dict) -> str:
        temp = copy.deepcopy(block)
        if "hash" in temp:
            temp.pop("hash")
        block_string = json.dumps(temp, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity(self) -> bool:
        if not self.chain:
            return True
        for i in range(len(self.chain)):
            current = self.chain[i]
            if self._calculate_hash(current) != current["hash"]:
                return False
            if i == 0:
                if current["prev_hash"] != self.genesis_hash:
                    return False
            else:
                previous = self.chain[i-1]
                if current["prev_hash"] != previous["hash"]:
                    return False
        return True

    def export_audit_proof(self):
        return {
            "version": "MNOS-SHADOW-1.0",
            "chain_length": len(self.chain),
            "root_hash": self.chain[-1]["hash"] if self.chain else None,
            "evidence": self.chain
        }

    def reset_state(self):
        self.chain = []

import hashlib
import json
import uuid
import copy
from datetime import datetime, UTC

class ShadowLedger:
    """
    SHADOW Hardened Ledger: Forensic-grade immutable audit chain.
    prev_hash -> data -> current_hash
    """
    def __init__(self):
        self.chain = []
        self.genesis_hash = "0" * 64

    def commit(self, event_type: str, actor_id: str, payload: dict) -> str:
        # SECURITY: Enforcement of ExecutionGuard Authority
        from mnos.shared.execution_guard import ExecutionGuard
        if not ExecutionGuard.is_authorized():
             raise PermissionError("FAIL CLOSED: Unauthorized direct write to SHADOW Ledger blocked.")

        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash

        # Deepcopy payload to prevent retro-active changes breaking the hash
        safe_payload = copy.deepcopy(payload)

        block = {
            "index": len(self.chain),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "payload": safe_payload,
            "prev_hash": prev_hash,
            "signature": self._sign_event(safe_payload)
        }

        block["hash"] = self._calculate_hash(block)
        self.chain.append(block)
        return block["hash"]

    def _calculate_hash(self, block: dict) -> str:
        # Use deepcopy here too just in case
        temp = copy.deepcopy(block)
        if "hash" in temp:
            temp.pop("hash")
        block_string = json.dumps(temp, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def _sign_event(self, payload: dict) -> str:
        # Placeholder for cryptographic signing
        return f"SIG-{uuid.uuid4().hex[:8]}"

    def verify_integrity(self) -> bool:
        if not self.chain:
            return True

        for i in range(len(self.chain)):
            current = self.chain[i]

            # Verify self-hash
            if self._calculate_hash(current) != current["hash"]:
                return False

            # Verify linkage
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

    def get_block(self, index: int) -> dict:
        if index < 0 or index >= len(self.chain):
            raise IndexError("Block index out of range")
        return self.chain[index]

import hashlib
import json
import copy
from datetime import datetime, UTC
import uuid

class ShadowLedger:
    """
    SHADOW Hardened Ledger v1.1: Forensic-grade immutable audit chain.
    """
    def __init__(self):
        self.chain = []
        self.genesis_hash = "0" * 64

    def commit(self, event: dict) -> str:
        # SECURITY: Gateway-mediated writes only
        # In this implementation, we assume the caller is authorized if they pass a valid event

        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash

        # Deepcopy to prevent retro-active changes
        safe_event = copy.deepcopy(event)

        # Ensure timestamp is present
        if "timestamp" not in safe_event:
            safe_event["timestamp"] = datetime.now(UTC).isoformat()

        block = {
            "index": len(self.chain),
            "event": safe_event,
            "prev_hash": prev_hash,
            "timestamp": safe_event["timestamp"]
        }

        block["hash"] = self._calculate_hash(block)
        self.chain.append(block)
        return block["hash"]

    def _calculate_hash(self, block: dict) -> str:
        temp = copy.deepcopy(block)
        if "hash" in temp:
            temp.pop("hash")

        # Requirement: Timestamp, previous_hash, payload_hash, actor.id, tenant.tin must be included.
        # These are all part of 'block' or 'block.event'.

        block_string = json.dumps(temp, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

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

import hashlib
import json
import os
from datetime import datetime, UTC
from typing import Dict, Any, List

class ShadowSovereignLedger:
    """
    SHADOW Sovereign Ledger for SALA Node.
    Immutable, hash-chained audit trails.
    Persisted to disk (WORM-style simulation).
    """
    def __init__(self, storage_path: str = "mnos/core/shadow/storage", genesis_hash: str = "0" * 64):
        self.chain: List[Dict[str, Any]] = []
        self.genesis_hash = genesis_hash
        self.storage_path = storage_path
        self.ledger_file = os.path.join(storage_path, "shadow_ledger.jsonl")
        os.makedirs(storage_path, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.ledger_file):
            with open(self.ledger_file, "r") as f:
                for line in f:
                    self.chain.append(json.loads(line.strip()))

    def _persist_block(self, block: Dict[str, Any]):
        with open(self.ledger_file, "a") as f:
            f.write(json.dumps(block) + "\n")

    def commit(self, event_type: str, actor_id: str, payload: Dict[str, Any]) -> str:
        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash

        block = {
            "index": len(self.chain),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "payload": payload,
            "prev_hash": prev_hash
        }

        block["hash"] = self._calculate_hash(block)
        self.chain.append(block)
        self._persist_block(block)
        return block["hash"]

    def _calculate_hash(self, block: Dict[str, Any]) -> str:
        b = block.copy()
        b.pop("hash", None)
        block_string = json.dumps(b, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity(self) -> bool:
        for i in range(len(self.chain)):
            current = self.chain[i]
            if self._calculate_hash(current) != current["hash"]:
                return False
            if i > 0:
                if current["prev_hash"] != self.chain[i-1]["hash"]:
                    return False
            elif current["prev_hash"] != self.genesis_hash:
                return False
        return True

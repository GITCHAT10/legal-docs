import hashlib
import json
import os
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

class ShadowSovereignLedger:
    """
    SHADOW Sovereign Ledger for SALA Node.
    Immutable, hash-chained audit trails.
    Persisted to disk (WORM-style simulation).
    Enforces Trace ID and Idempotency.
    """
    def __init__(self, storage_path: str = "mnos/core/shadow/storage", genesis_hash: str = "0" * 64):
        self.chain: List[Dict[str, Any]] = []
        self.genesis_hash = genesis_hash
        self.storage_path = storage_path
        self.ledger_file = os.path.join(storage_path, "shadow_ledger.jsonl")
        self.idempotency_keys = set()
        os.makedirs(storage_path, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.ledger_file):
            with open(self.ledger_file, "r") as f:
                for line in f:
                    block = json.loads(line.strip())
                    self.chain.append(block)
                    ikey = block.get("payload", {}).get("idempotency_key")
                    if ikey:
                        self.idempotency_keys.add(ikey)

    def _persist_block(self, block: Dict[str, Any]):
        with open(self.ledger_file, "a") as f:
            f.write(json.dumps(block) + "\n")

    def commit(self, event_type: str, actor_id: str, payload: Dict[str, Any], trace_id: str = None) -> str:
        """
        Commits a new block to the SHADOW ledger.
        Enforces TRACE_ID and IDEMPOTENCY_KEY (Replay Protection).
        """
        if not trace_id:
             # For legacy compatibility during migration, we can generate one,
             # but production SALA paths should always provide it.
             trace_id = f"AUTO-{uuid.uuid4().hex[:6]}"

        # Replay Protection
        ikey = payload.get("idempotency_key")
        if ikey and ikey in self.idempotency_keys:
            raise ValueError(f"REPLAY REJECTION: Duplicate idempotency_key {ikey} detected.")

        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash

        block = {
            "index": len(self.chain),
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "trace_id": trace_id,
            "payload": payload,
            "prev_hash": prev_hash
        }

        block["hash"] = self._calculate_hash(block)
        self.chain.append(block)
        if ikey:
            self.idempotency_keys.add(ikey)
        self._persist_block(block)
        return block["hash"]

    def _calculate_hash(self, block: Dict[str, Any]) -> str:
        b = block.copy()
        b.pop("hash", None)
        block_string = json.dumps(b, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity(self) -> bool:
        """
        Validates the entire SHADOW hash chain continuity and self-integrity.
        """
        if not self.chain:
            return True

        for i in range(len(self.chain)):
            current = self.chain[i]

            # 1. Self-Hash Check
            if self._calculate_hash(current) != current["hash"]:
                return False

            # 2. Index Continuity Check
            if current["index"] != i:
                return False

            # 3. Chain Linkage Check
            if i == 0:
                if current["prev_hash"] != self.genesis_hash:
                    return False
            else:
                previous = self.chain[i-1]
                if current["prev_hash"] != previous["hash"]:
                    return False
        return True

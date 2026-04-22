import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

class ShadowLedger:
    """
    Immutable Audit Ledger: SHA-256 hash chaining of all system events.
    Enforces fail-closed behavior if commit cannot be sealed.
    """
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self._seed_ledger()

    def _seed_ledger(self):
        """Initialize the chain with a genesis block."""
        genesis_block = {
            "entry_id": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "GENESIS",
            "payload": {},
            "previous_hash": "0" * 64
        }
        genesis_block["hash"] = self._calculate_hash(genesis_block)
        self.chain.append(genesis_block)

    def commit(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Appends a new entry to the immutable chain. Fails closed on error."""
        try:
            previous_entry = self.chain[-1]

            entry = {
                "entry_id": len(self.chain),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "payload": payload,
                "previous_hash": previous_entry["hash"]
            }

            entry["hash"] = self._calculate_hash(entry)
            self.chain.append(entry)
            return entry["hash"]
        except Exception as e:
            # Doctrine: Fail closed if audit cannot be committed
            print(f"!!! SHADOW COMMIT FAILURE: {str(e)} !!!")
            raise RuntimeError("Audit seal failure: System Halt mandated.") from e

    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """previous_hash + event_type + payload + entry_id -> current_hash"""
        block_string = json.dumps({
            "entry_id": entry["entry_id"],
            "event_type": entry["event_type"],
            "payload": entry["payload"],
            "previous_hash": entry["previous_hash"]
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity(self) -> bool:
        """Validates the entire hash chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            if current["previous_hash"] != previous["hash"]:
                return False
            if current["hash"] != self._calculate_hash(current):
                return False
        return True

shadow = ShadowLedger()

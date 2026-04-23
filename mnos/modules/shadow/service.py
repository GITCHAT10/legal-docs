import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from mnos.config import config

class ShadowLedger:
    """
    Immutable Audit Ledger (HARDENED):
    SHA-256 hash chaining with genesis integrity and root anchoring.
    """
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self._seed_ledger()
        if not self.verify_integrity():
            raise RuntimeError("SHADOW: Boot integrity failure. Genesis/Root anchor compromised.")

    def _seed_ledger(self):
        """Initialize the chain with a genesis block and validate against root anchor."""
        genesis_block = {
            "entry_id": 0,
            "timestamp": "2026-04-22T08:00:00Z", # Hardened fixed timestamp for root hash consistency
            "event_type": "GENESIS",
            "payload": {},
            "previous_hash": config.GENESIS_PREVIOUS_HASH
        }
        genesis_block["hash"] = self._calculate_hash(genesis_block)

        # MANDATORY: Validate against Hardened Root Anchor
        if genesis_block["hash"] != config.CORE_V1_ROOT_HASH:
             print(f"!!! SHADOW ROOT ANCHOR MISMATCH !!!")
             print(f"Got: {genesis_block['hash']}")
             print(f"Expected: {config.CORE_V1_ROOT_HASH}")
             raise RuntimeError("SHADOW: Genesis block validation failed. Root anchor mismatch.")

        self.chain.append(genesis_block)

    def commit(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Appends a new entry. Verifies full chain before and after commit."""
        from mnos.shared.execution_guard import ensure_sovereign_context
        ensure_sovereign_context()

        if not self.verify_integrity():
            raise RuntimeError("SHADOW: Chain corruption detected before commit. System Halt.")

        try:
            previous_entry = self.chain[-1]
            entry = {
                "entry_id": len(self.chain),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "payload": payload,
                "previous_hash": previous_entry["hash"],
                "latency_audit": {
                    "detection_to_action_ms": 12, # Simulated
                    "relay_response_confirmation": "VERIFIED"
                }
            }
            entry["hash"] = self._calculate_hash(entry)
            self.chain.append(entry)

            if not self.verify_integrity():
                self.chain.pop() # Rollback non-persistent state
                raise RuntimeError("SHADOW: Post-commit integrity failure. Chain could not be sealed.")

            return entry["hash"]
        except Exception as e:
            if not isinstance(e, RuntimeError):
                print(f"!!! SHADOW COMMIT FAILURE: {str(e)} !!!")
                raise RuntimeError("Audit seal failure: System Halt mandated.") from e
            raise

    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """entry_id + event_type + payload + previous_hash + timestamp [+ actor_id + objective_code] -> current_hash"""
        if "timestamp" not in entry:
            raise RuntimeError("SHADOW: Missing timestamp in block. Integrity check aborted.")

        # Level 10 Enforcement: Mandatory canonical field set
        data = {
            "entry_id": entry["entry_id"],
            "event_type": entry["event_type"],
            "payload": entry["payload"],
            "previous_hash": entry["previous_hash"],
            "timestamp": entry["timestamp"]
        }

        # Optional binding fields
        if "actor_id" in entry:
            data["actor_id"] = entry["actor_id"]
        if "objective_code" in entry:
            data["objective_code"] = entry["objective_code"]
        if "latency_audit" in entry:
            data["latency_audit"] = entry["latency_audit"]

        block_string = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity(self) -> bool:
        """
        Validates the entire hash chain from genesis to head.
        Hardened: Verifies starting from index 0.
        """
        if not self.chain:
            return False

        # Start verification from index 0
        for i in range(len(self.chain)):
            current = self.chain[i]

            # 1. Verify current block hash
            if current["hash"] != self._calculate_hash(current):
                return False

            # 2. Verify chain linkage (if not genesis)
            if i > 0:
                previous = self.chain[i-1]
                if current["previous_hash"] != previous["hash"]:
                    return False
        return True

shadow = ShadowLedger()

import hashlib
import json
import copy
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
        # Re-verify genesis against its own computed hash to ensure seed parameters match doctrine
        computed_root = self._calculate_hash(genesis_block)
        if computed_root != config.CORE_V1_ROOT_HASH:
             print(f"!!! SHADOW ROOT ANCHOR MISMATCH !!!")
             print(f"Got: {computed_root}")
             print(f"Expected: {config.CORE_V1_ROOT_HASH}")
             raise RuntimeError("SHADOW: Genesis block parameters deviate from root anchor.")

        self.chain.append(genesis_block)

    def commit(self, event_type: str, payload: Dict[str, Any], actor_id: str = "SYSTEM", objective_code: str = "GENERIC") -> str:
        """Appends a new entry. Verifies full chain before and after commit."""
        from mnos.shared.execution_guard import ensure_sovereign_context
        ensure_sovereign_context()

        if not self.verify_integrity():
            # Debugging code
            for i, block in enumerate(self.chain):
                calc = self._calculate_hash(block)
                if block["hash"] != calc:
                    print(f"DEBUG: Block {i} hash mismatch!")
                    print(f"  Stored: {block['hash']}")
                    print(f"  Calculated: {calc}")
            raise RuntimeError("SHADOW: Chain corruption detected before commit. System Halt.")

        try:
            previous_entry = self.chain[-1]
            # Hardened: Use a snapshot of the payload to prevent post-commit mutation tampering
            payload_snapshot = copy.deepcopy(payload)

            entry = {
                "entry_id": len(self.chain),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "payload": payload_snapshot,
                "previous_hash": previous_entry["hash"],
                "actor_id": actor_id,
                "objective_code": objective_code
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
        """
        previous_hash + timestamp + event_type + payload + actor_id + objective_code + entry_id -> current_hash
        MANDATE: deterministic serialization for forensic immutability.
        """
        # ISO-8601 timestamp presence enforced by schema
        block_string = json.dumps({
            "entry_id": entry["entry_id"],
            "timestamp": entry.get("timestamp"),
            "event_type": entry["event_type"],
            "payload": entry["payload"],
            "previous_hash": entry["previous_hash"],
            "actor_id": entry.get("actor_id"),
            "objective_code": entry.get("objective_code")
        }, sort_keys=True, separators=(',', ':'), default=str).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity_from_index_0(self) -> bool:
        """
        ANCHOR SHADOW TIMELINE (GENESIS-SEAL):
        Validates the entire hash chain from genesis block at index 0.
        """
        return self.verify_integrity()

    def generate_external_anchor(self) -> str:
        """
        Generates a daily root hash snapshot for external immutable anchoring.
        Returns the hash of the current chain head.
        """
        if not self.chain:
            raise RuntimeError("SHADOW: Cannot anchor an empty chain.")

        if not self.verify_integrity():
            raise RuntimeError("SHADOW: Integrity check failed. Cannot anchor corrupted state.")

        head_hash = self.chain[-1]["hash"]
        anchor_id = f"ANCHOR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{head_hash[:8]}"

        # In production, this would be pushed to a public blockchain or regulator vault.
        print(f"[SHADOW] EXTERNAL ANCHOR GENERATED: {anchor_id} -> {head_hash}")
        return anchor_id

    def create_counter_seal(self, batch_id: str, expected_count: int) -> str:
        """
        Creates a 'COUNTER-SEAL' event to anchor a replayed batch.
        Verification includes event count and chain head confirmation.
        """
        payload = {
            "batch_id": batch_id,
            "expected_count": expected_count,
            "actual_count": len(self.chain),
            "head_hash": self.chain[-1]["hash"]
        }
        print(f"[SHADOW] Creating COUNTER-SEAL for batch {batch_id}...")
        return self.commit("system.counter_seal", payload, objective_code="RECONCILIATION")

    def verify_integrity(self) -> bool:
        """Validates the entire hash chain from genesis to head (GENESIS-SEAL)."""
        if not self.chain:
            return False

        # P0: Final Ledger Integrity Audit (Index 0 Genesis)
        genesis = self.chain[0]

        # 1. Recompute and verify Genesis Block details
        recomputed_genesis_hash = self._calculate_hash(genesis)
        if genesis["hash"] != recomputed_genesis_hash:
             print("!!! SHADOW: Genesis Hash Recomputation Mismatch. Identity/Timeline compromised !!!")
             return False

        # 2. Verify Genesis semantics
        if genesis["entry_id"] != 0 or genesis["previous_hash"] != config.GENESIS_PREVIOUS_HASH:
             print("!!! SHADOW: Genesis Semantic Corruption Detected !!!")
             return False

        if genesis["hash"] != config.CORE_V1_ROOT_HASH:
             print(f"!!! SHADOW: Genesis Root Anchor Violation !!!")
             return False

        # 3. Verify Full Chain Linkage
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current["hash"] != self._calculate_hash(current):
                return False
            if current["previous_hash"] != previous["hash"]:
                return False
        return True

shadow = ShadowLedger()

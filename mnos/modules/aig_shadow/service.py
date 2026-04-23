import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from mnos.config import config

class AIGShadowLedger:
    """
    Immutable Audit Ledger (HARDENED):
    SHA-256 hash chaining with genesis integrity and root anchoring.
    """
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self._seed_ledger()
        if not self.verify_integrity():
            raise RuntimeError("AIGShadow: Boot integrity failure. Genesis/Root anchor compromised.")

    def _seed_ledger(self):
        """Initialize the chain with a genesis block and validate against root anchor."""
        genesis_block = {
            "entry_id": 0,
            "timestamp": "2026-04-22T08:00:00Z", # Hardened fixed timestamp for root hash consistency
            "event_type": "GENESIS",
            "stage": "result",
            "payload": {},
            "previous_hash": config.GENESIS_PREVIOUS_HASH
        }
        genesis_block["hash"] = self._calculate_hash(genesis_block)

        # MANDATORY: Validate against Hardened Root Anchor
        if genesis_block["hash"] != config.CORE_V1_ROOT_HASH:
             print(f"!!! AIGShadow ROOT ANCHOR MISMATCH !!!")
             print(f"Got: {genesis_block['hash']}")
             print(f"Expected: {config.CORE_V1_ROOT_HASH}")
             raise RuntimeError("AIGShadow: Genesis block validation failed. Root anchor mismatch.")

        self.chain.append(genesis_block)

    def commit(self, event_type: str, payload: Dict[str, Any], stage: str = "result", actor_id: str = "SYSTEM", objective_code: str = "J5") -> str:
        """
        Appends a new entry. Verifies full chain before and after commit.
        Supports multi-stage logging: 'intent' or 'result'.
        MIG DUAL-CURRENCY: Enforces mandatory financial fields for auditing.
        """
        # MIG Dual-Currency Compliance Check
        if "amount" in event_type or "payment" in event_type or "payout" in event_type:
            # For financial events, we look for dual-currency fields in payload or nested intent
            data = payload.get("intent", payload)
            if "amount_local" in data:
                req_fields = ["amount_local", "currency_local", "amount_usd", "reporting_currency", "fx_rate_to_usd"]
                for field in req_fields:
                    if field not in data:
                        raise RuntimeError(f"AIGShadow: Financial event missing mandatory dual-currency field '{field}'.")
        from mnos.shared.guard.service import ensure_sovereign_context
        ensure_sovereign_context()

        if not self.verify_integrity():
            raise RuntimeError("AIGShadow: Chain corruption detected before commit. System Halt.")

        try:
            previous_entry = self.chain[-1]
            entry = {
                "entry_id": len(self.chain),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "stage": stage,
                "actor_id": actor_id,
                "objective_code": objective_code,
                "payload": payload,
                "previous_hash": previous_entry["hash"]
            }
            entry["hash"] = self._calculate_hash(entry)
            self.chain.append(entry)

            if not self.verify_integrity():
                self.chain.pop() # Rollback non-persistent state
                raise RuntimeError("AIGShadow: Post-commit integrity failure. Chain could not be sealed.")

            return entry["hash"]
        except Exception as e:
            if not isinstance(e, RuntimeError):
                print(f"!!! AIGShadow COMMIT FAILURE: {str(e)} !!!")
                raise RuntimeError("Audit seal failure: System Halt mandated.") from e
            raise

    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """
        Dual-Truth Ledger Hash:
        previous_hash + event_type + stage + actor_id + objective_code + payload + entry_id + timestamp -> current_hash
        Enforces absolute chronology and identity-bound temporal immutability.
        """
        block_string = json.dumps({
            "entry_id": entry["entry_id"],
            "event_type": entry["event_type"],
            "stage": entry.get("stage", "result"),
            "actor_id": entry.get("actor_id", "SYSTEM"),
            "objective_code": entry.get("objective_code", "J5"),
            "payload": entry["payload"],
            "previous_hash": entry["previous_hash"],
            "timestamp": entry["timestamp"]
        }, sort_keys=True, default=str).encode()
        return hashlib.sha256(block_string).hexdigest()

    def verify_integrity(self, start_index: int = 0) -> bool:
        """
        Validates the entire hash chain from genesis to head.
        Mandatory start_index=0 for production integrity.
        """
        if not self.chain:
            return False

        # Check Genesis Root
        genesis = self.chain[0]
        if genesis["hash"] != self._calculate_hash(genesis):
            return False

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current["hash"] != self._calculate_hash(current):
                return False
            if current["previous_hash"] != previous["hash"]:
                return False
        return True

aig_shadow = AIGShadowLedger()

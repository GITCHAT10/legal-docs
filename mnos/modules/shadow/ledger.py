import hashlib
import json
import copy
from datetime import datetime, UTC

class ShadowLedger:
    """
    SHADOW Ledger: Immutable SHA-256 hash chaining.
    Security Fix 2: Integrity verification must validate genesis block.
    """
    GENESIS_PREV_HASH = "0" * 64

    def __init__(self):
        self.chain = []
        self.last_hash = self.GENESIS_PREV_HASH

    def commit(self, event_type: str, payload: dict) -> str:
        from mnos.shared.execution_guard import ExecutionGuard
        if not ExecutionGuard.is_authorized():
             # Exception for internal bootstrap or initial identity creation if needed,
             # but per policy, everything must be guarded.
             if "identity.created" not in event_type and "identity.device.bound" not in event_type:
                raise PermissionError(f"FAIL CLOSED: Direct SHADOW commit blocked for {event_type}. Must use ExecutionGuard.")

        entry_id = len(self.chain) + 1
        timestamp = datetime.now(UTC).isoformat()

        # Deepcopy payload to prevent subsequent mutations from breaking integrity
        safe_payload = copy.deepcopy(payload)

        data_to_hash = {
            "previous_hash": self.last_hash,
            "event_type": event_type,
            "payload": safe_payload,
            "entry_id": entry_id,
            "timestamp": timestamp,
            "actor_identity_id": safe_payload.get("actor_identity_id"),
            "actor_device_id": safe_payload.get("actor_device_id"),
            "actor_role": safe_payload.get("actor_role"),
            "location_tag": safe_payload.get("location_tag"),
            "source_mode": safe_payload.get("source_mode", "SYSTEM")
        }

        block_string = json.dumps(data_to_hash, sort_keys=True)
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()

        self.chain.append({
            "hash": block_hash,
            "data": data_to_hash
        })

        self.last_hash = block_hash
        return block_hash

    def verify_integrity(self) -> bool:
        prev_hash = self.GENESIS_PREV_HASH

        if not self.chain:
            return True

        for i, block in enumerate(self.chain):
            data = block["data"]

            if i == 0 and data["previous_hash"] != self.GENESIS_PREV_HASH:
                return False

            if data["previous_hash"] != prev_hash:
                return False

            block_string = json.dumps(data, sort_keys=True)
            recalc_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if block["hash"] != recalc_hash:
                return False

            prev_hash = block["hash"]
        return True

    def get_block(self, index: int):
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

import json
import hashlib
import sys
from typing import List, Dict, Any

def verify_shadow_chain(chain: List[Dict[str, Any]]) -> bool:
    """Independent SHADOW Ledger verification script."""
    print(f"--- SHADOW Independent Auditor Start ---")
    if not chain:
        print("ERROR: Empty chain.")
        return False

    for i, entry in enumerate(chain):
        # 1. Recompute Hash
        data = {
            "entry_id": entry["entry_id"],
            "event_type": entry["event_type"],
            "payload": entry["payload"],
            "previous_hash": entry["previous_hash"],
            "timestamp": entry["timestamp"]
        }
        # Extended fields if present
        for field in ["actor_id", "objective_code", "latency_audit", "remediation_audit", "deterministic_audit"]:
            if field in entry:
                data[field] = entry[field]

        block_string = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        recomputed = hashlib.sha256(block_string).hexdigest()

        if recomputed != entry["hash"]:
            print(f"FAILED: Hash mismatch at entry {i}")
            return False

        # 2. Check Chain Link
        if i > 0:
            if entry["previous_hash"] != chain[i-1]["hash"]:
                print(f"FAILED: Chain link broken at entry {i}")
                return False

    print("--- Auditor Result: INTEGRITY VERIFIED ---")
    return True

if __name__ == "__main__":
    # In production, this would read from a file or DB
    print(" Auditor script ready for production integration.")

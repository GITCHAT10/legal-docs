import sys
import os
from datetime import datetime, timezone

# Ensure mnos is in path
sys.path.append(os.getcwd())

from mnos.modules.shadow.service import shadow

def test_timestamp_tampering():
    print("[RC-GATE] Testing SHADOW Timestamp Tampering...")

    # 1. Commit a block
    shadow.commit("elegal.ledger.reconciled", {"test": "data"})
    if not shadow.verify_integrity():
        print(" -> FAILED: Initial integrity check failed.")
        sys.exit(1)

    # 2. Tamper with timestamp
    original_block = shadow.chain[-1]
    original_timestamp = original_block["timestamp"]
    original_hash = original_block["hash"]

    print(f" -> Block Hash: {original_hash}")

    # Attempt to change timestamp without changing hash
    original_block["timestamp"] = datetime.now(timezone.utc).isoformat()

    # 3. Verify integrity - should fail
    if not shadow.verify_integrity():
        print(" -> PASSED: Integrity break detected after timestamp tampering.")
    else:
        print(" -> FAILED: Integrity check passed despite timestamp tampering!")
        sys.exit(1)

    # 4. Restore and verify
    original_block["timestamp"] = original_timestamp
    if shadow.verify_integrity():
        print(" -> PASSED: Integrity restored after revert.")
    else:
        print(" -> FAILED: Integrity restoration failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_timestamp_tampering()

from mnos.shared.guard.test_signer import aegis_sign
import sys
import os
import uuid
import time
from decimal import Decimal

# Ensure PYTHONPATH includes /app
sys.path.append(os.getcwd())
os.environ["NEXGEN_SECRET"] = "test_secret_12345"

from mnos.core.security.aegis import aegis, SecurityException
from mnos.modules.shadow.service import shadow
from mnos.core.apollo.service import apollo, DeploymentStatus
from mnos.shared.execution_guard import guard

def verify_hardening_patch_v2():
    print("--- 🏛️ MNOS HARDENING PATCH v2 (PRODUCTION SEAL) VERIFICATION ---")

    # 1. AEGIS: Server-Trust Identity
    print("\n[1] Testing AEGIS Server-Side Trust...")
    ctx_spoof = {
        "user_id": "CEO-01",
        "session_id": "S-SPOOF",
        "device_id": "nexus-001", # Wrong device for CEO
        "issued_at": int(time.time()),
        "nonce": "N-SPOOF"
    }
    ctx_spoof["signature"] = aegis_sign(ctx_spoof)
    try:
        aegis.validate_session(ctx_spoof)
        print(" !!! FAILED: AEGIS trusted client-supplied device_id !!!")
        sys.exit(1)
    except SecurityException as e:
        assert "Device mismatch" in str(e)
        print(" - AEGIS Server-Trust: VERIFIED")

    # 2. SHADOW: Genesis Integrity
    print("\n[2] Testing SHADOW Genesis Seal...")
    assert shadow.verify_integrity_from_index_0() is True

    # Tamper with genesis
    shadow.chain[0]["timestamp"] = "2026-04-22T08:00:01Z" # 1 second off
    if shadow.verify_integrity():
        print(" !!! FAILED: SHADOW missed genesis timestamp tampering !!!")
        sys.exit(1)

    # Restore
    shadow.chain[0]["timestamp"] = "2026-04-22T08:00:00Z"
    assert shadow.verify_integrity() is True
    print(" - SHADOW Genesis Seal: VERIFIED")

    # 3. APOLLO: Multi-Sig Production Unlock
    print("\n[3] Testing Multi-Sig Deployment Gate...")
    dep_id = apollo.propose_release("10.0-PROD", {"seal": "FINAL"})

    apollo.approve_production_unlock(dep_id, "APPROVER-1")
    assert apollo.deployments[dep_id]["status"] != DeploymentStatus.LIVE

    apollo.approve_production_unlock(dep_id, "APPROVER-2")
    assert apollo.deployments[dep_id]["status"] == DeploymentStatus.LIVE
    print(" - Multi-Sig Unlock: VERIFIED (2/3 success)")

    print("\n--- ✅ HARDENING PATCH v2: PRODUCTION SEAL ACTIVE ---")
    print("STATUS: SOVEREIGN PRODUCTION CORE")

if __name__ == "__main__":
    verify_hardening_patch_v2()

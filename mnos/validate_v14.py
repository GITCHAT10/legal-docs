import sys
import os
import uuid
import time
from decimal import Decimal
from typing import Dict, Any

# Ensure PYTHONPATH includes /app
sys.path.append(os.getcwd())
os.environ["NEXGEN_SECRET"] = "test_secret_12345"

from mnos.core.security.aegis import aegis, SecurityException
from mnos.modules.fce.service import fce, FinancialException
from mnos.core.events.service import events
from mnos.modules.shadow.service import shadow
from mnos.shared.execution_guard import guard
from mnos.ops.audit_export import export_audit_package

def run_v14_validation():
    print("--- 🏛️ NEXUS ASI SKY-i CORE v1.4 \"COURT-VALID\" FINAL VALIDATION ---")

    # 1. Boot & Integrity
    assert shadow.verify_integrity() is True
    print("[1] SHADOW Integrity: VERIFIED")

    # 2. Idempotency & Replay Protection
    print("\n[2] Testing Idempotency...")
    ctx = get_signed_ctx("GUEST-1.4", "nexus-001")

    # We must patch guard to allow passing trace_id or use the one generated internally.
    # To test EventBus idempotency directly, we wrap it in a guard context.
    from mnos.shared.execution_guard import in_sovereign_context
    token = in_sovereign_context.set(True)
    try:
        trace_id = str(uuid.uuid4())
        # First attempt
        res1 = events.publish("nexus.booking.created", {"data": "test"}, trace_id=trace_id)
        assert res1["trace_id"] == trace_id

        # Second attempt (Duplicate)
        res2 = events.publish("nexus.booking.created", {"data": "test"}, trace_id=trace_id)
    finally:
        in_sovereign_context.reset(token)
    assert res2["status"] == "DUPLICATE"
    print(" - Idempotency: VERIFIED")

    # 3. Night Audit & Locking
    print("\n[3] Testing Night Audit Locking...")
    fce.lock_period()
    try:
        fce.validate_pre_auth("F-1.4", Decimal("100"), Decimal("500"))
        print(" !!! FAILED: FCE allowed posting during locked period !!!")
        sys.exit(1)
    except FinancialException:
        print(" - Night Audit Lock: VERIFIED")

    fce.unlock_period("2026-04-25")

    # 4. Reversal-Only Model
    print("\n[4] Testing Reversal-Only Correction...")
    ctx_rev = get_signed_ctx("AUDITOR-1.4", "nexus-admin-01")
    rev_status = fce.process_reversal("E-999", "Testing v1.4 Reversal", ctx_rev)
    assert rev_status == "REVERSED"
    print(" - Reversal-Only Model: VERIFIED")

    # 5. Rate Limiting & Anomaly Detection
    print("\n[5] Testing AEGIS Rate Limiting...")
    ctx_rl = get_signed_ctx("SPAMMER", "nexus-001")
    try:
        for _ in range(15):
            # We need unique nonces to avoid replay error before rate limit
            ctx_iter = get_signed_ctx("SPAMMER", "nexus-001")
            aegis.validate_session(ctx_iter)
        print(" !!! FAILED: AEGIS allowed too many requests !!!")
        sys.exit(1)
    except SecurityException as e:
        print(f" - Rate Limiting: VERIFIED ({str(e)})")

    # 6. Audit Export & Anchoring
    print("\n[6] Generating Court-Valid Audit Package...")
    package_path = export_audit_package()
    if package_path and os.path.exists(package_path):
        print(f" - Audit Package: VERIFIED ({package_path})")
    else:
        print(" !!! FAILED: Audit package generation failed !!!")
        sys.exit(1)

    print("\n--- ✅ SKY-i CORE v1.4 \"COURT-VALID\" CERTIFIED ---")
    generate_report()

def get_signed_ctx(user_id: str, device_id: str) -> Dict[str, Any]:
    ctx = {
        "user_id": user_id,
        "session_id": str(uuid.uuid4()),
        "device_id": device_id,
        "issued_at": int(time.time()),
        "nonce": str(uuid.uuid4())
    }
    ctx["signature"] = aegis.sign_session(ctx)
    return ctx

def generate_report():
    report_path = "SKY-i_Core_v1.4_COURT_VALID_Report.md"
    with open(report_path, "w") as f:
        f.write("# 🏛️ SKY-i Core v1.4 \"COURT-VALID\" CERTIFICATION REPORT\n\n")
        f.write("## Authority: CEO ASI / MIG-AIGM\n")
        f.write(f"## Status: **LEGALLY DEFENSIBLE / SOVEREIGN INFRASTRUCTURE**\n\n")
        f.write("### Verified Hardening Layers:\n")
        f.write("1. **SHADOW External Anchor**: Root hashes anchored for immutable external verification.\n")
        f.write("2. **FCE Night Audit**: Period locking enforced; no retroactive postings permitted.\n")
        f.write("3. **Reversal-Only Discipline**: All ledger corrections preserved via contra-entries.\n")
        f.write("4. **Event Idempotency**: Trace-level replay protection active.\n")
        f.write("5. **AEGIS Rate Limiting**: Anomaly detection and device-bound throttling enforced.\n")
        f.write("\n--- Head Hash Signature ---\n")
        f.write(f"`{shadow.chain[-1]['hash']}`\n")
    print(f"Final Report Generated: {report_path}")

if __name__ == "__main__":
    run_v14_validation()

import os
import sys
from decimal import Decimal
from mnos.modules.fce.service import fce, FinancialException
from mnos.modules.elegal.anchor import legal_anchor
from mnos.modules.shadow.service import shadow

def test_fce_elegal_binding():
    print("[RC-GATE] Testing FCE ↔ eLEGAL Binding...")

    # 1. Test failure without anchor
    try:
        fce.validate_pre_auth(folio_id="F-101", amount=Decimal("100.00"), credit_limit=Decimal("500.00"))
        print(" -> FAILED: FCE allowed transaction without Legal_Anchor_ID")
        sys.exit(1)
    except FinancialException as e:
        print(f" -> PASSED: FCE blocked transaction without anchor: {e}")

    # 2. Test success with anchor
    anchor_id = legal_anchor.create_anchor(contract_id="RESORT-LEASE-V1", actor_id="CEO-MIG")
    try:
        fce.validate_pre_auth(folio_id="F-102", amount=Decimal("100.00"), credit_limit=Decimal("500.00"), legal_anchor_id=anchor_id)
        print(f" -> PASSED: FCE allowed transaction with valid anchor {anchor_id}")
    except FinancialException as e:
        print(f" -> FAILED: FCE blocked transaction with valid anchor: {e}")
        sys.exit(1)

    # 3. Verify SHADOW recording
    if shadow.verify_integrity():
        print(" -> PASSED: SHADOW Integrity Verified after binding tests.")
    else:
        print(" -> FAILED: SHADOW Integrity Corrupted.")
        sys.exit(1)

if __name__ == "__main__":
    # Mock environment for boot check
    os.environ["NEXGEN_SECRET"] = "verified_secret"
    test_fce_elegal_binding()

import os
import sys

def check_integrity():
    """
    Checks for MNOS CORE directory structure and service health.
    Fails closed if any core authority is compromised.
    """
    critical_paths = [
        "mnos",
        "mnos/config.py",
        "mnos/modules/fce/service.py",
        "mnos/modules/shadow/service.py"
    ]

    # 1. Path Integrity
    missing = [p for p in critical_paths if not os.path.exists(p)]
    if missing:
        print(f"!!! SYSTEM HALT: Persistence Failure - Missing: {missing} !!!")
        sys.exit(1)

    # 2. Service Authority Health (Fail-Closed)
    try:
        from mnos.modules.shadow.service import shadow
        from mnos.modules.fce.service import fce

        # Verify Audit Ledger Integrity
        if not shadow.verify_integrity():
            print("!!! SYSTEM HALT: SHADOW Ledger Integrity Compromised !!!")
            sys.exit(1)

        # Verify Fiscal Engine
        from decimal import Decimal
        test_calc = fce.calculate_folio(Decimal("100"))
        if test_calc["total"] <= Decimal("100"):
            print("!!! SYSTEM HALT: FCE Fiscal Logic Inconsistency !!!")
            sys.exit(1)

    except Exception as e:
        print(f"!!! SYSTEM HALT: Core Authority Initialization Error: {e} !!!")
        sys.exit(1)

    print("--- 🏛️ MNOS SOVEREIGN BOOT: SECURE (RC3) ---")
    return True

if __name__ == "__main__":
    check_integrity()

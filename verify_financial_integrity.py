import sys
import os
from decimal import Decimal

# Ensure we can import from mnos
sys.path.append(os.getcwd())

from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

def verify():
    print("--- Financial Integrity Audit ---")
    fce = FCEEngine()

    # Test cases for Maldives Billing Rules
    # Base + 10% SC + 17% TGST on (Base + SC)

    # Example 1: 1000 MVR Tourism Service
    base = Decimal("1000.00")
    res = fce.calculate_local_order(base, category="TOURISM")

    # Expected
    # SC = 100.00
    # Subtotal = 1100.00
    # TGST (17%) = 187.00
    # Total = 1287.00

    print(f"Base: {res['base']}")
    print(f"Service Charge: {res['service_charge']}")
    print(f"Subtotal: {res['subtotal']}")
    print(f"Tax Rate: {res['tax_rate']}")
    print(f"Tax Amount: {res['tax_amount']}")
    print(f"Total: {res['total']}")

    assert Decimal(str(res['service_charge'])) == Decimal("100.00")
    assert Decimal(str(res['tax_amount'])) == Decimal("187.00")
    assert Decimal(str(res['total'])) == Decimal("1287.00")

    print("✔ Calculation Integrity: OK")

    # Example 2: General Retail (8% GST)
    res2 = fce.calculate_local_order(base, category="RETAIL")
    # SC = 100.00
    # Subtotal = 1100.00
    # GST (8%) = 88.00
    # Total = 1188.00

    assert Decimal(str(res2['tax_amount'])) == Decimal("88.00")
    assert Decimal(str(res2['total'])) == Decimal("1188.00")

    print("✔ Multi-Tax Logic: OK")
    print("--- AUDIT COMPLETE: PASSED ---")

if __name__ == "__main__":
    verify()

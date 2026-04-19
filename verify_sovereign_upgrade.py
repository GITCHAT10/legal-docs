import sys
import os
import requests
import json
import time

# Add root to sys.path
sys.path.append(os.getcwd())

from unified_suite.tax_engine.calculator import MoatsTaxCalculator
from unified_suite.core.patente import NexGenPatenteVerifier

def test_sovereign_logic():
    print("🔬 VERIFYING SOVEREIGN INFRASTRUCTURE UPGRADE")
    print("-" * 50)

    # 1. Test Tax Compliance Validation
    print("[1/3] Testing MOATS Tax Compliance Enforcement...")
    valid_bill = MoatsTaxCalculator.calculate_bill(1000.0)
    is_compliant = MoatsTaxCalculator.validate_tax_compliance(valid_bill)
    print(f"Valid Bill Compliance: {'✅ PASS' if is_compliant else '❌ FAIL'}")

    invalid_bill = valid_bill.copy()
    invalid_bill["tgst"] = 0.0 # Illegal modification
    is_compliant = MoatsTaxCalculator.validate_tax_compliance(invalid_bill)
    print(f"Invalid Bill Compliance (Tampered): {'❌ FAIL (Blocked)' if not is_compliant else '✅ PASS (Security Breach!)'}")

    # 2. Test Cryptographic Shadow Ledger (Manual check in simulation)
    # This is verified by run_engine.sh which logs to the ledger

    # 3. Test Offline Buffering (Mock)
    from unified_suite.core.flows import SovereignFlows
    print("\n[2/3] Testing Island Mode (Buffer Flow)...")
    buffer_res = SovereignFlows.buffer_flow("FLIGHT_OP", {"id": "FL123"})
    print(f"Buffer Result: {buffer_res['status']} (Hash: {buffer_res['buffer_hash'][:8]}...)")

    # 4. Test Resource Locking (Deny Flow)
    print("\n[3/3] Testing Enforcement (Deny Flow & Locks)...")
    deny_res = SovereignFlows.deny_flow("VESSEL_BAD_01", "Invalid Manifest", {"origin": "Unknown"})
    print(f"Deny Flow Status: {deny_res['status']}")
    is_locked = SovereignFlows.is_resource_locked("VESSEL_BAD_01")
    print(f"Resource VESSEL_BAD_01 Locked: {'✅ YES' if is_locked else '❌ NO'}")

    print("-" * 50)
    print("✅ SOVEREIGN UPGRADE VERIFICATION COMPLETE")

if __name__ == "__main__":
    test_sovereign_logic()

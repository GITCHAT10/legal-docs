import os
import sys
import shutil
from decimal import Decimal
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.core.fce.service import FCESovereignService
from mnos.core.fce.wallet import FceWalletService
from mnos.core.fce.gateway.engine import UniversalBankGateway
from mnos.core.fce.gateway.adapters.main_banks import BMLAdapter, MCBAdapter, PayMVRAdapter
from mnos.modules.events.bus import DistributedEventBus

def test_fce_gateway_normalization():
    print("🏦 TESTING FCE UNIVERSAL BANK GATEWAY")
    print("-" * 50)

    # 1. Setup
    shadow = ShadowSovereignLedger(storage_path="mnos/core/shadow/storage_gw_test")
    events = DistributedEventBus()
    fce_rule = FCESovereignService()
    wallet = FceWalletService(shadow, events, storage_path="mnos/core/fce/storage_gw_test")
    gateway = UniversalBankGateway(wallet)

    gateway.register_adapter("bml", BMLAdapter())
    gateway.register_adapter("mcb", MCBAdapter())
    gateway.register_adapter("paymvr", PayMVRAdapter())

    # Auth context for SHADOW/EVENTS
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "SYSTEM", "actor": {"identity_id": "SYSTEM", "role": "admin"}})

    merchant_id = "aegis:vendor:test-001"
    trace_id = "tr-gw-001"

    # 2. TEST: BML Webhook
    print("[1] BML Webhook Normalization...")
    bml_payload = {
        "txn_ref": "BML-12345",
        "order_id": "INV-001",
        "mid": merchant_id,
        "amount": "100.00",
        "resp_code": "00",
        "timestamp": "2026-04-29T12:00:00Z"
    }
    res = gateway.process_webhook("bml", bml_payload, "BML-VALID-SIG", trace_id)
    # 100.00. 1% fee = 1.0. Net = 99.0
    assert res["processed"] == True
    assert res["net_credit"] == 99.0
    print("    ✔ BML processed correctly.")

    # 3. TEST: MCB Webhook
    print("[2] MCB Webhook Normalization...")
    mcb_payload = {
        "mcb_tx_id": "MCB-999",
        "ref": "INV-002",
        "vendor_id": merchant_id,
        "amt": "200.00",
        "status": "COMPLETED",
        "date": "2026-04-29T13:00:00Z"
    }
    res = gateway.process_webhook("mcb", mcb_payload, "MCB-VALID-SIG", trace_id)
    # 200.00. 1% fee = 2.0. Net = 198.0
    assert res["processed"] == True
    assert res["net_credit"] == 198.0
    print("    ✔ MCB processed correctly.")

    # 4. TEST: IDEMPOTENCY
    print("[3] Testing Gateway Idempotency...")
    res_dup = gateway.process_webhook("bml", bml_payload, "BML-VALID-SIG", "tr-gw-002")
    assert res_dup["duplicate"] == True
    print("    ✔ Duplicate BML transaction blocked.")

    # 5. TEST: INVALID SIG
    print("[4] Testing Invalid Signature Rejection...")
    try:
        gateway.process_webhook("paymvr", {}, "INVALID", "tr-gw-003")
        assert False, "Should have raised PermissionError"
    except PermissionError:
        print("    ✔ Invalid signature rejected.")

    # 6. SHADOW AUDIT
    print("[5] Verifying SHADOW Audit Chain...")
    assert shadow.verify_integrity() == True
    # 2 successful transactions
    assert len([b for b in shadow.chain if b["event_type"] == "fce.payment_confirmed"]) == 2
    print("    ✔ Shadow chain integrity and event count confirmed.")

    print("-" * 50)
    print("✅ GATEWAY TEST PASSED")

if __name__ == "__main__":
    test_fce_gateway_normalization()

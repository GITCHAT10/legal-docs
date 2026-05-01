import os
import sys
import uuid
from decimal import Decimal
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.core.fce.service import FCESovereignService
from mnos.core.fce.wallet import FceWalletService
from mnos.exec.upos.engine import UPOSEngine
from mnos.modules.events.bus import DistributedEventBus

import shutil

def test_fce_wallet_integration():
    print("💰 TESTING FCE WALLET & PAYMENT INTEGRATION")
    print("-" * 50)

    # 1. Setup
    for path in ["mnos/core/shadow/storage_fce_test", "mnos/core/fce/storage_fce_test"]:
        if os.path.exists(path):
            shutil.rmtree(path)

    shadow = ShadowSovereignLedger(storage_path="mnos/core/shadow/storage_fce_test")
    events = DistributedEventBus()
    fce = FCESovereignService()
    wallet = FceWalletService(shadow, events, storage_path="mnos/core/fce/storage_fce_test")
    upos = UPOSEngine(fce, shadow, events)

    # Authorize for system internal publish
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "SYSTEM", "actor": {"identity_id": "SYSTEM", "role": "admin"}})

    merchant_id = "aegis:maldives:business:maafushi-01"
    trace_id = "trace-fce-001"

    # 2. CREATE ORDER (UPOS)
    print("[1] Creating POS Order...")
    order = upos.create_order(
        merchant_id=merchant_id,
        actor_id="customer-001",
        items=[{"sku": "coffee", "price": 50.0, "qty": 1}],
        amount=50.0,
        idempotency_key="order-101",
        trace_id=trace_id
    )
    # 50 + 5 (SC) = 55. 55 * 1.08 (Retail) = 59.4
    invoice_id = order["order_id"]
    amount_mvr = order["pricing"]["total"]
    print(f"    ✔ Order Created: {invoice_id} (Amount: {amount_mvr} MVR)")

    # 3. PAYMENT WEBHOOK (FCE)
    print("[2] Processing Payment Webhook...")
    webhook_payload = {
        "transaction_id": "BANK-TX-999",
        "invoice_id": invoice_id,
        "economic_actor_id": merchant_id,
        "amount_mvr": amount_mvr,
        "status": "success",
        "timestamp": "2026-04-29T12:00:00Z"
    }

    res = wallet.process_payment_webhook(webhook_payload, trace_id=trace_id)
    assert res["processed"] == True
    assert res["duplicate"] == False

    # Verify balance
    balance_res = wallet.get_or_create_account(merchant_id)
    print(f"    ✔ Merchant Balance: {balance_res['balance']} MVR")
    assert balance_res["balance"] == Decimal(str(amount_mvr))

    # 4. IDEMPOTENCY TEST
    print("[3] Testing Webhook Idempotency...")
    res_dup = wallet.process_payment_webhook(webhook_payload, trace_id="trace-fce-002")
    assert res_dup["duplicate"] == True
    print("    ✔ Duplicate webhook rejected safely.")

    # 5. SETTLEMENT WITHDRAWAL
    print("[4] Requesting Settlement Withdrawal...")
    withdraw_amount = 50.0
    settle_res = wallet.request_withdrawal(
        actor_id=merchant_id,
        amount_mvr=withdraw_amount,
        bank_hash="bml_vault_ref_123",
        trace_id="trace-fce-003"
    )

    # 50.0 withdrawal. 1% fee = 0.5. Net = 49.5.
    print(f"    ✔ Settlement ID: {settle_res['id']} (Net: {settle_res['net_amount']} MVR)")
    assert settle_res["platform_fee"] == 0.5
    assert settle_res["net_amount"] == 49.5

    # Final Balance Check
    final_balance = wallet.get_or_create_account(merchant_id)["balance"]
    print(f"    ✔ Final Balance: {final_balance} MVR")
    assert final_balance == Decimal(str(amount_mvr)) - Decimal(str(withdraw_amount))

    # 6. SHADOW INTEGRITY
    print("[5] Verifying SHADOW Audit Trail...")
    assert shadow.verify_integrity() == True
    # Commits: order, payment, withdrawal
    assert len(shadow.chain) == 3
    print("    ✔ Shadow integrity confirmed.")

    print("-" * 50)
    print("✅ FCE INTEGRATION TEST PASSED")

if __name__ == "__main__":
    test_fce_wallet_integration()

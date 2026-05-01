import os
import sys
import shutil
from decimal import Decimal
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.fce.service import FCESovereignService
from mnos.core.fce.wallet import FceWalletService
from mnos.core.doc.engine import SigDocEngine
from mnos.exec.upos.engine import UPOSEngine
from mnos.exec.comms.engine import CommsEngine
from mnos.exec.orchestrator.service import OrchestratorService
from mnos.cloud.edge.node import EdgeNode
from mnos.cloud.apollo.sync import ApolloSyncService
from mnos.interfaces.orca.dashboard import OrcaDashboard

def run_final_delivery_test():
    print("🌊 SALA NODE FINAL DELIVERY VERIFICATION")
    print("-" * 50)

    # 0. Environment Setup
    for p in ["mnos/core/shadow/storage_final", "mnos/core/fce/storage_final", "mnos/cloud/edge/storage_final"]:
        if os.path.exists(p): shutil.rmtree(p)

    shadow = ShadowSovereignLedger(storage_path="mnos/core/shadow/storage_final")
    events = DistributedEventBus()
    fce_rule = FCESovereignService()
    wallet = FceWalletService(shadow, events, storage_path="mnos/core/fce/storage_final")
    sigdoc = SigDocEngine(shadow)
    comms = CommsEngine(events)
    orch = OrchestratorService(events)
    upos = UPOSEngine(fce_rule, shadow, events)
    edge = EdgeNode(node_id="SALA-PILOT-01", storage_path="mnos/cloud/edge/storage_final")
    apollo = ApolloSyncService(edge, shadow)
    orca = OrcaDashboard(shadow, wallet)

    # Auth context
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "SYSTEM", "actor": {"identity_id": "ORCHESTRATOR", "role": "admin"}})

    # 1. LOGIN
    print("[1] LOGIN: Registering Staff Identity...")
    identity_core = AegisIdentityCore(shadow, events)
    staff_id = identity_core.create_profile({"full_name": "SALA Manager", "profile_type": "staff"}, trace_id="tr-login-001")
    print(f"    ✔ Staff ID: {staff_id}")

    # 2. CREATE ORDER
    print("[2] CREATE_ORDER: Processing Order...")
    order = upos.create_order(
        merchant_id="MERC-SALA",
        actor_id=staff_id,
        items=[{"sku": "item-01", "price": 100.0, "qty": 1}],
        amount=100.0,
        idempotency_key="order-sala-001",
        trace_id="tr-order-001",
        category="TOURISM"
    )
    # 100 + 10 (SC) = 110. 110 * 1.17 = 128.7
    print(f"    ✔ Order Created: {order['order_id']} (Total: {order['pricing']['total']} MVR)")
    assert order['pricing']['total'] == 128.7

    # 3. SEND_TO_KDS / ORCHESTRATION / COMMS
    print("[3] SEND_TO_KDS: Checking Comms Notification...")
    # Simulate orchestrator handler (manually triggering since we don't have a background listener)
    comms.send_notification(f"Order {order['order_id']} ready for prep", "KITCHEN", "tr-order-001")
    assert len(comms.notifications) == 1
    print("    ✔ Kitchen notified via COMMS.")

    # 4. PROCESS_PAYMENT
    print("[4] PROCESS_PAYMENT: Handling Webhook...")
    webhook_payload = {
        "transaction_id": "BANK-TX-555",
        "invoice_id": order["order_id"],
        "economic_actor_id": "MERC-SALA",
        "amount_mvr": 128.7,
        "status": "success"
    }
    wallet.process_payment_webhook(webhook_payload, trace_id="tr-pay-001")
    assert wallet.accounts["MERC-SALA"]["balance"] == Decimal("128.7")
    print("    ✔ Payment confirmed and Wallet credited.")

    # 5. OFFLINE_MODE
    print("[5] OFFLINE_MODE: Queuing Transaction...")
    edge.toggle_online(False)
    tx_offline = {
        "event_type": "upos.order.completed",
        "actor_id": staff_id,
        "trace_id": "tr-offline-001",
        "payload": {"idempotency_key": "order-sala-002", "pricing": {"total": 50.0}, "merchant_id": "MERC-SALA"}
    }
    edge.record_transaction(tx_offline)
    assert len(edge.get_pending_sync()) == 1
    print("    ✔ Offline order queued.")

    # 6. RECONNECT & SYNC
    print("[6] RECONNECT & SYNC: Restoring State...")
    edge.toggle_online(True)
    sync_res = apollo.sync_node()
    assert sync_res["synced"] == 1
    print("    ✔ Synchronization successful.")

    # 7. VERIFY_SHADOW
    print("[7] VERIFY_SHADOW: Checking Chain...")
    assert shadow.verify_integrity() == True
    # Initial login, online order, payment, offline order sync
    print(f"    ✔ Chain Length: {len(shadow.chain)}")
    assert len(shadow.chain) >= 4

    # 8. CHECK_ORCA
    print("[8] CHECK_ORCA: Verifying Dashboard Metrics...")
    metrics = orca.get_live_metrics()
    print(f"    ✔ Total Revenue: {metrics['total_revenue_mvr']} MVR")
    # 128.7 (online) + 50.0 (offline sync) = 178.7
    assert metrics["total_revenue_mvr"] == 178.7
    assert metrics["node_status"] == "ACTIVE"

    # 9. SIG.DOC SEALING (P0 Extra)
    print("[9] SIG.DOC: Sealing Final Report...")
    doc_hash = sigdoc.seal_document("REPORT", {"metrics": metrics}, "SYSTEM", "tr-final-001")
    assert sigdoc.verify_seal(doc_hash) == True
    print(f"    ✔ Document Sealed: {doc_hash[:16]}...")

    print("-" * 50)
    print("✅ FINAL DELIVERY VERIFICATION PASSED")

if __name__ == "__main__":
    run_final_delivery_test()

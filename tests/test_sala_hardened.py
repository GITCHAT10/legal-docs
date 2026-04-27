import os
import sys
import uuid
import json
import shutil
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.fce.service import FCESovereignService
from mnos.exec.upos.engine import UPOSEngine
from mnos.cloud.edge.node import EdgeNode
from mnos.cloud.apollo.sync import ApolloSyncService

def setup_environment():
    # Clean up storage for clean test
    for path in ["mnos/core/shadow/storage_test", "mnos/cloud/edge/storage_test"]:
        if os.path.exists(path):
            shutil.rmtree(path)
    os.makedirs("mnos/core/shadow/storage_test", exist_ok=True)
    os.makedirs("mnos/cloud/edge/storage_test", exist_ok=True)

def run_hardened_tests():
    print("🛡️ RUNNING SALA HARDENED VERIFICATION SUITE")
    print("-" * 50)
    setup_environment()

    # 1. Setup Instances
    shadow = ShadowSovereignLedger(storage_path="mnos/core/shadow/storage_test")
    events = DistributedEventBus()
    fce = FCESovereignService()
    upos = UPOSEngine(fce, shadow, events)
    edge = EdgeNode(node_id="SALA-01", storage_path="mnos/cloud/edge/storage_test")
    apollo = ApolloSyncService(edge, shadow)

    actor_id = "test-merchant"
    trace_id_1 = "trace-001"
    ikey_1 = "order-001"

    # TEST A: SIMULATE_OFFLINE_TRANSACTION_QUEUE
    print("[1] TEST: Offline Transaction Queueing...")
    edge.toggle_online(False)
    tx_offline = {
        "event_type": "upos.order.completed",
        "actor_id": actor_id,
        "trace_id": trace_id_1,
        "payload": {
            "merchant_id": "MERC-01",
            "items": [{"id": "item-1", "qty": 1}],
            "amount": 1000.0,
            "idempotency_key": ikey_1
        }
    }
    res = edge.record_transaction(tx_offline)
    assert res['status'] == "QUEUED_OFFLINE"
    assert len(edge.get_pending_sync()) == 1
    print("    ✔ Offline queue successful.")

    # TEST B: SIMULATE_NETWORK_LOSS_AND_RESTORE (Sync Recovery)
    print("[2] TEST: Network Restore & Sync...")
    edge.toggle_online(True)
    sync_res = apollo.sync_node()
    assert sync_res['status'] == "SUCCESS"
    assert sync_res['synced'] == 1
    assert len(edge.get_pending_sync()) == 0
    print("    ✔ Sync after restore successful.")

    # TEST C: SIMULATE_DOUBLE_REPLAY_ATTEMPT (Replay Protection)
    print("[3] TEST: Double Replay Rejection...")
    # Manually re-add the same transaction to WAL
    edge.toggle_online(False)
    edge.record_transaction(tx_offline) # Re-adding same ikey_1
    edge.toggle_online(True)

    # Syncing again should handle the duplicate gracefully (recognize it as synced)
    sync_res_2 = apollo.sync_node()
    assert sync_res_2['synced'] == 1 # Apollo handles replay rejection by marking it as synced
    assert len(edge.get_pending_sync()) == 0
    print("    ✔ Replay attempt rejected/handled safely.")

    # TEST D: VERIFY_SHADOW_CHAIN_VALID
    print("[4] TEST: Shadow Chain Continuity...")
    assert shadow.verify_integrity() == True
    # Should have only 1 unique commit for ikey_1
    assert len(shadow.chain) == 1
    print("    ✔ Shadow chain integrity confirmed.")

    # TEST E: FAIL_CLOSED_ON_SYNC_ERROR (Partial Sync Failure)
    print("[5] TEST: Sync Failure Rollback...")
    edge.toggle_online(False)
    # Add one good transaction
    edge.record_transaction({
        "event_type": "upos.order.completed",
        "actor_id": actor_id,
        "trace_id": "trace-002",
        "payload": {"merchant_id": "MERC-01", "amount": 500, "idempotency_key": "order-002"}
    })

    # Bypass record_transaction to put a bad entry in WAL that will fail in shadow.commit
    # We use a custom exception and catch it in sync service
    # To trigger ValueError in Shadow.commit, we can send a duplicate ikey or empty trace_id
    # but we want to test that order-002 is synced and the bad one stays.

    with open(edge.wal_file, "a") as f:
        f.write(json.dumps({
            "event_type": "bad.event",
            "actor_id": actor_id,
            "trace_id": "", # This will trigger ValueError if we enforced it, but we added AUTO.
            "payload": {"idempotency_key": "order-001"} # DUPLICATE IKEY!
        }) + "\n")

    edge.toggle_online(True)
    sync_res_fail = apollo.sync_node()
    assert sync_res_fail['status'] == "FAILED"
    assert sync_res_fail['synced_before_failure'] == 1 # order-002 synced
    assert len(edge.get_pending_sync()) == 1 # bad entry remains in WAL
    print("    ✔ Partial sync failure handled (Rollback/Stop).")

    print("-" * 50)
    print("✅ HARDENED VERIFICATION SUITE PASSED")

if __name__ == "__main__":
    run_hardened_tests()

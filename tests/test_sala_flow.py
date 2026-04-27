import os
import sys
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.core.shadow.service import ShadowSovereignLedger
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.fce.service import FCESovereignService
from mnos.exec.upos.engine import UPOSEngine
from mnos.cloud.edge.node import EdgeNode
from mnos.cloud.apollo.sync import ApolloSyncService
from mnos.shared.execution_guard import ExecutionGuard

def run_test_scenario():
    print("🧪 RUNNING FULL POS FLOW SCENARIO")
    print("-" * 40)

    os.environ["NEXGEN_SECRET"] = "test-secret"

    # 1. Setup
    shadow = ShadowSovereignLedger()
    events = DistributedEventBus()
    # Mock guard for shadow commit (which requires auth)
    # Actually our ShadowSovereignLedger doesn't enforce guard yet, but modules might
    identity = AegisIdentityCore(shadow, events)
    fce = FCESovereignService()
    upos = UPOSEngine(fce, shadow, events)
    edge = EdgeNode(node_id="SALA-01")
    apollo = ApolloSyncService(edge, shadow)

    # Pre-authorize for testing
    from mnos.shared.execution_guard import _sovereign_context
    _sovereign_context.set({"token": "test-token", "actor": {"identity_id": "test-actor"}})

    # 2. LOGIN (Create Identity)
    print("[1] Creating Identity...")
    actor_id = identity.create_profile({"full_name": "Test User", "profile_type": "merchant"})
    print(f"    ✔ Actor ID: {actor_id}")

    # 3. CREATE ORDER (Online)
    print("[2] Creating Online Order...")
    order = upos.create_order("MERC-01", actor_id, [{"id": "item-1", "qty": 1}], 1000.0)
    # Expected: 1000 + 100 (SC) = 1100. 1100 * 0.08 = 88. Total = 1188.
    print(f"    ✔ Order Total: {order['pricing']['total']}")
    assert order['pricing']['total'] == 1188.0

    # 4. DISCONNECT NETWORK
    print("[3] Simulating Network Failure...")
    edge.toggle_online(False)

    # 5. CREATE ORDER (Offline)
    print("[4] Creating Offline Order...")
    tx_offline = {
        "event_type": "upos.order.completed",
        "actor_id": actor_id,
        "payload": {
            "merchant_id": "MERC-01",
            "items": [{"id": "item-2", "qty": 1}],
            "amount": 2000.0
        }
    }
    res = edge.record_transaction(tx_offline)
    print(f"    ✔ Offline Result: {res['status']}")
    assert res['status'] == "QUEUED_OFFLINE"

    # 6. RECONNECT & SYNC
    print("[5] Reconnecting & Syncing...")
    edge.toggle_online(True)
    sync_res = apollo.sync_node()
    print(f"    ✔ Sync Result: {sync_res['status']} (Synced: {sync_res['synced']})")
    assert sync_res['synced'] == 1

    # 7. VERIFY SHADOW
    print("[6] Verifying SHADOW Integrity...")
    is_valid = shadow.verify_integrity()
    print(f"    ✔ Shadow Valid: {is_valid}")
    assert is_valid == True
    print(f"    ✔ Chain Length: {len(shadow.chain)}")

    print("-" * 40)
    print("✅ SCENARIO PASSED")

if __name__ == "__main__":
    run_test_scenario()

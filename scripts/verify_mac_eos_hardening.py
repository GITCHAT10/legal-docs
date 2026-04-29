import hashlib
import json
from mnos.modules.finance.fce import FCEEngine
from mnos.modules.shadow.ledger import ShadowLedger, SecurityAuditError
from mnos.modules.events.bus import DistributedEventBus
from mnos.core.aegis_identity.identity import AegisIdentityCore
from mnos.modules.imoxon.policies.engine import IdentityPolicyEngine
from mnos.shared.execution_guard import ExecutionGuard, _sovereign_context
from mnos.modules.imoxon.core.engine import ImoxonCore
from mnos.modules.education.engine import EducationEngine
from mnos.modules.education.sync import AcademySyncEngine
from mnos.modules.education.content import AirMovieContentManager

def verify_hardening():
    print("--- MAC EOS HARDENING VERIFICATION ---")

    # Setup
    shadow = ShadowLedger()
    events = DistributedEventBus()
    identity = AegisIdentityCore(shadow, events)
    guard = ExecutionGuard(identity, IdentityPolicyEngine(identity), FCEEngine(), shadow, events)
    imoxon = ImoxonCore(guard, FCEEngine(), shadow, events)
    edu = EducationEngine(imoxon)
    sync_engine = AcademySyncEngine(imoxon, edu)
    content = AirMovieContentManager(imoxon)

    # 1. Test Semantic Version Sorting (1.10.0 > 1.9.0)
    print("\n[1] Testing Semantic Version Sorting...")
    actor = {"identity_id": "SYSTEM", "device_id": "SRV", "role": "admin", "system_override": True}
    token = _sovereign_context.set({"token": "SEMVER-TEST", "actor": actor})
    try:
        content.publish_module(actor, {"module_id": "SOP-1", "version": "1.9.0", "title": "Old"})
        content.publish_module(actor, {"module_id": "SOP-1", "version": "1.10.0", "title": "New"})
        latest = content.get_latest_version("SOP-1")
        print(f"Latest Version Resolved: {latest['version']}")
        assert latest["version"] == "1.10.0"
    finally:
        _sovereign_context.reset(token)

    # 2. Test Multi-Node Sync Collision
    print("\n[2] Testing Multi-Node Sync Collision (Namespacing)...")
    event_data = {"score": 90}
    event_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()

    batch_1 = [{"id": "LOCAL-EVT-1", "action_type": "edu.test", "actor_ctx": actor, "data": event_data, "hash": event_hash}]
    batch_2 = [{"id": "LOCAL-EVT-1", "action_type": "edu.test", "actor_ctx": actor, "data": event_data, "hash": event_hash}]

    res1 = sync_engine.process_edge_sync("NODE-A", batch_1)
    res2 = sync_engine.process_edge_sync("NODE-B", batch_2)

    print(f"NODE-A Sync Status: {res1[0]['status']}")
    print(f"NODE-B Sync Status: {res2[0]['status']}")
    assert res1[0]["status"] == "SYNCED"
    assert res2[0]["status"] == "SYNCED" # Should BOTH pass because of node namespacing

    # 3. Test Missing Edge Node ID Rejection
    print("\n[3] Testing Missing Edge Node ID Rejection...")
    res3 = sync_engine.process_edge_sync(None, batch_1)
    print(f"Missing ID Sync Result: {res3[0]['reason']}")
    assert res3[0]["reason"] == "INVALID_EDGE_NODE_ID"

    # 4. Test Unauthorized Ledger Bypass
    print("\n[4] Testing Unauthorized Ledger Bypass...")
    try:
        # Attempting identity write WITHOUT sovereign context
        _sovereign_context.set(None)
        shadow.commit("identity.created", "FRAUD", {"name": "Hacker"})
        print("FAILED: Unauthorized bypass allowed!")
    except SecurityAuditError as e:
        print(f"SUCCESS: Unauthorized bypass blocked: {e}")
    except Exception as e:
        print(f"SUCCESS: Blocked with {type(e).__name__}: {e}")

    print("\n--- Hardening Verification Complete ---")

if __name__ == "__main__":
    verify_hardening()

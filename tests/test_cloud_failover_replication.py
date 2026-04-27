import pytest
import time
from mnos.cloud.apollo.heartbeat import HeartbeatMonitor
from mnos.cloud.apollo.replication import ApolloReplicationQueue
from mnos.cloud.apollo.failover import FailoverOrchestrator
from mnos.cloud.apollo.reconcile import ShadowReconciler
from mnos.cloud.api_fabric.router import FabricRouter
from mnos.modules.shadow.ledger import ShadowLedger

class MockOrca:
    def __init__(self):
        self.events = []
    def record_failover(self, event):
        self.events.append(event)

class MockFce:
    def __init__(self):
        self.locked = False
    def lock_settlement(self, reason):
        self.locked = True

def test_heartbeat_loss_triggers_failover():
    monitor = HeartbeatMonitor(threshold_seconds=0.1)
    shadow = ShadowLedger()
    orca = MockOrca()
    orchestrator = FailoverOrchestrator(monitor, shadow, orca)

    node_id = "EDGE-SALA"
    monitor.record_heartbeat(node_id, latency_ms=10)

    # 1. Healthy
    assert monitor.get_node_health(node_id) == "ONLINE"

    # 2. Loss
    time.sleep(0.2)
    assert monitor.get_node_health(node_id) == "OFFLINE"

    # 3. Trigger failover (requires shadow match)
    res = orchestrator.trigger_failover(node_id, remote_shadow_hash=shadow.genesis_hash)
    assert res["status"] == "ACTIVE_FAILOVER"
    assert orchestrator.is_promoted is True
    assert len(orca.events) == 1

def test_tampered_delta_rejected():
    shadow = ShadowLedger()
    queue = ApolloReplicationQueue(shadow, None)

    # Missing signature
    bad_delta = {"trace_id": "T1", "payload": {}}
    with pytest.raises(PermissionError, match="Missing signature"):
        queue.receive_delta(bad_delta, "MALE-CORE-01")

def test_shadow_hash_mismatch_blocks_promotion():
    monitor = HeartbeatMonitor()
    shadow = ShadowLedger()
    orca = MockOrca()
    orchestrator = FailoverOrchestrator(monitor, shadow, orca)

    with pytest.raises(PermissionError, match="hash mismatch"):
        orchestrator.trigger_failover("NODE-X", remote_shadow_hash="CORRUPT_HASH")

def test_duplicate_trace_id_idempotent():
    shadow = ShadowLedger()
    queue = ApolloReplicationQueue(shadow, None)

    delta = {"trace_id": "STABLE-TX-01", "signature": "SIG-OK", "payload": {}}

    res1 = queue.receive_delta(delta, "MALE-CORE-01")
    res2 = queue.receive_delta(delta, "MALE-CORE-01")

    assert res1 == "QUEUED_INBOX"
    assert res2 == "ALREADY_PROCESSED"
    assert len(queue.inbox) == 1

def test_offline_queue_replay_after_reconnect():
    shadow = ShadowLedger()
    queue = ApolloReplicationQueue(shadow, None)

    delta = {"trace_id": "STABLE-TX-02", "signature": "SIG-OK", "payload": {}}
    queue.offline_queue.append(delta)

    replayed_count = queue.handle_reconnect()
    assert replayed_count == 1
    assert len(queue.inbox) == 1
    assert len(queue.offline_queue) == 0

def test_unknown_node_replication_denied():
    from mnos.cloud.topology import AigAirCloudTopology
    shadow = ShadowLedger()
    topology = AigAirCloudTopology()
    queue = ApolloReplicationQueue(shadow, None, topology)

    delta = {"trace_id": "T1", "signature": "SIG-OK", "payload": {}}

    with pytest.raises(PermissionError, match="unknown node"):
        queue.receive_delta(delta, source_node_id="MALICIOUS-NODE")

def test_financial_lock_on_reconcile_mismatch():
    shadow = ShadowLedger()
    fce = MockFce()
    reconciler = ShadowReconciler(shadow, fce)

    # Add a block
    from mnos.shared.execution_guard import ExecutionGuard
    with ExecutionGuard.sovereign_context(trace_id="T1"):
        shadow.commit("EVENT", "U1", {"data": "ok"})

    # Reconcile with mismatch
    remote_summary = [{"index": 0, "hash": "WRONG_HASH"}]
    reconciler.reconcile_with_remote("NODE-REMOTE", remote_summary)

    assert fce.locked is True
    assert len(reconciler.conflicts) == 1

import pytest
from mnos.modules.shadow_sync.service import sync_agent
from mnos.modules.shadow_sync.db_mirror import db_mirror
from mnos.core.resilience.sentinel import sentinel
from mnos.shared.execution_guard import guard
from mnos.core.security.aegis import aegis

@pytest.fixture
def valid_session():
    payload = {"device_id": "nexus-admin-01", "biometric_verified": True}
    sig = aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def valid_connection():
    return {"is_vpn": True, "tunnel_id": "tun-001", "encryption": "wireguard"}

def test_shadow_sync_flow(valid_session, valid_connection):
    """
    Simulates:
    1. Normal operation (cloud active)
    2. Trigger "CABLE_CUT"
    3. Promote local DB
    4. Perform transactions locally
    5. Restore connection
    6. Reconcile to cloud
    """

    # 1. Normal Operation (Cloud CDC to local mirror)
    sync_agent.process_cdc_event("identity", "INSERT", {"id": "U-001", "name": "Ahmed"})
    assert db_mirror.data["identity"]["U-001"]["name"] == "Ahmed"
    assert db_mirror.is_primary is False

    # 2 & 3. Trigger Failover (CABLE_CUT + Promotion)
    sentinel.trigger_failover("CABLE_CUT", valid_session)
    assert db_mirror.is_primary is True
    assert sentinel.cloud_reachable is False

    # 4. Perform local transaction
    def local_action(p):
        db_mirror.write_local("transactions", {"id": "TX-99", "amount": 500})
        return "SUCCESS"

    res = guard.execute_sovereign_action(
        "nexus.payment.received",
        {},
        valid_session,
        local_action,
        connection_context=valid_connection
    )

    assert res == "SUCCESS"
    assert db_mirror.data["transactions"]["TX-99"]["amount"] == 500
    assert len(sync_agent.local_queue) == 1

    # 5 & 6. Restore Connection + Reconciliation
    sentinel.restore_connection()
    assert sentinel.cloud_reachable is True
    assert db_mirror.is_primary is False
    assert len(sync_agent.local_queue) == 0 # Should be cleared after reconciliation

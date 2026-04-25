import pytest
import time
from mnos.shared.guard.service import guard
from mnos.core.aig_aegis.service import aig_aegis

def test_guard_enforces_full_stack():
    session = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": "guard-test-nonce",
        "timestamp": int(time.time()),
        "mission_scope": "V1"
    }
    session["signature"] = aig_aegis.sign_session(session)

    connection = {
        "is_vpn": True,
        "tunnel": "aig_tunnel",
        "encryption": "wireguard",
        "tunnel_id": "tun-01",
        "source_ip": "10.0.0.1",
        "node_id": "SALA-EDGE-01"
    }

    # Valid call
    def logic(p): return "SUCCESS"
    res = guard.execute_sovereign_action(
        "test",
        {},
        session,
        logic,
        connection_context=connection,
        tenant="MIG-GENESIS"
    )
    assert res == "SUCCESS"

def test_guard_blocks_no_vpn():
    session = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": "guard-no-vpn",
        "timestamp": int(time.time())
    }
    session["signature"] = aig_aegis.sign_session(session)

    with pytest.raises(Exception): # NetworkSecurityException or similar
        guard.execute_sovereign_action("test", {}, session, lambda p: "OK", tenant="MIG-GENESIS")

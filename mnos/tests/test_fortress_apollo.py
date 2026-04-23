import pytest
import time
from mnos.core.apollo.deployment import apollo_deploy
from mnos.core.apollo.override import sovereign_override
from mnos.core.aig_aegis.service import aig_aegis

@pytest.fixture
def admin_session():
    s = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": str(time.time()),
        "timestamp": int(time.time())
    }
    s["signature"] = aig_aegis.sign_session(s)
    return s

@pytest.fixture
def valid_connection():
    return {
        "is_vpn": True,
        "tunnel": "aig_tunnel",
        "encryption": "wireguard",
        "tunnel_id": "tun-01",
        "source_ip": "10.0.0.1",
        "node_id": "SALA-EDGE-01"
    }

def test_apollo_tiered_deployment(admin_session, valid_connection):
    # Success: LAB to PILOT
    attestation = {
        "artifact_hash_match": True,
        "guard_proof_report": True
    }
    res = apollo_deploy.deploy("hash123", "PILOT", admin_session, attestation, connection_context=valid_connection)
    assert res["status"] == "DEPLOYED"
    assert apollo_deploy.current_state == "PILOT"

    # Failure: Jump to ELITE
    admin_session["nonce"] = "new-nonce-1"
    admin_session["signature"] = aig_aegis.sign_session(admin_session)
    with pytest.raises(RuntimeError, match="Illegal tier jump"):
        apollo_deploy.deploy("hash123", "ELITE", admin_session, attestation, connection_context=valid_connection)

def test_sovereign_override(admin_session, valid_connection):
    res = sovereign_override.authorize(
        "MIG-COMMAND-AUTHORITY-ROOT",
        "LOCAL-GOV-CERTIFIED-OVERRIDE",
        admin_session,
        connection_context=valid_connection
    )
    assert res == "SYSTEM_UNLOCK_AUTHORIZED"

def test_sovereign_override_rejection(admin_session, valid_connection):
    admin_session["nonce"] = "override-reject-nonce"
    admin_session["signature"] = aig_aegis.sign_session(admin_session)
    with pytest.raises(Exception, match="OVERRIDE: MIG Command signature invalid"):
        sovereign_override.authorize(
            "BAD-SIG",
            "LOCAL-GOV-CERTIFIED-OVERRIDE",
            admin_session,
            connection_context=valid_connection
        )

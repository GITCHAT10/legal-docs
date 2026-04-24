import pytest
import time
import uuid
from mnos.modules.nexus_skyi.client.imoxon_client import imoxon_client
from mnos.modules.imoxon.api_gateway import imoxon_airlock
from mnos.core.aig_aegis.service import aig_aegis
from mnos.modules.aig_shadow.service import aig_shadow

@pytest.fixture
def hms_session():
    payload = {
        "device_id": "nexus-admin-01",
        "biometric_verified": True,
        "nonce": str(time.time()),
        "timestamp": int(time.time()),
        "mission_scope": "V1"
    }
    payload["signature"] = aig_aegis.sign_session(payload)
    return payload

@pytest.fixture
def orban_conn():
    return {
        "is_vpn": True,
        "tunnel": "aig_tunnel",
        "encryption": "wireguard",
        "tunnel_id": "MIG-HMS-01",
        "source_ip": "10.0.0.1",
        "node_id": "SALA-EDGE-01"
    }

def test_hms_get_quotes(hms_session, orban_conn):
    """Test 1: HMS pulls GET /quotes from iMOXON"""
    res = imoxon_client.get_quotes(hms_session, orban_conn)
    assert res["status"] == "SUCCESS"
    assert len(res["quotes"]) > 0

def test_hms_send_rfq(hms_session, orban_conn):
    """Test 2: HMS sends POST /rfq to iMOXON"""
    res = imoxon_client.create_rfq("P-DETERGENT", 100, hms_session, orban_conn)
    assert res["status"] == "AUTHORIZED"

def test_unauthorized_scope_blocked(hms_session, orban_conn):
    """Test 3: HMS tries vendor scope and is blocked"""
    request = {
        "node_id": "hms-resort-01",
        "timestamp": int(time.time()),
        "nonce": "nonce-illegal-scope",
        "scope": "vendor:payout",
        "trace_id": str(uuid.uuid4())
    }
    res = imoxon_airlock.process_request(request, "sig:hms")
    assert res["status"] == "BLOCKED"
    assert "denied" in res["reason"]

def test_replayed_nonce_rejected():
    """Test 4: Replayed nonce is rejected"""
    nonce = "fixed-nonce-123"
    request = {
        "node_id": "hms-resort-01",
        "timestamp": int(time.time()),
        "nonce": nonce,
        "scope": "quotes:read",
        "trace_id": str(uuid.uuid4())
    }
    imoxon_airlock.process_request(request, "sig:valid")
    res = imoxon_airlock.process_request(request, "sig:valid")
    assert res["status"] == "BLOCKED"
    assert "Replayed nonce" in res["reason"]

def test_expired_timestamp_rejected():
    """Test 5: Expired timestamp is rejected"""
    request = {
        "node_id": "hms-resort-01",
        "timestamp": int(time.time()) - 100,
        "nonce": "nonce-expired",
        "scope": "quotes:read",
        "trace_id": str(uuid.uuid4())
    }
    res = imoxon_airlock.process_request(request, "sig:valid")
    assert res["status"] == "BLOCKED"
    assert "expired" in res["reason"]

def test_invalid_signature_rejected():
    """Test 6: Invalid signature is rejected"""
    request = {
        "node_id": "hms-resort-01",
        "timestamp": int(time.time()),
        "nonce": "nonce-bad-sig",
        "scope": "quotes:read",
        "trace_id": str(uuid.uuid4())
    }
    res = imoxon_airlock.process_request(request, "sig:invalid_data")
    assert res["status"] == "BLOCKED"
    assert "Invalid Ed25519 signature" in res["reason"]

def test_shadow_audit_logging():
    """Test 7 & 8: Verify shadow logging and data sovereignty"""
    initial_chain_len = len(aig_shadow.chain)

    request = {
        "node_id": "hms-resort-01",
        "timestamp": int(time.time()),
        "nonce": "nonce-audit-test",
        "scope": "quotes:read",
        "trace_id": "TRACE-GUEST-SOVEREIGN"
    }
    imoxon_airlock.process_request(request, "sig:valid")

    # Check shadow
    latest = aig_shadow.chain[-1]
    assert latest["event_type"] == "airlock.request_accepted"
    assert latest["payload"]["data"]["input"]["airlock_trace"] == "TRACE-GUEST-SOVEREIGN"

    # Sovereignty: Ensure no guest names in shadow log from this trace
    log_dump = str(latest["payload"])
    assert "Ahmed" not in log_dump
    assert "Guest" not in log_dump

def test_latency_measurement(hms_session, orban_conn):
    """Test 10: Latency test for same-cloud bridge"""
    start = time.perf_counter()
    imoxon_client.get_quotes(hms_session, orban_conn)
    latency_ms = (time.perf_counter() - start) * 1000
    print(f"\n[LATENCY] Same-Cloud Bridge: {latency_ms:.2f}ms")
    assert latency_ms < 50 # Cloud environment target

import pytest
import os
from mnos.modules.cloud_engine.service import cloud_engine
from mnos.core.aig_aegis.service import aig_aegis
from mnos.core.aig_tunnel.service import NetworkSecurityException
from mnos.core.aig_aegis.service import SecurityException
from mnos.core.aig_l5_control.service import GovernanceException
from mnos.modules.aig_vault.service import VaultException

# Mock environment for tests
os.environ["NEXGEN_SECRET"] = "test-secret-12345"

@pytest.fixture
def valid_session():
    payload = {"device_id": "nexus-admin-01", "biometric_verified": True}
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def valid_connection():
    return {
        "is_vpn": True,
        "tunnel_id": "tun-001",
        "encryption": "wireguard",
        "tunnel": "aig_tunnel",
        "source_ip": "10.0.0.1",
        "node_id": "CLOUD-01"
    }

@pytest.fixture
def valid_governance():
    return {"reason": "Maintenance", "timestamp": "2026-04-22T12:00:00Z", "confirmed": True}

def test_full_security_stack_success(valid_session, valid_connection, valid_governance):
    """Verifies that a request with all 5 layers correct succeeds."""
    result = cloud_engine.execute_critical_operation(
        operation_name="network_routing_change",
        params={"route": "10.0.0.1/24"},
        session_context=valid_session,
        connection_context=valid_connection,
        evidence=valid_governance,
        approvals=["nexus-admin-01"]
    )

    assert result["status"] == "SUCCESS"

def test_missing_vpn_fails(valid_session, valid_governance):
    """Layer 1: Network Security check."""
    with pytest.raises(NetworkSecurityException, match="AIG_TUNNEL: Public access blocked"):
        cloud_engine.execute_critical_operation(
            operation_name="network_routing_change",
            params={},
            session_context=valid_session,
            connection_context={"is_vpn": False},
            evidence=valid_governance,
            approvals=["admin"]
        )

def test_missing_biometric_fails(valid_connection, valid_governance):
    """Layer 4: Identity Security check (Biometric)."""
    payload = {"device_id": "nexus-admin-01", "biometric_verified": False}
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig

    with pytest.raises(SecurityException, match="AIGAegis: Biometric verification required"):
        cloud_engine.execute_critical_operation(
            operation_name="network_routing_change",
            params={},
            session_context=payload,
            connection_context=valid_connection,
            evidence=valid_governance,
            approvals=["admin"]
        )

def test_aig_l5_governance_failure(valid_session, valid_connection):
    """Layer 3: Governance Security check (AIGL5Control)."""
    with pytest.raises(GovernanceException, match="L5: Critical action .* requires formal evidence"):
        cloud_engine.execute_critical_operation(
            operation_name="system_shutdown",
            params={},
            session_context=valid_session,
            connection_context=valid_connection,
            evidence={}, # Missing evidence
            approvals=[]
        )

def test_aig_vault_permission_failure(valid_connection):
    """Layer 2: Data Security check (AIGVault Vault)."""
    # Guest session (no write permission)
    payload = {"device_id": "nexus-001", "biometric_verified": True}
    # nexus-001 is trusted in Registry but not given write in aig_vault mock permissions in service.py
    # Wait, in aig_vault mock, nexus-admin has write, nexus-guest has read.
    # mnos.core.aig_aegis.service.py TrustedDeviceRegistry has {"nexus-001", "nexus-admin-01"}

    # Let's use nexus-001 which is trusted device but not in aig_vault's admin list
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig

    with pytest.raises(VaultException, match="AIG_VAULT: Identity 'nexus-001' denied 'write' access"):
        cloud_engine.store_sovereign_data(
            file_id="top-secret.doc",
            data="...",
            session_context=payload,
            connection_context=valid_connection
        )

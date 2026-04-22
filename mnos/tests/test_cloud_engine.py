import pytest
import os
from mnos.modules.cloud_engine.service import cloud_engine
from mnos.core.security.aegis import aegis
from mnos.core.network.orban import NetworkSecurityException
from mnos.core.security.aegis import SecurityException
from mnos.core.governance.l5 import GovernanceException
from mnos.modules.ucloud.service import VaultException

# Mock environment for tests
os.environ["NEXGEN_SECRET"] = "test-secret-12345"

@pytest.fixture
def valid_session():
    payload = {"device_id": "nexus-admin-01", "biometric_verified": True}
    sig = aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def valid_connection():
    return {
        "is_vpn": True,
        "tunnel_id": "tun-001",
        "encryption": "wireguard",
        "tunnel": "orban",
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
    with pytest.raises(NetworkSecurityException, match="ORBAN: Public access blocked"):
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
    sig = aegis.sign_session(payload)
    payload["signature"] = sig

    with pytest.raises(SecurityException, match="AEGIS: Biometric verification required"):
        cloud_engine.execute_critical_operation(
            operation_name="network_routing_change",
            params={},
            session_context=payload,
            connection_context=valid_connection,
            evidence=valid_governance,
            approvals=["admin"]
        )

def test_l5_governance_failure(valid_session, valid_connection):
    """Layer 3: Governance Security check (L5 Safe-Firing)."""
    with pytest.raises(GovernanceException, match="L5: Critical action .* requires formal evidence"):
        cloud_engine.execute_critical_operation(
            operation_name="system_shutdown",
            params={},
            session_context=valid_session,
            connection_context=valid_connection,
            evidence={}, # Missing evidence
            approvals=[]
        )

def test_ucloud_permission_failure(valid_connection):
    """Layer 2: Data Security check (uCloud Vault)."""
    # Guest session (no write permission)
    payload = {"device_id": "nexus-001", "biometric_verified": True}
    # nexus-001 is trusted in Registry but not given write in ucloud mock permissions in service.py
    # Wait, in ucloud mock, nexus-admin has write, nexus-guest has read.
    # mnos/core/security/aegis.py TrustedDeviceRegistry has {"nexus-001", "nexus-admin-01"}

    # Let's use nexus-001 which is trusted device but not in ucloud's admin list
    sig = aegis.sign_session(payload)
    payload["signature"] = sig

    with pytest.raises(VaultException, match="UCLOUD: Identity 'nexus-001' denied 'write' access"):
        cloud_engine.store_sovereign_data(
            file_id="top-secret.doc",
            data="...",
            session_context=payload,
            connection_context=valid_connection
        )

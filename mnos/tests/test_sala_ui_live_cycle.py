import pytest
from mnos.interface.sala_os.cockpit.service import cockpit_service
from mnos.interface.sala_os.guest_profile.service import guest_profile_service
from mnos.interface.sala_os.arrival_radar.service import arrival_radar_service
from mnos.shared.guard.service import guard
from mnos.core.aig_aegis.service import aig_aegis

@pytest.fixture
def v1_session():
    # Valid V1 mission session
    payload = {"device_id": "nexus-admin-01", "biometric_verified": True, "mission_scope": "V1"}
    sig = aig_aegis.sign_session(payload)
    payload["signature"] = sig
    return payload

@pytest.fixture
def valid_connection():
    return {
        "is_vpn": True,
        "tunnel_id": "sala-cockpit-01",
        "encryption": "wireguard",
        "tunnel": "aig_tunnel",
        "source_ip": "10.0.0.100",
        "node_id": "SALA-EDGE-01"
    }

def test_sala_ui_live_cycle(v1_session, valid_connection):
    """
    Scenario:
    1. Cockpit WebSocket stream connect
    2. Arrival Radar check
    3. Guest Profile load
    4. Guarded UI action (Finalize Invoice)
    """
    # 1. Connect Stream
    res_conn = cockpit_service.connect_stream("live_folio", v1_session, valid_connection)
    assert res_conn["status"] == "CONNECTED"

    # 2. Arrival Radar view
    radar_view = arrival_radar_service.get_radar_view(v1_session)
    assert len(radar_view) > 0
    assert radar_view[0]["linked_guest"] == "Test Guest"

    # 3. Guest Profile Access
    profile = guest_profile_service.load_profile("G-001", v1_session, valid_connection)
    assert profile["mode"] == "ENCRYPTED_READ"

    # 4. Law of the Button: Finalize Invoice
    def finalize_logic(p): return {"status": "FINALIZED", "total": "500.00"}

    res_action = guard.execute_sovereign_action(
        "sala.invoice.finalized",
        {"folio_id": "F-101"},
        v1_session,
        finalize_logic,
        connection_context=valid_connection,
        tenant="MIG-GENESIS",
        mission_scope="V1"
    )

    assert res_action["status"] == "FINALIZED"

import pytest
from unified_suite.core.patente import NexGenPatenteVerifier
from unified_suite.tax_engine.calculator import MoatsTaxCalculator
from unified_suite.airports.service import AirportService
from unified_suite.airports.models import Flight
from unified_suite.seaports.service import SeaPortService
from unified_suite.seaports.models import Vessel, Container
from datetime import datetime

def test_patente_auth(monkeypatch):
    import hmac
    import hashlib
    secret = "test_secret"
    monkeypatch.setenv("NEXGEN_SECRET", secret)

    def make_token(eid):
        sig = hmac.new(secret.encode(), eid.encode(), hashlib.sha256).hexdigest()
        return f"{eid}:{sig}"

    admin_token = make_token("ADMIN_001")
    flgt_token = make_token("FLGT_123")

    # Test valid token
    assert NexGenPatenteVerifier.authorize_access(admin_token, "ADMIN_001", "ADMIN") is True

    # Test invalid token signature
    with pytest.raises(PermissionError, match="Invalid patente token signature"):
        NexGenPatenteVerifier.authorize_access("ADMIN_001:wrong_sig", "ADMIN_001", "ADMIN")

    # Test missing token
    with pytest.raises(PermissionError, match="Missing patente token"):
        NexGenPatenteVerifier.authorize_access(None, "ADMIN_001", "ADMIN")

    # Test Binding Violation
    with pytest.raises(PermissionError, match="not bound to entity ATTACKER"):
        NexGenPatenteVerifier.authorize_access(flgt_token, "ATTACKER", "AIRPORT_OPS")

    # Test Scope Rejection
    assert NexGenPatenteVerifier.authorize_access(flgt_token, "FLGT_123", "PORT_OPS") is False
    assert NexGenPatenteVerifier.authorize_access(flgt_token, "FLGT_123", "AIRPORT_OPS") is True

def test_moats_tax_logic():
    base = 1000.0
    bill = MoatsTaxCalculator.calculate_bill(base)
    # 1000 + 10% = 1100
    # 1100 + 17% = 1100 + 187 = 1287
    assert bill['service_charge'] == 100.0
    assert bill['subtotal'] == 1100.0
    assert bill['tgst'] == 187.0
    assert bill['total_amount'] == 1287.0
    assert bill['compliance'] == "MIRA_COMPLIANT_V2"

def test_gate_idempotency():
    service = AirportService()
    flight = Flight(
        flight_number="TEST123",
        airline="TestAir",
        origin="AAA",
        destination="BBB",
        arrival_time=datetime.now()
    )
    service.schedule_flight(flight)

    # First call
    gate1 = service.assign_gate(flight)
    assert gate1 is not None

    # Second call
    gate2 = service.assign_gate(flight)
    assert gate1 == gate2

    # Test exhaustion
    service.gates = ["GATE_1"]
    flight2 = Flight(flight_number="F2", airline="A", origin="O", destination="D", arrival_time=datetime.now())
    service.schedule_flight(flight2)
    with pytest.raises(Exception, match="No gates available"):
        service.assign_gate(flight2)

def test_berth_idempotency():
    service = SeaPortService()
    vessel = Vessel(
        vessel_id="V1",
        name="TestVessel",
        origin="CCC",
        arrival_time=datetime.now(),
        containers=[]
    )
    service.register_vessel(vessel)

    # First call
    berth1 = service.assign_berth(vessel)
    assert berth1 is not None

    # Second call
    berth2 = service.assign_berth(vessel)
    assert berth1 == berth2

    # Test exhaustion
    service.berths = ["BERTH_1"]
    vessel2 = Vessel(vessel_id="V2", name="T2", origin="O", arrival_time=datetime.now())
    service.register_vessel(vessel2)
    with pytest.raises(Exception, match="No berths available"):
        service.assign_berth(vessel2)

import pytest
from unified_suite.core.patente import NexGenPatenteVerifier
from unified_suite.tax_engine.calculator import MoatsTaxCalculator
from unified_suite.airports.service import AirportService
from unified_suite.airports.models import Flight
from unified_suite.seaports.service import SeaPortService
from unified_suite.seaports.models import Vessel, Container
from datetime import datetime

def test_nexgen_patente():
    entity_id = "CAPT_TEST"
    patente = NexGenPatenteVerifier.generate_patente(entity_id)
    # Valid auth
    assert NexGenPatenteVerifier.authorize_access(entity_id, patente, "DOCKING_AREA") is True
    # Invalid key
    assert NexGenPatenteVerifier.authorize_access(entity_id, "wrong_key", "DOCKING_AREA") is False
    # Invalid area for entity type
    assert NexGenPatenteVerifier.authorize_access("VESL_01", NexGenPatenteVerifier.generate_patente("VESL_01"), "GATE_AREA") is False

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

def test_airport_service_idempotency():
    service = AirportService()
    flight = Flight(
        flight_number="TEST123",
        airline="TestAir",
        origin="AAA",
        destination="BBB",
        arrival_time=datetime.now()
    )
    service.schedule_flight(flight)
    gate1 = service.assign_gate("TEST123")
    assert gate1 == "GATE_1"

    # IDEMPOTENCY CHECK
    gate2 = service.assign_gate("TEST123")
    assert gate2 == "GATE_1" # Should not change

def test_seaport_service():
    service = SeaPortService()
    vessel = Vessel(
        vessel_id="V1",
        name="TestVessel",
        origin="CCC",
        arrival_time=datetime.now(),
        containers=[Container(container_id="C1", size=20, contents="Stuff", weight=10.0)]
    )
    service.register_vessel(vessel)
    berth = service.assign_berth("V1")
    assert berth == "BERTH_1"
    assert len(service.get_vessel_manifest("V1")) == 1

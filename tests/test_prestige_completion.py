import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date, time
from mnos.modules.prestige.contracts.accommodation_schema import AccommodationContractV2, EstablishmentType, IslandType, MealPlan
from mnos.modules.prestige.contracts.accommodation_quote import AccommodationQuoteEngine
from mnos.modules.prestige.contracts.festive_engine import FestiveEngine
from mnos.modules.prestige.pricing.surcharge_calculator import SurchargeCalculator
from mnos.modules.prestige.logistics.access_point_schema import AccessPoint, AccessPointType
from mnos.modules.prestige.logistics.transfer_villa_sync import TransferVillaSync
from mnos.modules.prestige.forms.uhnw_booking_template import UHNWBookingTemplate
from mnos.modules.prestige.workflows.intake_validation import IntakeValidation
from mnos.modules.prestige.logistics.shadow_checklist import ShadowLogisticsChecklist, ChecklistItem
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard

@pytest.fixture
def shadow():
    return ShadowLedger()

@pytest.fixture
def auth_actor():
    return {"identity_id": "SYS", "device_id": "DEV-01", "role": "admin"}

@pytest.fixture
def accommodation_contract():
    return AccommodationContractV2(
        contract_id=uuid4(), supplier_id=uuid4(), establishment_id=uuid4(),
        establishment_type=EstablishmentType.RESORT, island_type=IslandType.PRIVATE_ISLAND,
        room_count=100, base_rate=Decimal("1000"), effective_from=date(2024,1,1),
        festive_gala_christmas=Decimal("500"), festive_gala_new_year=Decimal("800")
    )

def test_resort_green_tax_2026_is_12(accommodation_contract):
    engine = AccommodationQuoteEngine()
    # 1 adult, 1 night
    tax = engine.calculate_green_tax(accommodation_contract, 1, 0, 1)
    assert tax == Decimal("12.00")

def test_guesthouse_inhabited_50_or_fewer_rooms_green_tax_is_6():
    contract = AccommodationContractV2(
        contract_id=uuid4(), supplier_id=uuid4(), establishment_id=uuid4(),
        establishment_type=EstablishmentType.GUESTHOUSE, island_type=IslandType.INHABITED_LOCAL_ISLAND,
        room_count=20, base_rate=Decimal("100"), effective_from=date(2024,1,1)
    )
    engine = AccommodationQuoteEngine()
    tax = engine.calculate_green_tax(contract, 1, 0, 1)
    assert tax == Decimal("6.00")

def test_guesthouse_ai_becomes_non_alcoholic_ai():
    contract = AccommodationContractV2(
        contract_id=uuid4(), supplier_id=uuid4(), establishment_id=uuid4(),
        establishment_type=EstablishmentType.GUESTHOUSE, island_type=IslandType.INHABITED_LOCAL_ISLAND,
        room_count=20, base_rate=Decimal("100"), effective_from=date(2024,1,1)
    )
    engine = AccommodationQuoteEngine()
    resolved = engine.resolve_meal_plan(contract, MealPlan.AI)
    assert resolved == MealPlan.NON_ALCOHOLIC_AI

def test_christmas_eve_surcharge_applied_if_staying_dec_24(accommodation_contract):
    engine = FestiveEngine()
    stay = [date(2024, 12, 23), date(2024, 12, 24)]
    surcharge = engine.calculate_festive_surcharge(accommodation_contract, stay)
    assert surcharge == Decimal("500")

def test_festive_surcharge_includes_10_percent_service_charge_and_17_percent_tgst():
    calc = SurchargeCalculator()
    res = calc.apply_taxes(Decimal("100.00"))
    # 100 + 10% = 110. 110 * 1.17 = 128.7
    assert res["service_charge"] == 10.0
    assert res["tgst"] == 18.7
    assert res["total"] == 128.7

def test_p4_guest_excludes_main_lobby_routing():
    sync = TransferVillaSync()
    points = [
        AccessPoint(access_point_id="LOBBY", access_point_gps="0,0", access_point_type=AccessPointType.HOTEL_LOBBY, host_meeting_point="Desk"),
        AccessPoint(access_point_id="JETTY", access_point_gps="1,1", access_point_type=AccessPointType.MAIN_JETTY, host_meeting_point="Pier")
    ]
    best = sync.determine_arrival_point("P4", "YACHT", points)
    assert best.access_point_id == "JETTY"

def test_p3_p4_triggers_human_escalation():
    validator = IntakeValidation()
    intake = UHNWBookingTemplate(
        lead_type="Direct", main_contact="Me", travel_dates={"from": date(2024,1,1), "to": date(2024,1,5)},
        adults=2, nationalities=["UK"], arrival_mode="PRIVATE_JET", luggage_details={},
        villa_preference=["Pool"], privacy_level="P4", transfer_preference="Yacht", budget_band="High",
        payment_preference="Wire", private_jet_tail_no="N123", eta=time(10,0)
    )
    assert validator.check_escalation(intake) is True

def test_72h_checklist_starts_before_arrival(shadow, auth_actor):
    checklist = ShadowLogisticsChecklist(shadow)
    with ExecutionGuard.authorized_context(auth_actor):
        checklist.verify_item("BK123", ChecklistItem.GUEST_IDENTITY_VERIFIED, {})
    assert checklist.checklists["BK123"][ChecklistItem.GUEST_IDENTITY_VERIFIED] is True
    assert checklist.is_arrival_ready("BK123") is False # Final seal missing

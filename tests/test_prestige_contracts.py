import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date, time
from mnos.modules.prestige.taxes.airport_fees_engine import AirportFeesEngine
from mnos.modules.prestige.taxes.airport_fees_schema import TravelClass, PassengerResidency
from mnos.modules.prestige.contracts.transfer_quote import UHNWIntake, generate_transfer_quote_preview
from mnos.modules.prestige.contracts.transfer_schema import TransferContract, TransferType, TransferWay, Currency, TaxContext, ContractStatus

@pytest.fixture
def fees_engine():
    return AirportFeesEngine()

def test_dpt_foreign_economy_is_50(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.ECONOMY,
        residency=PassengerResidency.FOREIGN,
        departure_airport="GAN"
    )
    # DPT 50, ADF 0 (Not Velana)
    assert res["total_airport_fees_usd"] == 50.0
    codes = [f["code"] for f in res["breakdown"]]
    assert "DPT" in codes
    assert "ADF" not in codes

def test_dpt_maldivian_economy_is_12(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.ECONOMY,
        residency=PassengerResidency.MALDIVIAN,
        departure_airport="GAN"
    )
    assert res["total_airport_fees_usd"] == 12.0

def test_dpt_business_is_120(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.BUSINESS,
        residency=PassengerResidency.FOREIGN,
        departure_airport="GAN"
    )
    assert res["total_airport_fees_usd"] == 120.0

def test_dpt_first_is_240(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.FIRST,
        residency=PassengerResidency.FOREIGN,
        departure_airport="GAN"
    )
    assert res["total_airport_fees_usd"] == 240.0

def test_dpt_private_jet_is_480(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.PRIVATE_JET,
        residency=PassengerResidency.FOREIGN,
        departure_airport="GAN"
    )
    assert res["total_airport_fees_usd"] == 480.0

def test_adf_applies_only_to_velana(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.ECONOMY,
        residency=PassengerResidency.FOREIGN,
        departure_airport="Velana International Airport"
    )
    # DPT 50 + ADF 50 = 100
    assert res["total_airport_fees_usd"] == 100.0
    codes = [f["code"] for f in res["breakdown"]]
    assert "DPT" in codes
    assert "ADF" in codes

def test_child_under_2_exempt_from_dpt(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.ECONOMY,
        residency=PassengerResidency.FOREIGN,
        departure_airport="GAN",
        is_infant=True
    )
    # DPT exempt
    assert res["total_airport_fees_usd"] == 0.0

def test_direct_transit_exempt_from_adf(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.ECONOMY,
        residency=PassengerResidency.FOREIGN,
        departure_airport="Velana International Airport",
        is_direct_transit=True
    )
    # ADF exempt, DPT still applies (unless it's general transit)
    # In my engine, direct_transit exempts ADF.
    assert res["total_airport_fees_usd"] == 50.0
    codes = [f["code"] for f in res["breakdown"]]
    assert "DPT" in codes
    assert "ADF" not in codes

def test_diplomatic_immunity_exempt_from_dpt_and_adf(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.PRIVATE_JET,
        residency=PassengerResidency.FOREIGN,
        departure_airport="Velana International Airport",
        is_diplomat=True
    )
    assert res["total_airport_fees_usd"] == 0.0

def test_airport_fees_are_pass_through_not_margin(fees_engine):
    res = fees_engine.calculate_airport_fees(
        travel_class=TravelClass.ECONOMY,
        residency=PassengerResidency.FOREIGN,
        departure_airport="GAN"
    )
    assert res["is_statutory_pass_through"] is True
    assert res["is_prestige_margin"] is False

def test_missing_travel_class_fails_closed(fees_engine):
    with pytest.raises(ValueError, match="FAIL CLOSED"):
        fees_engine.calculate_airport_fees(None, PassengerResidency.FOREIGN, "GAN")

@pytest.fixture
def sample_contract():
    return TransferContract(
        transfer_contract_id=uuid4(),
        supplier_id=uuid4(),
        carrier_name="Trans Maldivian",
        sector="MLE-Noku",
        route_from="MLE",
        route_to="Noku",
        transfer_type=TransferType.SEAPLANE,
        one_way_or_return=TransferWay.RETURN,
        adult_rate=Decimal("450.00"),
        child_rate=Decimal("250.00"),
        infant_rate=Decimal("0.00"),
        currency=Currency.USD,
        tax_context=TaxContext.TOURISM_STANDARD,
        applicable_taxes={},
        baggage_allowance_kg=20,
        hand_luggage_kg=5,
        excess_baggage_rate=Decimal("5.00"),
        fuel_surcharge_rule={"fuel_supplement_pct": 0.1},
        cancellation_rule={"within_24h": 1.0, "within_72h": 0.5},
        refund_rule={},
        credit_terms={},
        manifest_deadline_hours=72,
        ticketing_deadline_hours=96,
        free_cancel_deadline_hours=120,
        late_cancel_fee=Decimal("100.00"),
        effective_from=date(2024, 1, 1),
        effective_to=date(2025, 1, 1),
        status=ContractStatus.ACTIVE
    )

def test_airport_fee_breakdown_in_quote_preview(sample_contract):
    intake = UHNWIntake(
        guest_count_adult=2,
        guest_count_child=0,
        guest_count_infant=0,
        estimated_baggage_kg=40,
        arrival_airport="Velana International Airport",
        arrival_date=date(2024, 12, 10),
        arrival_time=time(10, 0),
        resort_id="Noku",
        destination_atoll="Noonu",
        preferred_transfer_mode="seaplane",
        privacy_level="high",
        travel_class=TravelClass.BUSINESS,
        passenger_residency=PassengerResidency.FOREIGN
    )

    quote = generate_transfer_quote_preview(intake, sample_contract)

    # Carrier: 2 * 450 = 900. Fuel 10% = 90. Total 990.
    # Fees: DPT 120 + ADF 120 = 240.
    # Quote Total: 990 + 240 = 1230.

    assert quote.total_estimated_cost == Decimal("1230.00")
    assert quote.airport_fee_breakdown["total_airport_fees_usd"] == 240.0
    assert quote.status == "PREVIEW_ONLY"
    assert quote.confirmed_ticket is False

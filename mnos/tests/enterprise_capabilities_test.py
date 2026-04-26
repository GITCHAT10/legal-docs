import pytest
from decimal import Decimal
from mnos.modules.ontology.models import GuestBioProfile, CorporateBioTwin
from mnos.modules.fce.service import fce
from mnos.modules.fce.pricing_engine import pricing_engine

def test_guest_bio_profile_creation():
    """Verify GuestBioProfile model integrity."""
    profile = GuestBioProfile(
        guest_id="G-UNIT",
        hrv_baseline=75.0,
        sleep_efficiency=0.92,
        cortisol_index=0.15,
        regen_score=85.0,
        is_eco_sovereign=True
    )
    assert profile.guest_id == "G-UNIT"
    assert profile.is_eco_sovereign is True
    assert profile.regen_score == 85.0

def test_corporate_bio_twin_creation():
    """Verify CorporateBioTwin model integrity."""
    twin = CorporateBioTwin(
        corporate_id="CORP-X",
        employee_count=500,
        collective_recovered_hours=1250.5
    )
    assert twin.corporate_id == "CORP-X"
    assert twin.collective_recovered_hours == 1250.5

def test_biological_roi_calculation():
    """Verify Pricing Engine logic for Biological ROI."""
    # 1. Recovered Hour Fee: 10 hours @ $50/hr = $500
    fee = pricing_engine.calculate_recovered_hour_fee(10, Decimal("50.00"))
    assert fee == Decimal("500.00")

    # 2. Longevity Dividend: 5 days @ $100/day = $500
    dividend = pricing_engine.calculate_longevity_dividend(5, Decimal("100.00"))
    assert dividend == Decimal("500.00")

    # 3. ESG Regen Premium: 90 score on $1000 base
    # (90-80)/20 * 0.10 + 0.05 = 0.5 * 0.10 + 0.05 = 0.10 (10%)
    # $1000 * 0.10 = $100
    premium = pricing_engine.calculate_esg_regen_premium(90.0, Decimal("1000.00"))
    assert premium == Decimal("100.00")

def test_fce_integration_with_biological_outcomes():
    """Verify FCE calculate_folio correctly incorporates biological outcomes."""
    base_price = Decimal("1000.00")
    outcomes = {
        "recovered_hours": 10,
        "recovered_hour_rate": Decimal("50.00"), # $500
        "healthspan_gain_days": 2,
        "longevity_dividend_rate": Decimal("250.00"), # $500
        "regen_score": 100 # (100-80)/20 * 0.1 + 0.05 = 0.15 premium ($150)
    }

    # Expected outcome_fees = 500 + 500 + 150 = 1150
    # Expected subtotal = 1000 + 1150 = 2150
    # Expected SC = 2150 * 0.1 = 215
    # Expected Taxable = 2150 + 215 = 2365
    # Expected TGST = 2365 * 0.17 = 402.05
    # Expected Green Tax = $6 (1 pax, 1 night)
    # Total = 2365 + 402.05 + 6 = 2773.05

    folio = fce.calculate_folio(base_price, biological_outcomes=outcomes)

    assert folio["base"] == Decimal("2150.00")
    assert folio["service_charge"] == Decimal("215.00")
    assert folio["tgst"] == Decimal("402.05")
    assert folio["green_tax"] == Decimal("6.00")
    assert folio["total"] == Decimal("2773.05")

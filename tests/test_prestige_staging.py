import pytest
from decimal import Decimal
from mnos.modules.prestige.pricing import PrestigePricingEngine
from mnos.modules.prestige.models import OutreachContact
from mnos.modules.prestige.config import get_model_for_capability, get_region_config
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.modules.prestige.hotel_sourcing import HotelSourcingEngine

def test_tgst_17_on_base_plus_service_charge():
    engine = PrestigePricingEngine(fx_rate=Decimal("15.42"))
    # Base $100 -> 1542 MVR
    # SC 10% -> 154.2 MVR
    # Subtotal -> 1696.2 MVR
    # TGST 17% -> 288.354 -> 288.35 MVR
    # Green Tax 1 night, 1 adult -> $12 -> 185.04 MVR
    # Total -> 1696.2 + 288.35 + 185.04 = 2169.59 MVR

    res = engine.calculate_luxury_package(Decimal("100.00"), nights=1, adults=1)

    assert res["service_charge_mvr"] == 154.2
    assert res["subtotal_mvr"] == 1696.2
    assert res["tgst_amount_mvr"] == 288.35
    assert res["green_tax_mvr"] == 185.04
    assert res["total_mvr"] == 2169.59

def test_shadow_commit_requires_execution_guard():
    shadow = ShadowLedger()
    actor = {"identity_id": "test_actor", "device_id": "device_1", "role": "admin"}

    # Direct commit should fail
    with pytest.raises(PermissionError, match="FAIL CLOSED"):
        shadow.commit("test_event", "test_actor", {"data": "secret"})

    # Authorized commit should succeed
    with ExecutionGuard.sovereign_context(actor):
        h = shadow.commit("test_event", "test_actor", {"data": "safe", "amount": Decimal("10.50")})
        assert h is not None
        # Payload in chain is original object if same process
        assert shadow.chain[-1]["payload"]["amount"] == Decimal("10.50")

def test_outreach_high_score_requires_approval():
    # Priority A
    c1 = OutreachContact.from_csv_row({"contact_id": "C1", "priority": "A", "lead_score": "10"})
    assert c1.requires_approval is True

    # lead_score >= 13
    c2 = OutreachContact.from_csv_row({"contact_id": "C2", "priority": "B", "lead_score": "13"})
    assert c2.requires_approval is True

    # Regular
    c3 = OutreachContact.from_csv_row({"contact_id": "C3", "priority": "B", "lead_score": "12"})
    assert c3.requires_approval is False

def test_lead_score_casting_safe():
    c = OutreachContact.from_csv_row({"lead_score": "invalid"})
    assert c.lead_score == 0

    c2 = OutreachContact.from_csv_row({"lead_score": "15"})
    assert c2.lead_score == 15

def test_model_router_uses_capability_not_vendor_name():
    m = get_model_for_capability("planning")
    assert m == "computer_use_planning"

    m2 = get_model_for_capability("non_existent")
    assert m2 == "default_reasoning_model"

def test_region_config_rejects_invalid_male_azure():
    with pytest.raises(ValueError, match="REJECTED"):
        get_region_config("male-azure")

    conf = get_region_config("Singapore")
    assert conf["region"] == "Singapore"

@pytest.mark.asyncio
async def test_hotel_supply_priority():
    sourcing = HotelSourcingEngine()
    results = await sourcing.search_hotels({})

    # Direct Supply should be present (Priority 1)
    sources = [r["source"] for r in results]
    assert "Direct Supply" in sources
    assert "TBO Holidays" in sources
    assert "RateHawk" in sources
    assert "Hotelbeds" in sources

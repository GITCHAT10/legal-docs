from decimal import Decimal

import pytest

from mnos.modules.marketing.engine import SovereignMarketingEngine


class FakeCore:
    def __init__(self):
        self.actions = []

    def execute_commerce_action(self, action, actor, fn, *args):
        self.actions.append(action)
        return fn(*args)


@pytest.fixture
def engine():
    return SovereignMarketingEngine(FakeCore())


@pytest.fixture
def admin():
    return {"identity_id": "ADM-1", "role": "admin"}


@pytest.fixture
def operator():
    return {"identity_id": "MKT-1", "role": "marketing_manager"}


def test_campaign_requires_approval_and_enforces_budget(engine, admin, operator):
    brand = engine.register_brand(admin, {"name": "SALA Hotels", "languages": ["en", "ru"]})
    campaign = engine.create_campaign(operator, {
        "brand_id": brand["id"],
        "name": "CIS Winter",
        "budget": "1000.00",
        "channels": ["META", "GOOGLE"],
    })

    with pytest.raises(ValueError):
        engine.activate_campaign(operator, campaign["id"])

    engine.submit_campaign(operator, campaign["id"])
    engine.approve_campaign(admin, campaign["id"], "APPROVE", "Within approved plan")
    active = engine.activate_campaign(operator, campaign["id"])
    assert active["status"] == "ACTIVE"

    engine.record_spend(admin, campaign["id"], Decimal("900"), "META-001")
    with pytest.raises(ValueError, match="budget exceeded"):
        engine.record_spend(admin, campaign["id"], Decimal("101"), "META-002")


def test_attribution_dashboard(engine, admin, operator):
    brand = engine.register_brand(admin, {"name": "UNITED TRANSPORT"})
    campaign = engine.create_campaign(operator, {
        "brand_id": brand["id"], "name": "Airport Transfer", "budget": "500"
    })
    engine.submit_campaign(operator, campaign["id"])
    engine.approve_campaign(admin, campaign["id"], "APPROVE")
    engine.activate_campaign(operator, campaign["id"])
    engine.record_spend(admin, campaign["id"], Decimal("100"), "GOOGLE-1")

    lead = engine.capture_lead(operator, {
        "campaign_id": campaign["id"], "source": "GOOGLE", "consent": True
    })
    engine.record_conversion(operator, {
        "campaign_id": campaign["id"],
        "lead_id": lead["id"],
        "booking_ref": "UT-BOOK-100",
        "ledger_entry_ref": "LEDGER-200",
        "revenue": "450",
    })

    dashboard = engine.dashboard(operator, brand["id"])
    assert dashboard["leads"] == 1
    assert dashboard["conversions"] == 1
    assert dashboard["roas"] == "4.50"

import pytest
import uuid
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest, PricingContext, FailClosed, TaxContext

@pytest.fixture
def engine():
    return PricingEngine()

@pytest.fixture
def aegis_ctx():
    return {"identity_id": "AGENT_01", "device_id": "DEV_01", "role": "agent"}

def test_tax_context_tourism(engine, aegis_ctx):
    # accommodation -> TOURISM (17%)
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.tax.tax_type == "TOURISM"
    # Base 100 + 18% margin = 118. SC 10% = 11.8. Subtotal 129.8. Tax 17% = 22.07. Total 151.87
    assert resp.tax.tgst == Decimal("22.07")

def test_tax_context_retail(engine, aegis_ctx):
    # retail -> RETAIL (8%)
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="retail")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.tax.tax_type == "RETAIL"
    # Base 100 + 10% margin = 110. SC 0. GST 8% = 8.8. Total 118.8
    assert resp.tax.tgst == Decimal("8.80")
    assert resp.tax.service_charge == Decimal("0.00")

def test_fail_on_zero_amount(engine, aegis_ctx):
    with pytest.raises(FailClosed) as exc:
        req = PricingRequest.model_construct(net_amount=Decimal("0.0"), product_type="accommodation")
        engine.calculate(req, aegis_ctx=aegis_ctx)
    assert "INVALID_AMOUNT" in str(exc.value)

def test_fail_on_missing_amount(engine, aegis_ctx):
    with pytest.raises(FailClosed) as exc:
        req = PricingRequest.model_construct(net_amount=None, product_type="accommodation")
        engine.calculate(req, aegis_ctx=aegis_ctx)
    assert "MISSING_AMOUNT" in str(exc.value)

def test_margin_application(engine, aegis_ctx):
    # Test high allotment discount
    req = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="accommodation",
        context=PricingContext(allotment_pct=80.0)
    )
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    # Base margin 18% - 3% discount = 15%
    assert resp.waterfall.margin_pct == 0.15

def test_commission_split(engine, aegis_ctx):
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    # Sell price 118. Agent 10% = 11.8. Platform 5% = 5.9
    assert resp.waterfall.agent_commission == Decimal("11.80")
    assert resp.waterfall.platform_fee == Decimal("5.90")

def test_shadow_log_required(engine):
    # Fail if SHADOW write fails (Simulated by missing context which leads to SHADOW failure in calculate)
    # In my implementation, I auto-assign SYSTEM if context missing, so let's test absolute failure
    # Actually, let's mock shadow to raise
    from unittest.mock import MagicMock
    engine.shadow = MagicMock()
    engine.shadow.commit.side_effect = Exception("Disk Full")

    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    with pytest.raises(FailClosed) as exc:
        engine.calculate(req, aegis_ctx={"identity_id":"A","device_id":"D"})
    assert "SHADOW_COMMIT_FAILED" in str(exc.value)

def test_trace_id_present(engine, aegis_ctx):
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.trace_id is not None
    assert resp.trace_id.startswith("TR-") or len(resp.trace_id) > 0

def test_dynamic_agent_pricing(engine, aegis_ctx):
    # Top performer (score 0.9) gets -5% margin
    req = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="accommodation",
        context=PricingContext(agent_score=0.9)
    )
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    # 18% - 5% = 13%
    assert resp.waterfall.margin_pct == 0.13

def test_market_adjustment(engine, aegis_ctx):
    # Sell price would be 118. Competitor is 110. Match 110 (above 5% margin limit)
    req = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="accommodation",
        context=PricingContext(competitor_price=Decimal("110.00"))
    )
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.waterfall.sell_price == Decimal("110.00")
    # Margin now 10%
    assert resp.waterfall.margin_pct == 0.1

def test_bundle_instead_of_discount(engine, aegis_ctx):
    # Margin 18% (>15%) -> Add bundles
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert "FREE_TRANSFER_UPGRADE" in resp.bundles_applied
    assert "EARLY_CHECKIN" in resp.bundles_applied

import pytest
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
    # Base 1000 + 18% margin = 1180. SC 10% = 118. Subtotal 1298. Tax 17% = 220.66. Total 1518.66
    req = PricingRequest(net_amount=Decimal("1000.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.tax.tax_type == "TOURISM"
    assert resp.tax.tgst == Decimal("220.66")
    assert resp.tax.service_charge == Decimal("118.00")

def test_tax_context_retail(engine, aegis_ctx):
    # retail -> RETAIL (8%)
    # Base 1000 + 10% margin = 1100. SC 0. GST 8% = 88.0. Total 1188.0
    req = PricingRequest(net_amount=Decimal("1000.00"), product_type="retail")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.tax.tax_type == "RETAIL"
    assert resp.tax.tgst == Decimal("88.00")
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
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    # Default margin for accommodation is 18%
    assert resp.waterfall.margin_pct == 0.18
    assert resp.waterfall.margin_applied == Decimal("18.00")

def test_commission_split(engine, aegis_ctx):
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    # Sell price 118. Agent 10% = 11.8. Platform 5% = 5.9
    assert resp.waterfall.agent_commission == Decimal("11.80")
    assert resp.waterfall.platform_fee == Decimal("5.90")

def test_shadow_log_required(engine):
    from unittest.mock import MagicMock
    engine.shadow = MagicMock()
    engine.shadow.commit.side_effect = Exception("Audit Log Failed")

    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    with pytest.raises(FailClosed) as exc:
        engine.calculate(req, aegis_ctx={"identity_id":"A","device_id":"D"})
    assert "SHADOW_COMMIT_FAILED" in str(exc.value)

def test_trace_id_present(engine, aegis_ctx):
    req = PricingRequest(net_amount=Decimal("100.00"), product_type="accommodation")
    resp = engine.calculate(req, aegis_ctx=aegis_ctx)
    assert resp.trace_id is not None
    assert len(resp.trace_id) > 0

def test_invalid_tax_type(engine, aegis_ctx):
    with pytest.raises(FailClosed) as exc:
        req = PricingRequest(
            net_amount=Decimal("100.00"),
            product_type="accommodation",
            context=PricingContext(tax_context="ILLEGAL")
        )
        engine.calculate(req, aegis_ctx=aegis_ctx)
    assert "INVALID_TAX_CONTEXT" in str(exc.value)

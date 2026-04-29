import pytest
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest, PricingContext, TaxContext

def test_tax_context_dynamic():
    engine = PricingEngine()

    # 1. TOURISM (17% TGST + 10% SC)
    req_tourism = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="accommodation",
        context=PricingContext(tax_context=TaxContext.TOURISM)
    )
    resp_tourism = engine.calculate(req_tourism)
    # margin 18% -> 118. SC 11.8. Subtotal 129.8. TGST 22.066 -> 22.07. Total 151.87
    assert resp_tourism.tax.tax_type == "TOURISM"
    assert resp_tourism.tax.tgst == Decimal("22.07")

    # 2. RETAIL (8% GST + 0% SC)
    req_retail = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="retail",
        context=PricingContext(tax_context=TaxContext.RETAIL)
    )
    resp_retail = engine.calculate(req_retail)
    # margin 10% -> 110. SC 0. GST 8.8. Total 118.8
    assert resp_retail.tax.tax_type == "RETAIL"
    assert resp_retail.tax.tgst == Decimal("8.80")
    assert resp_retail.tax.service_charge == Decimal("0.00")

    # 3. EXEMPT (0% Tax)
    req_exempt = PricingRequest(
        net_amount=Decimal("100.00"),
        product_type="accommodation",
        context=PricingContext(tax_context="EXEMPT")
    )
    resp_exempt = engine.calculate(req_exempt)
    assert resp_exempt.tax.tgst == Decimal("0.00")

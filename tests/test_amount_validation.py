import pytest
from decimal import Decimal
from mnos.modules.imoxon.pricing.engine import PricingEngine, PricingRequest

def test_amount_validation():
    engine = PricingEngine()

    # 1. Zero Amount Rejection
    with pytest.raises(ValueError) as exc:
        req = PricingRequest(net_amount=Decimal("0.00"), product_type="accommodation")
        engine.calculate(req)
    # Pydantic validation handles this before engine.calculate but let's be sure
    assert "greater than 0" in str(exc.value)

    # 2. Negative Amount Rejection
    with pytest.raises(ValueError) as exc:
        req = PricingRequest(net_amount=Decimal("-10.00"), product_type="accommodation")
        engine.calculate(req)
    assert "greater than 0" in str(exc.value)

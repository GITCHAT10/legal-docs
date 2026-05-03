import pytest
from mnos.core.fce.tax_engine_mv import calculate_maldives_tax

def test_maldives_tax_calculation():
    # Example:
    # Base: 1000.00
    # Service Charge: 100.00
    # Taxable Subtotal: 1100.00
    # TGST: 187.00
    # Customer Total: 1287.00

    result = calculate_maldives_tax(1000.00)
    assert result.base_price == 1000.00
    assert result.service_charge == 100.00
    assert result.taxable_subtotal == 1100.00
    assert result.tgst == 187.00
    assert result.customer_total == 1287.00

def test_maldives_tax_rounding():
    result = calculate_maldives_tax(99.99)
    # 99.99 * 0.1 = 9.999 -> 10.00
    # 99.99 + 10.00 = 109.99
    # 109.99 * 0.17 = 18.6983 -> 18.70
    # 109.99 + 18.70 = 128.69
    assert result.service_charge == 10.00
    assert result.tgst == 18.70
    assert result.customer_total == 128.69

def test_unsupported_currency():
    with pytest.raises(ValueError):
        calculate_maldives_tax(100, currency="EUR")

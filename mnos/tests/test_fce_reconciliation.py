import pytest
from mnos.modules.fce.tax_logic import calculate_maldives_taxes
from datetime import date

def test_maldives_tax_calculation():
    # Base: 1000
    # SC: 10% of 1000 = 100
    # Subtotal: 1100
    # TGST: 17% of 1100 = 187
    # Total: 1287
    result = calculate_maldives_taxes(1000.0, business_date=date(2025, 7, 1))
    assert result["service_charge"] == 100.0
    assert result["tgst"] == 187.0
    assert result["total_amount"] == 1287.0

def test_maldives_tax_with_green_tax():
    # Base: 500
    # SC: 50
    # TGST: 17% of 550 = 93.5
    # Green Tax: 12 * 2 = 24 (Effective Jan 1, 2025)
    # Total: 550 + 93.5 + 24 = 667.5
    result = calculate_maldives_taxes(500.0, business_date=date(2025, 7, 1), apply_green_tax=True, nights=2)
    assert result["service_charge"] == 50.0
    assert result["tgst"] == 93.5
    assert result["green_tax"] == 24.0
    assert result["total_amount"] == 667.5

def test_zero_base_amount():
    result = calculate_maldives_taxes(0.0, business_date=date(2025, 7, 1))
    assert result["total_amount"] == 0.0

import pytest
from mnos.core.fce.service import calculate_maldives_tax

def test_maldives_tax_calculation():
    # Base: 1000
    # SC: 10% of 1000 = 100
    # Subtotal: 1100
    # TGST: 17% of 1100 = 187
    # Total: 1287
    result = calculate_maldives_tax(1000.0)
    assert result["service_charge"] == 100.0
    assert result["tgst"] == 187.0
    assert result["total"] == 1287.0

def test_maldives_tax_with_green_tax():
    # Base: 500
    # SC: 50
    # TGST: 17% of 550 = 93.5
    # Green Tax: 6 * 2 = 12
    # Total: 550 + 93.5 + 12 = 655.5
    result = calculate_maldives_tax(500.0, apply_green_tax=True, nights=2)
    assert result["service_charge"] == 50.0
    assert result["tgst"] == 93.5
    assert result["green_tax"] == 12.0
    assert result["total"] == 655.5

def test_zero_base_amount():
    result = calculate_maldives_tax(0.0)
    assert result["total"] == 0.0

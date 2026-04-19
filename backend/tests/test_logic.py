from app.logic import calculate_footprint
from app.schemas import FootprintInput, HomeInput, TransportInput, WasteInput
import pytest

def test_calculate_home_only():
    input_data = FootprintInput(home=HomeInput(electricity_kwh=100, water_m3=10, lpg_kg=5))
    # 100 * 0.73 + 10 * 3.0 + 5 * 2.98 = 73 + 30 + 14.9 = 117.9
    result = calculate_footprint(input_data)
    assert result.home_total == 117.9
    assert result.grand_total == 117.9

def test_calculate_transport_only():
    input_data = FootprintInput(transport=TransportInput(speedboat_liters=10, seaplane_km=100))
    # 10 * 2.31 + 100 * 0.50 = 23.1 + 50 = 73.1
    result = calculate_footprint(input_data)
    assert result.transport_total == 73.1
    assert result.grand_total == 73.1

def test_calculate_empty():
    input_data = FootprintInput()
    result = calculate_footprint(input_data)
    assert result.grand_total == 0

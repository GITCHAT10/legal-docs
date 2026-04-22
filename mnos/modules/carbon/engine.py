from .signals import *
from .schemas import FootprintInput

def calculate_raw_emissions(input_data: FootprintInput) -> dict:
    """
    Pure carbon calculation logic based on environmental signals.
    """
    home_total = 0
    if input_data.environmental:
        e = input_data.environmental
        home_total += e.electricity_kwh * ELECTRICITY_FACTOR
        home_total += e.water_m3 * WATER_FACTOR
        home_total += e.lpg_kg * LPG_FACTOR

    transport_total = 0
    if input_data.logistics:
        l = input_data.logistics
        transport_total += l.speedboat_fuel_liters * SPEEDBOAT_FACTOR
        transport_total += l.staff_travel_km * SEAPLANE_FACTOR
        transport_total += l.guest_travel_km * DOMESTIC_FLIGHT_FACTOR

    waste_total = 0
    if input_data.environmental:
        e = input_data.environmental
        waste_total += (e.plastic_waste_kg - e.recycled_waste_kg) * WASTE_FACTOR

    return {
        "home_total": home_total,
        "transport_total": transport_total,
        "waste_total": waste_total,
        "grand_total": home_total + transport_total + waste_total
    }

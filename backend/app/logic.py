from .constants import *
from .schemas import FootprintInput, FootprintResult

def calculate_footprint(input_data: FootprintInput) -> FootprintResult:
    home_total = 0
    if input_data.home:
        home_total += input_data.home.electricity_kwh * ELECTRICITY_FACTOR
        home_total += input_data.home.water_m3 * WATER_FACTOR
        home_total += input_data.home.lpg_kg * LPG_FACTOR

    transport_total = 0
    if input_data.transport:
        t = input_data.transport
        transport_total += t.petrol_car_km * PETROL_CAR_FACTOR
        transport_total += t.diesel_car_km * DIESEL_CAR_FACTOR
        transport_total += t.motorcycle_km * MOTORCYCLE_FACTOR
        transport_total += t.speedboat_liters * SPEEDBOAT_FACTOR
        transport_total += t.ferry_km * FERRY_FACTOR
        transport_total += t.seaplane_km * SEAPLANE_FACTOR
        transport_total += t.domestic_flight_km * DOMESTIC_FLIGHT_FACTOR

    waste_total = 0
    if input_data.waste:
        waste_total += input_data.waste.waste_kg * WASTE_FACTOR

    grand_total = home_total + transport_total + waste_total

    return FootprintResult(
        home_total=round(home_total, 2),
        transport_total=round(transport_total, 2),
        waste_total=round(waste_total, 2),
        grand_total=round(grand_total, 2)
    )

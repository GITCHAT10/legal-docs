from .signals import *
from .schemas import FootprintInput, FootprintResult
from .ledger import create_shadow_hash

def calculate_footprint(input_data: FootprintInput) -> FootprintResult:
    """
    mRIS scoring engine core logic.
    Aligns with HCMI 2.0 (Hotel Carbon Measurement Initiative) methodologies.
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
        # staff/guest travel (Staff: seaplane avg, Guest: domestic flight avg)
        transport_total += l.staff_travel_km * SEAPLANE_FACTOR
        transport_total += l.guest_travel_km * DOMESTIC_FLIGHT_FACTOR

    waste_total = 0
    if input_data.environmental:
        e = input_data.environmental
        waste_total += (e.plastic_waste_kg - e.recycled_waste_kg) * WASTE_FACTOR

    grand_total = home_total + transport_total + waste_total

    # HCMI: Carbon per occupied room
    rooms = input_data.pms.occupancy_rooms if input_data.pms and input_data.pms.occupancy_rooms > 0 else 1
    carbon_per_room = grand_total / rooms

    # Compliance logic
    compliance_status = "PENDING"
    if input_data.social and input_data.social.female_board_percent >= 30:
        compliance_status = "IFRS-ALIGNED"

    # Create immutable shadow hash
    payload = input_data.model_dump()
    shadow_hash = create_shadow_hash(payload)

    return FootprintResult(
        home_total=round(home_total, 2),
        transport_total=round(transport_total, 2),
        waste_total=round(waste_total, 2),
        carbon_per_occupied_room=round(carbon_per_room, 2),
        grand_total=round(grand_total, 2),
        shadow_hash=shadow_hash,
        compliance_status=compliance_status,
        metrics={
            "coral_health": input_data.environmental.coral_health_index if input_data.environmental else 0,
            "local_spend_percent": 100 # Placeholder
        }
    )

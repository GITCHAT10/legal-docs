from .schemas import FootprintInput, FootprintResult
from .ledger import create_shadow_hash
from .carbon import calculate_raw_emissions

def calculate_footprint(input_data: FootprintInput) -> FootprintResult:
    """
    mRIS ESG Orchestrator.
    Combines raw emissions with HCMI metrics and sovereign compliance logic.
    """
    # Step 1: Raw Carbon Calculation
    emissions = calculate_raw_emissions(input_data)

    # Step 2: ESG Orchestration & HCMI Metrics
    rooms = input_data.pms.occupancy_rooms if input_data.pms and input_data.pms.occupancy_rooms > 0 else 1
    carbon_per_room = emissions["grand_total"] / rooms

    # Step 3: Sovereign Compliance Logic
    compliance_status = "PENDING"
    if input_data.social and input_data.social.female_board_percent >= 30:
        compliance_status = "IFRS-ALIGNED"

    # Step 4: Shadow Ledger Commit (Immutable Hash)
    payload = input_data.model_dump()
    shadow_hash = create_shadow_hash(payload)

    return FootprintResult(
        home_total=round(emissions["home_total"], 2),
        transport_total=round(emissions["transport_total"], 2),
        waste_total=round(emissions["waste_total"], 2),
        carbon_per_occupied_room=round(carbon_per_room, 2),
        grand_total=round(emissions["grand_total"], 2),
        shadow_hash=shadow_hash,
        compliance_status=compliance_status,
        metrics={
            "coral_health": input_data.environmental.coral_health_index if input_data.environmental else 0,
            "local_spend_percent": 100 # Placeholder
        }
    )

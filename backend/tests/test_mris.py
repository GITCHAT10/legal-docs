from app.mris import calculate_footprint
from app.schemas import FootprintInput, EnvironmentalInput, PMSInput, SocialInput
import pytest

def test_hcmi_calculation():
    # 100 rooms, 1000kg CO2 = 10kg/room
    input_data = FootprintInput(
        pms=PMSInput(occupancy_rooms=100),
        environmental=EnvironmentalInput(electricity_kwh=1000 / 0.73) # results in ~1000kg CO2
    )
    result = calculate_footprint(input_data)
    assert result.carbon_per_occupied_room == 10.0

def test_shadow_ledger_hashing():
    input_data = FootprintInput(island_id="MV-TEST")
    result1 = calculate_footprint(input_data)
    result2 = calculate_footprint(input_data)

    assert result1.shadow_hash != ""
    # Even with same input, timestamp in ledger makes them unique for auditability
    # though our current create_shadow_hash uses datetime.utcnow()
    assert len(result1.shadow_hash) == 64

def test_ifrs_compliance_alignment():
    # Target: 30% female board representation
    input_data = FootprintInput(social=SocialInput(female_board_percent=30.0))
    result = calculate_footprint(input_data)
    assert result.compliance_status == "IFRS-ALIGNED"

    input_data_fail = FootprintInput(social=SocialInput(female_board_percent=25.0))
    result_fail = calculate_footprint(input_data_fail)
    assert result_fail.compliance_status == "PENDING"

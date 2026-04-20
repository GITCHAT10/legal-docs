import pytest
from unified_suite.atoll_airways.models import LoadManifest, WaterZone, WaterLane, WeatherStatus
from unified_suite.atoll_airways.engines.runway import LagoonRunwayEngine
from unified_suite.atoll_airways.load_control.balancer import AtollLoadBalancer
from unified_suite.atoll_airways.scheduler.rotator import RotationScheduler

def test_runway_assignment():
    zone = WaterZone(
        zone_id="ZONE1",
        location_name="Test Lagoon",
        lanes=[
            WaterLane(lane_id="L1", heading=90),
            WaterLane(lane_id="L2", heading=270)
        ]
    )
    weather = WeatherStatus(
        location_id="ZONE1",
        wind_speed_knots=10,
        wind_direction=100,
        visibility_meters=5000
    )
    lane = LagoonRunwayEngine.assign_best_lane(zone, weather)
    assert lane.lane_id == "L1" # 90 is closer to 100 than 270

def test_load_validation():
    # MTOW is 5670. OEW is 3500. Remainder is 2170.
    valid_manifest = LoadManifest(
        flight_id="F1",
        passenger_count=10,
        total_passenger_weight=800.0,
        total_baggage_weight=200.0
    )
    assert AtollLoadBalancer.validate_load(valid_manifest) is True

    invalid_manifest = LoadManifest(
        flight_id="F2",
        passenger_count=20, # Exceeds 19
        total_passenger_weight=1500.0,
        total_baggage_weight=500.0
    )
    assert AtollLoadBalancer.validate_load(invalid_manifest) is False

def test_rotation_generation():
    rotation = RotationScheduler.create_daily_rotation("8Q-TEST", "BASE", ["DEST1", "DEST2"])
    assert len(rotation) == 24 # 12 cycles * 2 legs
    assert rotation[0].origin == "BASE"
    assert rotation[0].destination == "DEST1"
    assert rotation[1].origin == "DEST1"
    assert rotation[1].destination == "BASE"

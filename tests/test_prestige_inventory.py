import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date, time
from mnos.modules.prestige.inventory.room_category_schema import RoomCategory, RoomCategoryType, EstablishmentType, ViewType, PrivacyLevel, TransferRequirement, InventorySource, RoomStatus
from mnos.modules.prestige.inventory.room_matching import RoomMatchingEngine
from mnos.modules.prestige.contracts.transfer_quote import UHNWIntake
from mnos.modules.shadow.ledger import ShadowLedger
from mnos.shared.execution_guard import ExecutionGuard
from mnos.modules.prestige.taxes.airport_fees_schema import TravelClass, PassengerResidency

@pytest.fixture
def shadow():
    return ShadowLedger()

@pytest.fixture
def room_matching(shadow):
    return RoomMatchingEngine(shadow)

@pytest.fixture
def auth_actor():
    return {"identity_id": "SYS", "device_id": "DEV-01", "role": "admin"}

def test_room_category_schema_requires_establishment_id():
    with pytest.raises(Exception): # Pydantic ValidationError
        RoomCategory(room_category_name="Test")

def test_room_category_rejects_invalid_occupancy():
    with pytest.raises(ValueError, match="max_total_occupancy cannot be less than base_occupancy"):
        RoomCategory(
            room_category_id=uuid4(),
            establishment_id=uuid4(),
            supplier_id=uuid4(),
            room_category_name="Villa",
            room_category_type=RoomCategoryType.POOL_VILLA,
            establishment_type=EstablishmentType.RESORT,
            view_type=ViewType.OCEAN,
            privacy_levels_supported={PrivacyLevel.P4},
            max_adults=2,
            max_children=0,
            max_infants=0,
            max_total_occupancy=1, # Invalid: less than base 2
            base_occupancy=2,
            extra_bed_rate=Decimal("0"),
            child_rate_rule={},
            infant_policy={},
            meal_plan_allowed={"AI"},
            bedroom_count=1,
            bathroom_count=1,
            transfer_requirement=TransferRequirement.SEAPLANE,
            inventory_source=InventorySource.DIRECT_CONTRACT,
            allotment_count=5,
            release_period_days=30,
            effective_from=date(2024,1,1),
            status=RoomStatus.ACTIVE
        )

@pytest.mark.anyio
async def test_room_matching_rejects_over_occupancy(room_matching, auth_actor):
    intake = UHNWIntake(
        guest_count_adult=3,
        guest_count_child=2,
        guest_count_infant=0,
        estimated_baggage_kg=50,
        arrival_airport="VIA",
        arrival_date=date(2024,12,1),
        arrival_time=time(10,0),
        resort_id="R1",
        destination_atoll="Kaafu",
        preferred_transfer_mode="speedboat",
        privacy_level="P1",
        travel_class=TravelClass.ECONOMY,
        passenger_residency=PassengerResidency.FOREIGN
    )

    room = RoomCategory(
        room_category_id=uuid4(),
        establishment_id=uuid4(),
        supplier_id=uuid4(),
        room_category_name="Small Villa",
        room_category_type=RoomCategoryType.BEACH_VILLA,
        establishment_type=EstablishmentType.RESORT,
        view_type=ViewType.BEACH,
        privacy_levels_supported={PrivacyLevel.P1},
        max_adults=2,
        max_children=1,
        max_infants=0,
        max_total_occupancy=2, # Total 5 guests in intake
        base_occupancy=2,
        extra_bed_rate=Decimal("0"),
        child_rate_rule={},
        infant_policy={},
        meal_plan_allowed={"BB"},
        bedroom_count=1,
        bathroom_count=1,
        transfer_requirement=TransferRequirement.SPEEDBOAT,
        inventory_source=InventorySource.DIRECT_CONTRACT,
        allotment_count=5,
        release_period_days=30,
        effective_from=date(2024,1,1),
        status=RoomStatus.ACTIVE
    )

    with ExecutionGuard.authorized_context(auth_actor):
        results = room_matching.match_room_categories(intake, [room])
        assert len(results) == 0

@pytest.mark.anyio
async def test_room_matching_prefers_p4_privacy_rooms(room_matching, auth_actor):
    intake = UHNWIntake(
        guest_count_adult=2, guest_count_child=0, guest_count_infant=0,
        estimated_baggage_kg=20, arrival_airport="VIA", arrival_date=date(2024,12,1),
        arrival_time=time(10,0), resort_id="R1", destination_atoll="K",
        preferred_transfer_mode="seaplane", privacy_level="P4",
        travel_class=TravelClass.PRIVATE_JET, passenger_residency=PassengerResidency.FOREIGN
    )

    # Room 1: Standard P1
    r1 = RoomCategory(
        room_category_id=uuid4(), establishment_id=uuid4(), supplier_id=uuid4(),
        room_category_name="Standard", room_category_type=RoomCategoryType.GARDEN_ROOM,
        establishment_type=EstablishmentType.RESORT, view_type=ViewType.GARDEN,
        privacy_levels_supported={PrivacyLevel.P1}, max_adults=2, max_children=0, max_infants=0,
        max_total_occupancy=2, base_occupancy=2, extra_bed_rate=Decimal("0"),
        child_rate_rule={}, infant_policy={}, meal_plan_allowed={"BB"},
        bedroom_count=1, bathroom_count=1, transfer_requirement=TransferRequirement.WALKING,
        inventory_source=InventorySource.SALA, allotment_count=10, release_period_days=0,
        effective_from=date(2024,1,1), status=RoomStatus.ACTIVE
    )

    # Room 2: Residence P4 with private pool
    r2 = RoomCategory(
        room_category_id=uuid4(), establishment_id=uuid4(), supplier_id=uuid4(),
        room_category_name="Luxury Residence", room_category_type=RoomCategoryType.RESIDENCE,
        establishment_type=EstablishmentType.RESORT, view_type=ViewType.SUNSET,
        privacy_levels_supported={PrivacyLevel.P4}, max_adults=4, max_children=2, max_infants=2,
        max_total_occupancy=8, base_occupancy=4, extra_bed_rate=Decimal("500"),
        child_rate_rule={}, infant_policy={}, meal_plan_allowed={"AI"},
        bedroom_count=3, bathroom_count=3, private_pool=True,
        transfer_requirement=TransferRequirement.SEAPLANE, inventory_source=InventorySource.DIRECT_CONTRACT,
        allotment_count=1, release_period_days=60, effective_from=date(2024,1,1),
        status=RoomStatus.ACTIVE
    )

    with ExecutionGuard.authorized_context(auth_actor):
        results = room_matching.match_room_categories(intake, [r1, r2])
        # r1 should be filtered by privacy level P4
        assert len(results) == 1
        assert results[0]["room"].room_category_name == "Luxury Residence"
        assert results[0]["score"] > 0

@pytest.mark.anyio
async def test_room_matching_creates_shadow_events(room_matching, auth_actor, shadow):
    intake = UHNWIntake(
        guest_count_adult=2, guest_count_child=0, guest_count_infant=0,
        estimated_baggage_kg=20, arrival_airport="VIA", arrival_date=date(2024,12,1),
        arrival_time=time(10,0), resort_id="R1", destination_atoll="K",
        preferred_transfer_mode="seaplane", privacy_level="P1",
        travel_class=TravelClass.ECONOMY, passenger_residency=PassengerResidency.FOREIGN
    )

    with ExecutionGuard.authorized_context(auth_actor):
        room_matching.match_room_categories(intake, [])
        # Verify matching started event
        assert any(e["event_type"] == "prestige.room.matching_started" for e in shadow.chain)
        assert any(e["event_type"] == "prestige.room.matching_completed" for e in shadow.chain)

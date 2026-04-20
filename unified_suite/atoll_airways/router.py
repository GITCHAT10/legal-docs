from fastapi import APIRouter, HTTPException, Request, Depends
from .models import SeaplaneFlight, WaterZone, LoadManifest, WaterLane
from .engines.runway import LagoonRunwayEngine
from .scheduler.rotator import RotationScheduler
from .load_control.balancer import AtollLoadBalancer
from .integrations.sync import AtollIntegrations
from mnos.events.publisher import EventPublisher
from mnos.shadow_service import ShadowService
from unified_suite.tax_engine.calculator import MoatsTaxCalculator
import logging
import json

logger = logging.getLogger("unified_suite")
router = APIRouter()

from fastapi import Query

@router.post("/rotations/{aircraft_id}", response_model=list[SeaplaneFlight])
async def generate_rotation(aircraft_id: str, base: str, destinations: list[str] = Query(...)):
    flights = RotationScheduler.create_daily_rotation(aircraft_id, base, destinations)

    # Standard Sovereign Logging
    for flight in flights:
        # Convert to dict and handle datetime serialization for JSON
        event_payload = json.loads(flight.json())
        ShadowService.log_event("SEAPLANE_ROTATION_CREATED", event_payload)
        EventPublisher().publish(
            channel="atoll_airways.events",
            entity_id=flight.flight_id,
            entity_type="SEAPLANE",
            action="CREATE_ROTATION",
            payload=event_payload
        )
    return flights

@router.post("/flights/{flight_id}/dispatch")
async def dispatch_seaplane(flight_id: str, manifest: LoadManifest, zone: WaterZone):
    # 1. MOATS TAX ENFORCEMENT
    tax_info = MoatsTaxCalculator.calculate_bill(1200.00) # Seaplane Sector Fee
    if not MoatsTaxCalculator.validate_tax_compliance(tax_info):
         raise HTTPException(status_code=400, detail="Sovereign Error: MOATS Tax Validation Failed")

    # 2. LOAD CONTROL
    if not AtollLoadBalancer.validate_load(manifest):
        raise HTTPException(status_code=400, detail="Safety Violation: Load manifest invalid")

    # 3. WEATHER & RUNWAY ENGINE
    weather = AtollIntegrations.get_weather(zone.zone_id)
    lane = LagoonRunwayEngine.assign_best_lane(zone, weather)
    if not lane:
        raise HTTPException(status_code=503, detail="Weather Restriction: No safe water lane available")

    # 4. MNOS INTEGRATION
    dispatch_data = {
        "flight_id": flight_id,
        "lane_id": lane.lane_id,
        "tax_applied": tax_info,
        "load_verified": True
    }
    ShadowService.log_event("SEAPLANE_DISPATCHED", dispatch_data)
    EventPublisher().publish(
        channel="atoll_airways.events",
        entity_id=flight_id,
        entity_type="SEAPLANE",
        action="DISPATCH",
        payload=dispatch_data
    )

    return {"status": "DISPATCHED", "lane": lane.lane_id, "tax": tax_info}

@router.get("/resorts/{resort_id}/guest-ready")
async def check_guest_ready(resort_id: str):
    ready = AtollIntegrations.get_resort_status(resort_id)
    return {"resort_id": resort_id, "guest_ready": ready}

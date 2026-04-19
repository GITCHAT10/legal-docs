from fastapi import APIRouter, HTTPException, Request
from .models import Flight
from .service import AirportService
from typing import List
from mnos.events.publisher import EventPublisher
from mnos.shadow_service import ShadowService
from unified_suite.tax_engine.calculator import MoatsTaxCalculator

router = APIRouter()
service = AirportService()

@router.post("/flights", response_model=Flight)
async def create_flight(flight: Flight, request: Request):
    # MOATS TAX ENFORCEMENT
    tax_info = MoatsTaxCalculator.calculate_bill(1500.00) # Standard Airport Fee

    if not MoatsTaxCalculator.validate_tax_compliance(tax_info):
        from unified_suite.core.flows import SovereignFlows
        SovereignFlows.deny_flow(flight.flight_number, "Tax Compliance Breach", {"tax_data": tax_info})
        raise HTTPException(status_code=400, detail="Sovereign Error: MOATS Tax Validation Failed")

    scheduled_flight = service.schedule_flight(flight)

    # MNOS Integration
    event_payload = {
        "type": "flight.scheduled",
        "flight_number": flight.flight_number,
        "origin": flight.origin,
        "tax_applied": tax_info
    }
    ShadowService.log_event("FLIGHT_SCHEDULED", event_payload)
    EventPublisher().publish("airport.events", event_payload)

    return scheduled_flight

@router.get("/flights", response_model=List[Flight])
async def list_flights():
    return service.get_all_flights()

@router.post("/flights/{flight_number}/assign-gate")
async def assign_gate(flight_number: str, request: Request):
    gate = service.assign_gate(flight_number)
    if not gate:
        raise HTTPException(status_code=404, detail="Flight not found or no gates available")

    # MNOS Integration
    event_payload = {"type": "flight.gate_assigned", "flight_number": flight_number, "gate": gate}
    ShadowService.log_event("GATE_ASSIGNED", event_payload)
    EventPublisher().publish("airport.events", event_payload)

    return {"flight_number": flight_number, "gate": gate}

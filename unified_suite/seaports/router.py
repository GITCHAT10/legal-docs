from fastapi import APIRouter, HTTPException, Request
from .models import Vessel, Container
from .service import SeaPortService
from typing import List
from mnos.events.publisher import EventPublisher
from mnos.shadow_service import ShadowService
from unified_suite.tax_engine.calculator import MoatsTaxCalculator

router = APIRouter()
service = SeaPortService()

@router.post("/vessels", response_model=Vessel)
async def register_vessel(vessel: Vessel, request: Request):
    # MOATS TAX ENFORCEMENT
    tax_info = MoatsTaxCalculator.calculate_bill(5000.00) # Standard Port Fee

    if not MoatsTaxCalculator.validate_tax_compliance(tax_info):
        from unified_suite.core.flows import SovereignFlows
        SovereignFlows.deny_flow(vessel.vessel_id, "Tax Compliance Breach", {"tax_data": tax_info})
        raise HTTPException(status_code=400, detail="Sovereign Error: MOATS Tax Validation Failed")

    registered_vessel = service.register_vessel(vessel)

    # MNOS Integration
    event_payload = {
        "vessel_id": vessel.vessel_id,
        "name": vessel.name,
        "tax_applied": tax_info
    }
    ShadowService.log_event("VESSEL_REGISTERED", event_payload)
    EventPublisher().publish("seaport.events", entity=vessel.vessel_id, action="REGISTER", payload=event_payload)

    return registered_vessel

@router.get("/vessels", response_model=List[Vessel])
async def list_vessels():
    return service.get_all_vessels()

@router.post("/vessels/{vessel_id}/assign-berth")
async def assign_berth(vessel_id: str, request: Request):
    # MOATS TAX ENFORCEMENT
    tax_info = MoatsTaxCalculator.calculate_bill(750.00) # Berth Assignment Fee

    if not MoatsTaxCalculator.validate_tax_compliance(tax_info):
        from unified_suite.core.flows import SovereignFlows
        SovereignFlows.deny_flow(vessel_id, "Tax Compliance Breach", {"tax_data": tax_info})
        raise HTTPException(status_code=400, detail="Sovereign Error: MOATS Tax Validation Failed")

    berth = service.assign_berth(vessel_id)
    if not berth:
        raise HTTPException(status_code=404, detail="Vessel not found or no berths available")

    # MNOS Integration
    event_payload = {"vessel_id": vessel_id, "berth": berth}
    ShadowService.log_event("BERTH_ASSIGNED", event_payload)
    EventPublisher().publish("seaport.events", entity=vessel_id, action="ASSIGN_BERTH", payload=event_payload)

    return {"vessel_id": vessel_id, "berth": berth}

@router.get("/vessels/{vessel_id}/manifest", response_model=List[Container])
async def get_manifest(vessel_id: str):
    return service.get_vessel_manifest(vessel_id)

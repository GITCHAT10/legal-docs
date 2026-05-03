from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from mnos.modules.mios.schemas.models import CargoDWS, Shipment

from mnos.modules.mios.schemas.aircraft import FlightData

def create_mios_router(godown, freight, clearing, fce, fx, handoff, aircraft, get_actor_ctx):
    router = APIRouter(prefix="/mios", tags=["MIOS"])

    @router.post("/shipments/create", response_model=Shipment)
    async def create_shipment(customer_id: UUID, origin_hub: str, actor: dict = Depends(get_actor_ctx)):
        shipment_id = uuid4()
        shipment = Shipment(id=shipment_id, customer_id=customer_id, origin_hub=origin_hub)
        godown.shipments[shipment_id] = shipment
        godown.shadow.commit("mios.shipment.created", actor["identity_id"], shipment.dict())
        return shipment

    @router.post("/godown/receive")
    async def receive_cargo(shipment_id: UUID, description: str, dws: CargoDWS, actor: dict = Depends(get_actor_ctx)):
        return godown.receive_cargo(actor, shipment_id, description, dws)

    @router.post("/clearing/submit")
    async def submit_customs(shipment_id: UUID, declaration_no: str, actor: dict = Depends(get_actor_ctx)):
        try:
            return clearing.submit_to_customs(actor, shipment_id, declaration_no)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/landed-cost/{shipment_id}")
    async def get_landed_cost(shipment_id: UUID, actor: dict = Depends(get_actor_ctx)):
        cost = fce.get_landed_cost(shipment_id)
        sc = fce.calculate_sky_clearance_sc(shipment_id)
        return {"landed_cost": float(cost), "service_charge": float(sc), "currency": "MVR"}

    @router.get("/intelligence/strategy/national-flow")
    async def get_national_flow(actor: dict = Depends(get_actor_ctx)):
        # Strategic ASI-ready data
        from mnos.modules.mios.intelligence.strategic import MIOSStrategicLayer
        strat = MIOSStrategicLayer()
        return strat.get_national_import_flow()

    @router.post("/intelligence/agents/reconcile")
    async def agent_reconcile(shipment_id: UUID, actor: dict = Depends(get_actor_ctx)):
        from mnos.modules.mios.intelligence.agent_layer import FCEReconciliationAgent
        from mnos.modules.mios.services.shadow_service import MIOSShadowService
        shadow_svc = MIOSShadowService(godown.shadow)
        agent = FCEReconciliationAgent(shadow_svc)
        return agent.reconcile(shipment_id)

    @router.post("/intelligence/aircraft/decide")
    async def aircraft_decide(data: FlightData, actor: dict = Depends(get_actor_ctx)):
        return aircraft.evaluate_flight(actor, data)

    return router

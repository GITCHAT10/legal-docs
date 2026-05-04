from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

class UmbilicalRoute(BaseModel):
    route_id: str
    project_id: str
    coordinates: List[Dict[str, float]]

class UtilityMotionSimulation(BaseModel):
    sim_id: str
    route_id: str
    passed: bool

class HoseBendReading(BaseModel):
    reading_id: str
    route_id: str
    bend_radius_cm: float

class CableTensionReading(BaseModel):
    reading_id: str
    route_id: str
    tension_kn: float

class DryBreakDisconnectEvent(BaseModel):
    event_id: str
    route_id: str
    leak_detected: bool

class ZeroLeakCertification(BaseModel):
    cert_id: str
    route_id: str
    status: str

def create_utilities_router(guard: ExecutionGuard, shadow, orca):
    router = APIRouter(prefix="/atollx/utilities", tags=["ATOLLX_UTILITIES"])

    @router.post("/route")
    async def create_route(route: UmbilicalRoute, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.utilities.route",
            actor,
            lambda **kwargs: {"status": "ROUTE_LOGGED", "route_id": route.route_id}
        )

    @router.post("/motion-simulation")
    async def log_simulation(sim: UtilityMotionSimulation, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.utilities.simulation",
            actor,
            lambda **kwargs: {"status": "SIMULATION_LOGGED", "sim_id": sim.sim_id}
        )

    @router.post("/hose-bend")
    async def log_hose_bend(reading: HoseBendReading, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.utilities.hose_bend",
            actor,
            lambda **kwargs: {"status": "HOSE_BEND_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/cable-tension")
    async def log_cable_tension(reading: CableTensionReading, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.utilities.cable_tension",
            actor,
            lambda **kwargs: {"status": "CABLE_TENSION_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/drybreak-disconnect")
    async def log_disconnect(event: DryBreakDisconnectEvent, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: Floating utility dry-break disconnect must fail if zero-leak validation fails.
        orca_res = orca.validate("ZERO_LEAK", actor["identity_id"], {"leak_detected": event.leak_detected})
        if not orca_res["passed"]:
            raise HTTPException(status_code=400, detail=f"FAIL CLOSED: Zero-leak validation failed: {orca_res['failure_reasons']}")

        return guard.execute_sovereign_action(
            "atollx.utilities.disconnect",
            actor,
            lambda **kwargs: {"status": "DISCONNECT_LOGGED", "event_id": event.event_id}
        )

    @router.post("/zero-leak-validate")
    async def validate_zero_leak(route_id: str, actor: dict = Depends(get_actor_context)):
        return orca.validate("ZERO_LEAK", actor["identity_id"], {"route_id": route_id})

    return router

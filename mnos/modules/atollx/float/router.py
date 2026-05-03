from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from mnos.shared.execution_guard import ExecutionGuard

class FloatingPlatform(BaseModel):
    platform_id: str
    project_id: str
    buoyancy_rating: float

class StabilityCalculation(BaseModel):
    calc_id: str
    platform_id: str
    metacentric_height: float

class MooringSystem(BaseModel):
    system_id: str
    platform_id: str
    type: str

class MooringTensionReading(BaseModel):
    reading_id: str
    system_id: str
    tension_kn: float

class FloatingSTPReading(BaseModel):
    reading_id: str
    platform_id: str
    effluent_quality: str

class GuestComfortMetric(BaseModel):
    metric_id: str
    platform_id: str
    vibration_level: float
    roll_angle: float

def create_float_router(guard: ExecutionGuard, shadow, orca):
    router = APIRouter(prefix="/atollx/float", tags=["ATOLLX_FLOAT"])

    @router.post("/platform")
    async def create_platform(platform: FloatingPlatform, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.float.platform",
            actor,
            lambda: {"status": "PLATFORM_LOGGED", "platform_id": platform.platform_id}
        )

    @router.post("/stability")
    async def log_stability(calc: StabilityCalculation, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.float.stability",
            actor,
            lambda: {"status": "STABILITY_LOGGED", "calc_id": calc.calc_id}
        )

    @router.post("/mooring")
    async def create_mooring(system: MooringSystem, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.float.mooring",
            actor,
            lambda: {"status": "MOORING_LOGGED", "system_id": system.system_id}
        )

    @router.post("/tension")
    async def log_tension(reading: MooringTensionReading, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.float.tension",
            actor,
            lambda: {"status": "TENSION_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/stp")
    async def log_stp(reading: FloatingSTPReading, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.float.stp",
            actor,
            lambda: {"status": "STP_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/validate")
    async def validate_float(actor: dict = Depends(guard.get_actor)):
        return orca.validate("FLOATING_STABILITY", actor["identity_id"], {})

    return router

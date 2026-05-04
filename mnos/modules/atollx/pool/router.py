from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

class PoolSystem(BaseModel):
    pool_id: str
    project_id: str
    type: str # Chemical-free, Mirror-infinity
    is_reef_safe: bool

class PoolWaterQualityReading(BaseModel):
    reading_id: str
    pool_id: str
    ph: float
    chlorine_level: float # Should be 0 for chemical-free
    reef_safe_certified: bool

class PoolAutomationCommand(BaseModel):
    command_id: str
    pool_id: str
    action: str

class PoolEnergyReading(BaseModel):
    reading_id: str
    pool_id: str
    usage_kwh: float

class PoolDesignApproval(BaseModel):
    approval_id: str
    pool_id: str
    approver_id: str
    status: str

def create_pool_router(guard: ExecutionGuard, shadow, orca):
    router = APIRouter(prefix="/atollx/pool", tags=["ATOLLX_POOL"])

    @router.post("/system")
    async def create_system(pool: PoolSystem, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.pool.system",
            actor,
            lambda **kwargs: {"status": "POOL_LOGGED", "pool_id": pool.pool_id}
        )

    @router.post("/water-quality")
    async def log_water_quality(reading: PoolWaterQualityReading, actor: dict = Depends(get_actor_context)):
        # REQUIREMENT: Pool system must fail if reef-safe validation fails.
        orca_res = orca.validate("REEF_SAFE", actor["identity_id"], {"reef_safe_certified": reading.reef_safe_certified})
        if not orca_res["passed"]:
            raise HTTPException(status_code=400, detail=f"FAIL CLOSED: Reef-safe validation failed: {orca_res['failure_reasons']}")

        return guard.execute_sovereign_action(
            "atollx.pool.water_quality",
            actor,
            lambda **kwargs: {"status": "QUALITY_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/automation")
    async def log_automation(command: PoolAutomationCommand, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.pool.automation",
            actor,
            lambda **kwargs: {"status": "COMMAND_LOGGED", "command_id": command.command_id}
        )

    @router.post("/energy")
    async def log_energy(reading: PoolEnergyReading, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.pool.energy",
            actor,
            lambda **kwargs: {"status": "ENERGY_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/design-approval")
    async def approve_design(approval: PoolDesignApproval, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.pool.design_approve",
            actor,
            lambda **kwargs: {"status": "DESIGN_APPROVED", "approval_id": approval.approval_id}
        )

    @router.post("/validate")
    async def validate_pool(actor: dict = Depends(get_actor_context)):
        return orca.validate("REEF_SAFE", actor["identity_id"], {})

    return router

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from mnos.shared.execution_guard import ExecutionGuard

class WaterBatch(BaseModel):
    batch_id: str
    source_id: str
    volume_liters: float

class TreatmentUnit(BaseModel):
    unit_id: str
    type: str
    status: str

class WaterQualityReading(BaseModel):
    reading_id: str
    batch_id: str
    ph: float
    turbidity: float
    contamination_level: float

class OdorReading(BaseModel):
    reading_id: str
    batch_id: str
    odor_intensity: int

class SludgeRecord(BaseModel):
    record_id: str
    batch_id: str
    weight_kg: float

class ReclaimedWaterCredit(BaseModel):
    credit_id: str
    project_id: str
    amount_mvr: float

def create_water_router(guard: ExecutionGuard, shadow, orca):
    router = APIRouter(prefix="/atollx/water", tags=["ATOLLX_WATER"])

    @router.post("/batch")
    async def create_batch(batch: WaterBatch, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.water.batch",
            actor,
            lambda: {"status": "BATCH_LOGGED", "batch_id": batch.batch_id}
        )

    @router.post("/quality")
    async def log_quality(reading: WaterQualityReading, actor: dict = Depends(guard.get_actor)):
        # REQUIREMENT: Water batch must quarantine if Class A validation fails.
        orca_res = orca.validate("CLASS_A_WATER", actor["identity_id"], {"contamination_level": reading.contamination_level})

        status = "QUALITY_LOGGED"
        if not orca_res["passed"]:
            status = "BATCH_QUARANTINED"

        return guard.execute_sovereign_action(
            "atollx.water.quality",
            actor,
            lambda: {"status": status, "reading_id": reading.reading_id, "orca": orca_res},
            forced_status=status
        )

    @router.post("/odor")
    async def log_odor(reading: OdorReading, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.water.odor",
            actor,
            lambda: {"status": "ODOR_LOGGED", "reading_id": reading.reading_id}
        )

    @router.post("/sludge")
    async def log_sludge(record: SludgeRecord, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.water.sludge",
            actor,
            lambda: {"status": "SLUDGE_LOGGED", "record_id": record.record_id}
        )

    @router.post("/validate-class-a")
    async def validate_class_a(batch_id: str, actor: dict = Depends(guard.get_actor)):
        return orca.validate("CLASS_A_WATER", actor["identity_id"], {"batch_id": batch_id})

    @router.post("/fce-credit")
    async def issue_fce_credit(credit: ReclaimedWaterCredit, actor: dict = Depends(guard.get_actor)):
        return guard.execute_sovereign_action(
            "atollx.water.fce_credit",
            actor,
            lambda: {"status": "CREDIT_ISSUED", "credit_id": credit.credit_id}
        )

    return router

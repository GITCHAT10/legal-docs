from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from mnos.shared.execution_guard import ExecutionGuard
from mnos.shared.auth import get_actor_context

class CivilDesign(BaseModel):
    design_id: str
    project_id: str
    spec_url: str

class BIMModel(BaseModel):
    model_id: str
    project_id: str
    file_url: str

class MEPElement(BaseModel):
    element_id: str
    type: str # Mechanical, Electrical, Plumbing
    system_id: str

class EnergyModel(BaseModel):
    model_id: str
    project_id: str
    efficiency_rating: str

class ClashReport(BaseModel):
    report_id: str
    model_id: str
    clash_count: int

class PrefabPackage(BaseModel):
    package_id: str
    project_id: str
    components: List[str]

class DesignValidationResult(BaseModel):
    validation_id: str
    passed: bool
    reasons: List[str]

def create_design_router(guard: ExecutionGuard, shadow, orca):
    router = APIRouter(prefix="/atollx/design", tags=["ATOLLX_DESIGN"])

    @router.post("/civil")
    async def create_civil(design: CivilDesign, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.design.civil",
            actor,
            lambda: {"status": "CIVIL_LOGGED", "design_id": design.design_id}
        )

    @router.post("/bim")
    async def create_bim(model: BIMModel, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.design.bim",
            actor,
            lambda: {"status": "BIM_LOGGED", "model_id": model.model_id}
        )

    @router.post("/mep")
    async def create_mep(element: MEPElement, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.design.mep",
            actor,
            lambda: {"status": "MEP_LOGGED", "element_id": element.element_id}
        )

    @router.post("/energy")
    async def create_energy(model: EnergyModel, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.design.energy",
            actor,
            lambda: {"status": "ENERGY_LOGGED", "model_id": model.model_id}
        )

    @router.post("/clash-check")
    async def check_clash(report: ClashReport, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.design.clash",
            actor,
            lambda: {"status": "CLASH_CHECKED", "report_id": report.report_id}
        )

    @router.post("/prefab")
    async def create_prefab(pkg: PrefabPackage, actor: dict = Depends(get_actor_context)):
        return guard.execute_sovereign_action(
            "atollx.design.prefab",
            actor,
            lambda: {"status": "PREFAB_LOGGED", "package_id": pkg.package_id}
        )

    @router.post("/validate")
    async def validate_design(actor: dict = Depends(get_actor_context)):
        return orca.validate("ENGINEERING_DESIGN", actor["identity_id"], {})

    return router

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import List, Optional
from .aegis.auth import AegisAuth
from .shadow_vault.vault_api import ShadowVault
from .shadow_audit.ledger import ShadowLedger
from .ai.cognition import CognitiveBrain
from .ai.predictions import PredictionEngine
from .compliance.pdpa_redactor import PdpaRedactor
from .compliance.mira_export import MiraExportEngine

# Root Instances (normally in a dependency container)
audit_ledger = ShadowLedger()
aegis = AegisAuth("sovereign-secret")
vault = ShadowVault(audit_ledger)
brain = CognitiveBrain(audit_ledger)
ml_engine = PredictionEngine(audit_ledger)
redactor = PdpaRedactor()
mira_engine = MiraExportEngine(audit_ledger)

def create_aegis_router():
    router = APIRouter(prefix="/aegis", tags=["aegis"])

    @router.post("/login")
    async def login(username: str, password: str, device_id: str):
        try:
            token = aegis.login(username, password, device_id)
            return {"access_token": token}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    @router.get("/me")
    async def get_me(x_aegis_token: str = Header(...)):
        return aegis.jwt_manager.validate_token(x_aegis_token)

    @router.post("/register-device")
    async def register_device(identity_id: str, fingerprint: str):
        # In a real system, this might be gated by an initial setup token
        dev_id = aegis.device_registry.register_device(identity_id, fingerprint)
        return {"device_id": dev_id}

    return router

def create_vault_router():
    router = APIRouter(prefix="/vault", tags=["vault"])

    @router.post("/upload")
    async def upload(filename: str, request: Request, x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_write")
        data = await request.body()
        trace_id = f"TRC-UP-{uuid_hex()}"
        file_id = vault.upload_file(actor, filename, data, trace_id)
        return {"file_id": file_id}

    @router.get("/files")
    async def list_files(x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_read")
        return vault.list_files(actor)

    @router.get("/files/{file_id}/download")
    async def download(file_id: str, x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_read")
        trace_id = f"TRC-DL-{uuid_hex()}"
        data = vault.download_file(actor, file_id, trace_id)
        # In real life, return a StreamingResponse
        return {"data_b64": data.decode()}

    @router.post("/files/{file_id}/share")
    async def share(file_id: str, target_identity_id: str, x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_share")
        trace_id = f"TRC-SH-{uuid_hex()}"
        vault.share_file(actor, file_id, target_identity_id, trace_id)
        return {"status": "shared"}

    @router.delete("/files/{file_id}")
    async def delete(file_id: str, x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_delete")
        trace_id = f"TRC-DEL-{uuid_hex()}"
        vault.delete_file(actor, file_id, trace_id)
        return {"status": "deleted"}

    return router

def create_ai_router():
    router = APIRouter(prefix="/ai", tags=["ai"])

    @router.post("/solve")
    async def solve(problem_type: str, context: dict, x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_read") # Simple check
        trace_id = f"TRC-AI-{uuid_hex()}"
        return brain.solve_problem(actor, problem_type, context, trace_id)

    @router.post("/predict")
    async def predict(dataset: List[float], x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "vault_read")
        trace_id = f"TRC-ML-{uuid_hex()}"
        return ml_engine.predict_workload(actor, dataset, trace_id)

    return router

def create_compliance_router():
    router = APIRouter(prefix="/compliance", tags=["compliance"])

    @router.get("/mira-export")
    async def export_mira(start_date: str, end_date: str, x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "audit_read")
        return mira_engine.generate_mira_report(start_date, end_date)

    @router.get("/audit/events")
    async def get_audit_events(x_aegis_token: str = Header(...)):
        actor = aegis.validate_request(x_aegis_token, "audit_read")
        return [b["data"] for b in audit_ledger.ledger]

    return router

def uuid_hex():
    import uuid
    return uuid.uuid4().hex[:6].upper()

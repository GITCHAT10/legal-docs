from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.request import ClearanceRequest
from schemas.response import ClearanceResponse
from domain.services import CustomsOrchestrator
from domain.database import get_db
from api.auth import verify_customs_token

router = APIRouter(dependencies=[Depends(verify_customs_token)])

@router.post("/clearance-request", response_model=ClearanceResponse)
async def create_clearance_request(request: ClearanceRequest, db: Session = Depends(get_db)):
    orchestrator = CustomsOrchestrator(db)
    return await orchestrator.process_clearance_request(request)

@router.get("/clearance-request/{request_id}")
async def get_clearance_request(request_id: str, db: Session = Depends(get_db)):
    orchestrator = CustomsOrchestrator(db)
    req = orchestrator.get_request_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Clearance request not found")
    return req

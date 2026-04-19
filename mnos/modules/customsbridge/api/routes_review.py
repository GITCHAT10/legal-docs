from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.request import OverrideRequest
from domain.services import CustomsOrchestrator
from domain.database import get_db
from api.auth import verify_customs_token

router = APIRouter(dependencies=[Depends(verify_customs_token)])

@router.post("/review/override-request")
async def override_request(request: OverrideRequest, db: Session = Depends(get_db)):
    orchestrator = CustomsOrchestrator(db)
    return await orchestrator.process_override(request)

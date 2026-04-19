from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from mnos.modules.customsbridge.schemas.request import OverrideRequest
from mnos.modules.customsbridge.domain.services import CustomsOrchestrator
from mnos.modules.customsbridge.domain.database import get_db
from mnos.modules.customsbridge.api.auth import verify_customs_token

router = APIRouter(dependencies=[Depends(verify_customs_token)])

@router.post("/review/override-request")
async def override_request(request: OverrideRequest, db: Session = Depends(get_db)):
    orchestrator = CustomsOrchestrator(db)
    return await orchestrator.process_override(request)

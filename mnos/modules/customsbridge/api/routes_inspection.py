from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from mnos.modules.customsbridge.schemas.request import InspectionResult
from mnos.modules.customsbridge.domain.services import CustomsOrchestrator
from mnos.modules.customsbridge.domain.database import get_db
from mnos.modules.customsbridge.api.auth import verify_customs_token

router = APIRouter(dependencies=[Depends(verify_customs_token)])

@router.post("/inspection-result")
async def record_inspection_result(result: InspectionResult, db: Session = Depends(get_db)):
    orchestrator = CustomsOrchestrator(db)
    return await orchestrator.process_inspection(result)

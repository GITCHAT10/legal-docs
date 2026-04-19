from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.request import InspectionResult
from domain.services import CustomsOrchestrator
from domain.database import get_db
from api.auth import verify_customs_token

router = APIRouter(dependencies=[Depends(verify_customs_token)])

@router.post("/inspection-result")
async def record_inspection_result(result: InspectionResult, db: Session = Depends(get_db)):
    orchestrator = CustomsOrchestrator(db)
    return await orchestrator.process_inspection(result)

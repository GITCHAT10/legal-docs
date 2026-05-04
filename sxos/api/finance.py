from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from sxos.finance.service import process_settlement

router = APIRouter(prefix="/sxos/finance")

@router.post("/settle")
def settle(transaction_id: str, amount: float, tenant_id: str, db: Session = Depends(get_db)):
    return process_settlement(db, tenant_id, transaction_id, amount)

@router.get("/yield")
def get_yield(transaction_id: str):
    return {"transaction_id": transaction_id, "yield": 0.85}

@router.post("/distribute")
def distribute(transaction_id: str):
    return {"status": "DISTRIBUTED", "transaction_id": transaction_id}

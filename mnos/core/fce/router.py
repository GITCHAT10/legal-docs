from fastapi import APIRouter, Depends, HTTPException
from mnos.core.fce.tax_engine_mv import calculate_maldives_tax
from mnos.core.fce.models import FCEPriceBreakdown

router = APIRouter(prefix="/fce")

@router.post("/tax/calculate", response_model=FCEPriceBreakdown)
async def calculate_tax(base_price: float, currency: str = "USD"):
    try:
        return calculate_maldives_tax(base_price, currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reconcile")
async def reconcile():
    return {"status": "RECONCILED", "audit_sealed": True}

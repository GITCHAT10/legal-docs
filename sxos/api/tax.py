from fastapi import APIRouter
from sxos.tax.service import classify_and_calculate_tax
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/sxos/tax")

class TaxItem(BaseModel):
    name: str
    price: float
    category: str

@router.post("/calculate")
def calculate(items: List[TaxItem]):
    return classify_and_calculate_tax([item.model_dump() for item in items])

@router.post("/classify")
def classify(items: List[TaxItem]):
    return {"classified_items": [item.name for item in items]}

@router.get("/export_mira")
def export_mira():
    return {"mira_xml": "<report>...</report>", "status": "READY"}

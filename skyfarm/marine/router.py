from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import log_fish_intake, grade_fish
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/marine")

class CatchCreate(BaseModel):
    vessel_id: str
    species: str
    weight: float
    location: str
    tenant_id: str = "sf_maldives_001"
    temperature_c: float = 2.0

class GradeCreate(BaseModel):
    catch_id: str
    grade: str
    tenant_id: str = "sf_maldives_001"

@router.post("/catch")
def create_catch(catch: CatchCreate, db: Session = Depends(get_db)):
    return log_fish_intake(db, **catch.model_dump())

@router.post("/grade")
def create_grade(grade: GradeCreate, db: Session = Depends(get_db)):
    return grade_fish(db, **grade.model_dump())

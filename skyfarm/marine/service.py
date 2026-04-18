from sqlalchemy.orm import Session
from .models import CatchLogModel
from skyfarm.integration.outbox_service import queue_event
from fastapi import HTTPException
import uuid

def log_fish_intake(db: Session, vessel_id: str, species: str, weight: float, location: str, tenant_id: str, temperature_c: float = 2.0):
    # Validation Rules (EPIC 3)
    if temperature_c > 4.0:
        raise HTTPException(status_code=400, detail=f"Temperature breach: {temperature_c}C exceeds 4.0C limit")

    if weight <= 0:
        raise HTTPException(status_code=400, detail="Weight must be positive")

    catch = CatchLogModel(
        id=f"fish_{uuid.uuid4().hex[:8]}",
        vessel_id=vessel_id,
        species=species,
        weight=weight,
        location=location,
        status="fish.intake.recorded"
    )
    db.add(catch)

    # Queue event for MNOS
    queue_event(db, tenant_id, "fish.intake.recorded", {
        "species": species,
        "gross_weight_kg": weight,
        "vessel_id": vessel_id,
        "landing_location": location,
        "temperature_c": temperature_c
    })

    db.commit()
    db.refresh(catch)
    return catch

def grade_fish(db: Session, catch_id: str, grade: str, tenant_id: str):
    catch = db.query(CatchLogModel).filter(CatchLogModel.id == catch_id).first()
    if not catch:
        raise HTTPException(status_code=404, detail="Catch not found")

    # Valid grades: A+, A, B, Rejected
    valid_grades = ["A+", "A", "B", "Rejected"]
    if grade not in valid_grades:
        raise HTTPException(status_code=400, detail=f"Invalid grade: {grade}")

    catch.status = f"fish.graded.{grade.lower()}"

    queue_event(db, tenant_id, "fish.graded", {
        "catch_id": catch_id,
        "grade": grade
    })

    db.commit()
    db.refresh(catch)
    return catch

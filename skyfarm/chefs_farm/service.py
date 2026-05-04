"""
CHEFS_FARM_OPERATING_MODEL_V1
"""
from sqlalchemy.orm import Session
from .models import ChefsFarmSiteModel, ChefHarvestRequestModel, ChefAcceptanceRecordModel, ChefFeedbackRecordModel
from skyfarm.integration.outbox_service import queue_event
from fastapi import HTTPException
import uuid
import hashlib

def create_harvest_request(db: Session, chefs_farm_id: str, chef_id: str, crop_batch_id: str, container_id: str):
    request = ChefHarvestRequestModel(
        chefs_farm_id=chefs_farm_id,
        chef_id=chef_id,
        crop_batch_id=crop_batch_id,
        container_id=container_id
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Notify SKYFARM Operator via event
    queue_event(db, "sf_maldives_001", "cf.harvest.requested", {
        "request_id": request.id,
        "chefs_farm_id": chefs_farm_id,
        "chef_id": chef_id,
        "crop_batch_id": crop_batch_id
    })

    return request

def record_chef_acceptance(db: Session, chefs_farm_id: str, chef_id: str, harvest_request_id: str, accepted_kg: float, rejected_kg: float):
    if accepted_kg <= 0 and rejected_kg <= 0:
         raise HTTPException(status_code=400, detail="Must have non-zero weight for acceptance/rejection")

    confirmation_id = f"conf_{uuid.uuid4().hex[:12]}"

    # Generate SHADOW proof hash
    proof_data = f"{chefs_farm_id}|{chef_id}|{accepted_kg}|{confirmation_id}"
    shadow_hash = hashlib.sha256(proof_data.encode()).hexdigest()

    record = ChefAcceptanceRecordModel(
        chefs_farm_id=chefs_farm_id,
        chef_id=chef_id,
        harvest_request_id=harvest_request_id,
        accepted_kg=accepted_kg,
        rejected_kg=rejected_kg,
        chef_confirmation_id=confirmation_id,
        shadow_proof_hash=shadow_hash
    )
    db.add(record)

    # Update harvest request status
    hr = db.query(ChefHarvestRequestModel).filter(ChefHarvestRequestModel.id == harvest_request_id).first()
    if hr:
        hr.harvest_request_status = "COMPLETED"

    # Queue event for FCE Settlement & SHADOW
    queue_event(db, "sf_maldives_001", "cf.harvest.confirmed", {
        "acceptance_id": record.id,
        "chefs_farm_id": chefs_farm_id,
        "accepted_kg": accepted_kg,
        "rejected_kg": rejected_kg,
        "confirmation_id": confirmation_id,
        "shadow_hash": shadow_hash,
        "guest_story_qr_url": f"https://skyfarm.live/story/{record.id}"
    })

    db.commit()
    db.refresh(record)
    return record

def submit_chef_feedback(db: Session, chefs_farm_id: str, chef_id: str, crop_batch_id: str, feedback: str, prefs: dict = None):
    record = ChefFeedbackRecordModel(
        chefs_farm_id=chefs_farm_id,
        chef_id=chef_id,
        crop_batch_id=crop_batch_id,
        feedback_text=feedback,
        metadata_json=prefs
    )
    db.add(record)

    # Queue for SKYBRAIN / Operator recommendation
    queue_event(db, "sf_maldives_001", "cf.chef.feedback", {
        "chefs_farm_id": chefs_farm_id,
        "chef_id": chef_id,
        "feedback": feedback,
        "preferences": prefs
    })

    db.commit()
    return record

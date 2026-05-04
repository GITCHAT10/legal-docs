"""
CHEFS_FARM_OPERATING_MODEL_V1
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from skyfarm.database import get_db
from .service import create_harvest_request, record_chef_acceptance, submit_chef_feedback
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v1/chefs-farm")

class HarvestRequest(BaseModel):
    chefs_farm_id: str
    chef_id: str
    crop_batch_id: str
    container_id: str

class AcceptanceRecord(BaseModel):
    chefs_farm_id: str
    chef_id: str
    harvest_request_id: str
    accepted_kg: float
    rejected_kg: float = 0.0

class FeedbackRecord(BaseModel):
    chefs_farm_id: str
    chef_id: str
    crop_batch_id: str
    feedback: str
    preferences: Optional[Dict[str, Any]] = None

@router.post("/harvest/request")
def request_harvest(req: HarvestRequest, db: Session = Depends(get_db)):
    return create_harvest_request(db, **req.model_dump())

@router.post("/harvest/accept")
def accept_harvest(acc: AcceptanceRecord, db: Session = Depends(get_db)):
    return record_chef_acceptance(db, **acc.model_dump())

@router.post("/feedback")
def give_feedback(fdb: FeedbackRecord, db: Session = Depends(get_db)):
    return submit_chef_feedback(db, **fdb.model_dump())

@router.get("/live-link/{chefs_farm_id}")
def get_live_link(chefs_farm_id: str, db: Session = Depends(get_db)):
    # Mocking live link status and CCTV stream
    return {
        "chefs_farm_id": chefs_farm_id,
        "live_link_status": "ONLINE",
        "cctv_stream_url": f"wss://cctv.skyfarm.live/{chefs_farm_id}",
        "operator_audio_url": f"wss://audio.skyfarm.live/{chefs_farm_id}",
        "can_control_machines": False
    }

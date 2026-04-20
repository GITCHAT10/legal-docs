from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import uuid

from mnos.core.api import deps
from mnos.modules.inn.staging import models, parsers, approval_service

router = APIRouter()

@router.post("/upload", response_model=Any)
async def upload_rooming_list(
    wholesaler_id: str,
    mapping_profile_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
):
    trace_id = f"UPLOAD-{uuid.uuid4().hex[:8]}"
    content = await file.read()

    # 1. Record upload
    upload = models.RoomingListUpload(
        filename=file.filename,
        wholesaler_id=wholesaler_id,
        trace_id=trace_id,
        status=models.StagingStatus.PENDING_PARSE
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    # 2. Get mapping
    profile = db.query(models.MappingProfile).filter(models.MappingProfile.id == mapping_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Mapping profile not found")

    # 3. Parse
    try:
        parsed_results = parsers.parse_xlsx(content, profile.mapping_config)
        upload.raw_data = parsed_results
        upload.status = models.StagingStatus.STAGED

        for entry in parsed_results:
            staging = models.StagingReservation(
                upload_id=upload.id,
                guest_name=entry.get("guest_name"),
                check_in=entry.get("check_in"),
                check_out=entry.get("check_out"),
                room_type=entry.get("room_type"),
                trace_id=f"STG-{uuid.uuid4().hex[:8]}",
                status=models.StagingStatus.STAGED
            )
            db.add(staging)

        db.commit()
    except Exception as e:
        upload.status = models.StagingStatus.FAILED
        db.commit()
        raise HTTPException(status_code=400, detail=f"Parsing failed: {str(e)}")

    return {"upload_id": upload.id, "status": upload.status, "trace_id": trace_id}

@router.post("/{staging_id}/promote")
def promote_reservation(
    staging_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
):
    result = approval_service.promote_staging_to_live(db, staging_id)
    if not result:
        raise HTTPException(status_code=404, detail="Staging record not found or already promoted")
    return {"status": "promoted", "staging_id": staging_id}

@router.get("/status", response_model=Any)
def get_intake_status(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
):
    from sqlalchemy import func
    counts = db.query(models.StagingReservation.status, func.count(models.StagingReservation.id)).group_by(models.StagingReservation.status).all()
    upload_count = db.query(func.count(models.RoomingListUpload.id)).scalar()

    return {
        "upload_total": upload_count,
        "staging_counts": {status.value: count for status, count in counts}
    }

@router.post("/profiles", response_model=Any)
def create_mapping_profile(
    name: str,
    mapping_config: Any,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
):
    profile = models.MappingProfile(name=name, mapping_config=mapping_config)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

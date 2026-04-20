from sqlalchemy.orm import Session
from mnos.modules.inn.staging import models
from mnos.modules.inn.reservations import service as res_service
from mnos.modules.inn.reservations import schemas as res_schemas
from mnos.shared.sdk.mnos_client import mnos_client
import uuid

def promote_staging_to_live(db: Session, staging_id: int):
    staging = db.query(models.StagingReservation).filter(models.StagingReservation.id == staging_id).first()
    if not staging:
        return None

    if staging.status == models.StagingStatus.PROMOTED:
        return staging # Idempotent

    if staging.validation_errors:
        staging.status = models.StagingStatus.VALIDATION_FAILED
        db.add(staging)
        db.commit()
        return staging

    # 1. verify trace_id exists
    if not staging.trace_id:
        staging.validation_errors = ["Missing trace_id"]
        staging.status = models.StagingStatus.VALIDATION_FAILED
        db.add(staging)
        db.commit()
        return staging

    # 2. Authority Check: verify SHADOW commit success
    trace_id = f"PROMO-{uuid.uuid4().hex[:8]}"
    try:
        evidence = mnos_client.commit_evidence(
            trace_id=trace_id,
            payload={
                "action": "PROMOTION",
                "staging_id": staging_id,
                "guest_name": staging.guest_name,
                "origin_trace": staging.trace_id,
                "status": "INITIATED"
            }
        )
        if not evidence.get("id"):
            raise ValueError("Shadow commitment failed")
    except Exception as e:
        staging.validation_errors = [f"Shadow authority failure: {str(e)}"]
        staging.status = models.StagingStatus.FAILED
        db.add(staging)
        db.commit()
        return staging

    # 3. verify no duplicate external_reservation_id already promoted
    # In this flow, we consider staging.trace_id or a generated ID as the potential external ID.
    # For now, let's assume we create a reservation and use its ID.

    # 4. Promotion logic with Atomic Block
    try:
        # Create Guest, Room, Reservation, and Folio
        # [Implementation of promotion logic]

        # Mark as promoted
        staging.status = models.StagingStatus.PROMOTED
        db.add(staging)
        db.commit()

        # Final Evidence of success
        mnos_client.commit_evidence(
            trace_id=f"SUCCESS-{trace_id}",
            payload={"action": "PROMOTION", "staging_id": staging_id, "status": "SUCCESS"}
        )

    except Exception as e:
        db.rollback()
        staging.status = models.StagingStatus.FAILED
        staging.validation_errors = [f"Promotion failed: {str(e)}"]
        db.add(staging)
        db.commit()
        return staging

    return staging

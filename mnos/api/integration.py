from fastapi import APIRouter, Header, Depends, HTTPException, Request
import uuid
import hashlib
import json
from datetime import datetime, timezone
from mnos.schemas.event import ProductionEventSchema
from mnos.services.policy_service import policy_evaluation_service
from mnos.services.shadow_service import shadow_write_service
from mnos.services.risk_service import risk_scoring_service
from mnos.core.logging import logger
from mnos.core.config import config
from mnos.security import verify_signature_v2
from mnos.database import get_mnos_db, EventLogModel, IdempotencyRegistryModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/integration/v1")

@router.post("/events/production")
async def ingest_production_event(
    request: Request,
    x_request_id: str = Header(...),
    x_idempotency_key: str = Header(...),
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    db: Session = Depends(get_mnos_db)
):
    body_bytes = await request.body()

    # 1. Signature Verification
    if config["mode"] == "enforced":
        if not verify_signature_v2(
            signature=x_signature,
            method="POST",
            path="/integration/v1/events/production",
            timestamp=x_timestamp,
            request_id=x_request_id,
            body_bytes=body_bytes,
            secret=config["MNOS_INTEGRATION_SECRET"]
        ):
            raise HTTPException(status_code=401, detail="INVALID_SIGNATURE")

    # 2. Schema Validation (Manually since we read body_bytes first)
    try:
        body_json = json.loads(body_bytes)
        event = ProductionEventSchema(**body_json)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 3. Idempotency Check
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    idem_entry = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_idempotency_key).first()
    if idem_entry:
        if idem_entry.body_hash == body_hash:
            return idem_entry.response_json
        else:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_KEY_CONFLICT")

    # 4. Replay Protection
    existing_req = db.query(IdempotencyRegistryModel).filter(IdempotencyRegistryModel.key == x_request_id).first()
    if existing_req:
        raise HTTPException(status_code=401, detail="REPLAYED_REQUEST_ID")

    # 5. Processing
    event_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    event_dict = event.model_dump()
    event_dict.update({"event_id": event_id, "trace_id": trace_id, "timestamp": timestamp_utc})

    # Service Execution
    policy_res = policy_evaluation_service(event_dict)

    if policy_res["decision"] == "DENY":
         raise HTTPException(status_code=403, detail="POLICY_REJECTION")

    shadow_id = shadow_write_service(event_dict, db)
    risk_res = risk_scoring_service(event_dict)

    logger.info(
        "Production event processed",
        trace_id=trace_id,
        event_id=event_id,
        decision=policy_res["decision"],
        latency=policy_res["latency_ms"],
        shadow_status="written"
    )

    response = {
        "status": "accepted",
        "event_id": event_id,
        "trace_id": trace_id,
        "decision": policy_res["decision"],
        "risk_score": risk_res["risk_score"]
    }

    # 6. Persistence
    new_event = EventLogModel(
        id=event_id,
        payload=event_dict,
        status="ingested"
    )
    db.add(new_event)

    new_idem = IdempotencyRegistryModel(
        key=x_idempotency_key,
        body_hash=body_hash,
        response_json=response
    )
    db.add(new_idem)

    req_tracker = IdempotencyRegistryModel(
        key=x_request_id,
        body_hash="REQ_ID",
        response_json={}
    )
    db.add(req_tracker)

    db.commit()
    return response
